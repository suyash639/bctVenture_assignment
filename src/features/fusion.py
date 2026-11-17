"""
Normalise feature blocks and fuse them into one matrix for clustering.

Blocks (each optional, controlled by FusionConfig.blocks weights; weight 0 = unused):
  clip     CLIP image embedding (512-d), centred; optional PCA (fixed seed). Not z-scored per
           dimension, so the embedding's cosine geometry is kept.
  numeric  log(aspect_ratio), brightness, contrast, log1p(sharpness), colourfulness,
           text_density, log1p(ocr_n_text_regions); scaled with standard or robust scaling
  colour   colour_distribution (white, black, grey + 12 hue bins = 15 shares) + the top dominant
           colour in CIE Lab (L*, a*, b*), the colour space where Euclidean distance ≈ perceived
           difference, + that colour's proportion; scaled
  layout   one-hot layout_category, orientation, text_position (unscaled 0/1)
  text     hook for future text embeddings; not implemented (weight must stay 0)

Block balancing: after scaling, each block is divided by sqrt(mean squared row norm) so that
on average every block contributes a squared norm of 1 (for a z-scored block this equals
dividing by sqrt(n_dims)); then it is multiplied by its weight. A block's influence therefore
does not grow with its dimensionality.

Missing values: impute="median" fills the block-column median (and records an issue);
impute="drop" excludes the record with a reason. A record without a usable CLIP embedding is
always excluded when the clip block is active, because semantics can't be imputed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.features.bundle import FeatureBundle

LAYOUTS = ["product_focused", "lifestyle", "testimonial", "offer_heavy", "educational", "unknown"]
ORIENTATIONS = ["portrait", "square", "landscape"]
TEXT_POSITIONS = ["top", "middle", "bottom", "none"]
COLOUR_SHARES = ["white", "black", "grey", "red", "orange", "yellow", "yellow_green", "green",
                 "green_cyan", "cyan", "azure", "blue", "violet", "magenta", "rose"]
NUMERIC_NAMES = ["log_aspect_ratio", "brightness", "contrast", "log1p_sharpness", "colourfulness",
                 "text_density", "log1p_ocr_regions"]


@dataclass
class FusionConfig:
    blocks: Dict[str, float] = field(default_factory=lambda: {"clip": 1.0, "numeric": 0.0, "colour": 0.0,
                                                              "layout": 0.0, "text": 0.0})
    clip_pca_components: Optional[int] = None
    scaler: str = "standard"           # "standard" | "robust"
    impute: str = "median"             # "median" | "drop"
    seed: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "FusionConfig":
        cfg = cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
        cfg.validate()
        return cfg

    def validate(self) -> None:
        unknown = set(self.blocks) - {"clip", "numeric", "colour", "layout", "text"}
        if unknown:
            raise ValueError(f"unknown blocks: {sorted(unknown)}")
        if any(w < 0 for w in self.blocks.values()):
            raise ValueError("block weights must be >= 0")
        if not any(w > 0 for w in self.blocks.values()):
            raise ValueError("at least one block needs a positive weight")
        if self.blocks.get("text", 0) > 0:
            raise NotImplementedError("text block is a hook only; keep its weight at 0")
        if self.scaler not in ("standard", "robust"):
            raise ValueError("scaler must be 'standard' or 'robust'")
        if self.impute not in ("median", "drop"):
            raise ValueError("impute must be 'median' or 'drop'")


@dataclass
class FeatureMatrix:
    X: np.ndarray
    ad_ids: List[str]
    feature_names: List[str]
    blocks: Dict[str, slice]
    excluded: List[tuple]
    config: dict
    issues: List[dict] = field(default_factory=list)

    def save(self, out_dir) -> Path:
        d = Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        np.save(d / "matrix.npy", self.X.astype(np.float64))
        (d / "matrix_index.json").write_text(json.dumps({
            "ad_ids": self.ad_ids, "feature_names": self.feature_names,
            "blocks": {k: [s.start, s.stop] for k, s in self.blocks.items()},
            "excluded": [list(e) for e in self.excluded], "config": self.config,
            "issues": self.issues, "shape": list(self.X.shape)}, indent=1))
        return d

    @classmethod
    def load(cls, out_dir) -> "FeatureMatrix":
        d = Path(out_dir)
        idx = json.loads((d / "matrix_index.json").read_text())
        X = np.load(d / "matrix.npy")
        if list(X.shape) != idx["shape"] or len(idx["ad_ids"]) != X.shape[0]:
            raise ValueError("matrix.npy and matrix_index.json disagree")
        return cls(X=X, ad_ids=idx["ad_ids"], feature_names=idx["feature_names"],
                   blocks={k: slice(a, b) for k, (a, b) in idx["blocks"].items()},
                   excluded=[tuple(e) for e in idx["excluded"]], config=idx["config"],
                   issues=idx.get("issues", []))


# ----------------------------------------------------------------------------- raw blocks

def _num(v):
    return float(v) if isinstance(v, (int, float)) and np.isfinite(v) else np.nan


def _numeric_row(r: dict) -> List[float]:
    ar = _num(r.get("aspect_ratio"))
    sh = _num(r.get("sharpness"))
    reg = _num(r.get("ocr_n_text_regions"))
    return [np.log(ar) if ar > 0 else np.nan, _num(r.get("brightness")), _num(r.get("contrast")),
            np.log1p(sh) if sh >= 0 else np.nan, _num(r.get("colourfulness")),
            _num(r.get("text_density")), np.log1p(reg) if reg >= 0 else np.nan]


def srgb_to_lab(rgb) -> List[float]:
    """sRGB 0..255 -> CIE L*a*b* (D65)."""
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = M @ c / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return [116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])]


def _colour_row(r: dict) -> List[float]:
    dist = r.get("colour_distribution") or {}
    shares = [_num(dist.get(k)) if dist else np.nan for k in COLOUR_SHARES]
    dom = r.get("dominant_colours") or []
    if dom and dom[0].get("rgb") is not None:
        lab = srgb_to_lab(dom[0]["rgb"])
        prop = _num(dom[0].get("proportion"))
    else:
        lab, prop = [np.nan] * 3, np.nan
    return shares + lab + [prop]


def _onehot(value, vocab) -> List[float]:
    return [1.0 if value == v else 0.0 for v in vocab]


def _layout_row(r: dict) -> List[float]:
    return (_onehot(r.get("layout_category"), LAYOUTS) + _onehot(r.get("orientation"), ORIENTATIONS)
            + _onehot(r.get("text_position"), TEXT_POSITIONS))


def _scale(A: np.ndarray, how: str) -> np.ndarray:
    if how == "robust":
        med = np.median(A, axis=0)
        iqr = np.percentile(A, 75, axis=0) - np.percentile(A, 25, axis=0)
        return (A - med) / np.where(iqr > 0, iqr, 1.0)
    mu, sd = A.mean(axis=0), A.std(axis=0)
    return (A - mu) / np.where(sd > 0, sd, 1.0)


def _balance(A: np.ndarray) -> np.ndarray:
    ms = float(np.mean(np.sum(A ** 2, axis=1))) if A.size else 0.0
    return A / np.sqrt(ms) if ms > 0 else A


# ----------------------------------------------------------------------------- build

def build_feature_matrix(bundle: FeatureBundle, config: Optional[FusionConfig] = None) -> FeatureMatrix:
    cfg = config or FusionConfig()
    cfg.validate()
    w = {k: float(cfg.blocks.get(k, 0.0)) for k in ("clip", "numeric", "colour", "layout")}
    excluded = list(bundle.excluded)
    issues: List[dict] = []

    keep = []
    for i, aid in enumerate(bundle.ad_ids):
        if w["clip"] > 0 and not np.all(np.isfinite(bundle.embeddings[i])):
            excluded.append((aid, "no usable CLIP embedding (clip block active)"))
            continue
        keep.append(i)

    raw = {}
    if w["numeric"] > 0:
        raw["numeric"] = (NUMERIC_NAMES, [_numeric_row(bundle.records[bundle.ad_ids[i]]) for i in keep])
    if w["colour"] > 0:
        names = [f"share_{c}" for c in COLOUR_SHARES] + ["dom_L", "dom_a", "dom_b", "dom_proportion"]
        raw["colour"] = (names, [_colour_row(bundle.records[bundle.ad_ids[i]]) for i in keep])

    # missing values in scaled blocks
    if raw:
        drop: Dict[int, List[str]] = {}
        for blk, (names, rows) in raw.items():
            A = np.array(rows, dtype=np.float64)
            for r_i, c_i in zip(*np.where(~np.isfinite(A))):
                aid = bundle.ad_ids[keep[r_i]]
                if cfg.impute == "drop":
                    drop.setdefault(int(r_i), []).append(f"{blk}.{names[c_i]}")
                else:
                    issues.append({"ad_id": aid, "field": f"{blk}.{names[c_i]}", "problem": "imputed with median"})
        for r_i, fields in sorted(drop.items()):  # one exclusion entry per ad
            excluded.append((bundle.ad_ids[keep[r_i]], f"missing {', '.join(fields)} (impute=drop)"))
        if drop:
            keep = [k for j, k in enumerate(keep) if j not in drop]
            raw = {b: (n, [r for j, r in enumerate(rows) if j not in drop]) for b, (n, rows) in raw.items()}

    parts, names_all, blocks, col = [], [], {}, 0

    def add(name, A, fnames):
        nonlocal col
        A = _balance(A) * w[name]
        parts.append(A)
        names_all.extend(fnames)
        blocks[name] = slice(col, col + A.shape[1])
        col += A.shape[1]

    n = len(keep)
    if w["clip"] > 0 and n:
        E = bundle.embeddings[keep].astype(np.float64)
        E = E - E.mean(axis=0)
        if cfg.clip_pca_components:
            from sklearn.decomposition import PCA
            k = min(cfg.clip_pca_components, n, E.shape[1])
            E = PCA(n_components=k, random_state=cfg.seed, svd_solver="full").fit_transform(E)
            add("clip", E, [f"clip_pc{j}" for j in range(E.shape[1])])
        else:
            add("clip", E, [f"clip_{j}" for j in range(E.shape[1])])
    for blk in ("numeric", "colour"):
        if blk in raw and n:
            fnames, rows = raw[blk]
            A = np.array(rows, dtype=np.float64)
            if np.isnan(A).any():
                all_nan = np.isnan(A).all(axis=0)
                for c in np.where(all_nan)[0]:  # e.g. OCR disabled: no median exists
                    issues.append({"ad_id": "*", "field": f"{blk}.{fnames[c]}",
                                   "problem": "missing for every record; constant 0 (carries no information)"})
                med = np.zeros(A.shape[1])
                if (~all_nan).any():
                    med[~all_nan] = np.nanmedian(A[:, ~all_nan], axis=0)
                A = np.where(np.isfinite(A), A, med)
            add(blk, _scale(A, cfg.scaler), fnames)
    if w["layout"] > 0 and n:
        A = np.array([_layout_row(bundle.records[bundle.ad_ids[i]]) for i in keep], dtype=np.float64)
        fn = ([f"layout_{x}" for x in LAYOUTS] + [f"orient_{x}" for x in ORIENTATIONS]
              + [f"textpos_{x}" for x in TEXT_POSITIONS])
        add("layout", A, fn)

    X = np.hstack(parts) if parts else np.zeros((n, 0))
    return FeatureMatrix(X=X, ad_ids=[bundle.ad_ids[i] for i in keep], feature_names=names_all,
                         blocks=blocks, excluded=excluded, config=cfg.to_dict(), issues=issues)
