"""
Image loading and normalisation for feature extraction.

Every extractor receives the same `PreparedImage`, so colour-mode handling is decided
in one place:
  * EXIF orientation is applied.
  * Palette / RGBA / LA images are alpha-composited onto white (ad creatives are shown
    on white feeds, and compositing avoids transparent pixels turning black).
  * Grayscale, CMYK, 16-bit etc. are converted to 8-bit RGB.
Original files are only ever opened read-only.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
PathLike = Union[str, Path]


class ImageLoadError(Exception):
    """Raised when a file is missing, unsupported, truncated or otherwise unreadable."""


class DuplicateAdIdError(ValueError):
    """Raised when one ad_id appears more than once in a selection (one ad -> one record)."""


# Upper bound on decoded pixels; above it an image is rejected with ImageLoadError instead of
# being decoded (Pillow's own decompression-bomb limit, ~89 MP, unless changed by the caller).
def max_pixels() -> int:
    return Image.MAX_IMAGE_PIXELS or 2 ** 31


@dataclass
class PreparedImage:
    path: Path
    rgb: Image.Image                 # full-resolution, 8-bit RGB, EXIF-corrected
    source_mode: str                 # PIL mode of the file on disk (e.g. "RGBA", "L")
    source_format: Optional[str]     # "PNG", "JPEG", ...

    @property
    def size(self):
        return self.rgb.size

    def analysis_copy(self, max_side: int) -> Image.Image:
        """Downscaled copy (aspect ratio preserved, never upscaled) for pixel statistics."""
        return resize_max_side(self.rgb, max_side)


@dataclass
class ImageRecord:
    """One row to extract features for: an ad ID, its brand and its image file."""
    ad_id: str
    brand: Optional[str]
    image_path: Path
    extra: dict = field(default_factory=dict)


def to_rgb(img: Image.Image, background=(255, 255, 255)) -> Image.Image:
    """Convert any PIL mode to 8-bit RGB, compositing transparency onto `background`."""
    if img.mode == "P":
        img = img.convert("RGBA" if "transparency" in img.info else "RGB")
    if img.mode in ("RGBA", "LA", "PA"):
        img = img.convert("RGBA")
        canvas = Image.new("RGBA", img.size, background + (255,))
        return Image.alpha_composite(canvas, img).convert("RGB")
    if img.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        # 16/32-bit integer or float grayscale: min-max rescale to 0..255 before converting.
        import numpy as np
        a = np.asarray(img, dtype=np.float64)
        lo, hi = float(a.min()), float(a.max())
        a = (a - lo) / (hi - lo) * 255 if hi > lo else a * 0
        return Image.fromarray(a.astype("uint8"), "L").convert("RGB")
    return img.convert("RGB") if img.mode != "RGB" else img


def load_image(path: PathLike) -> PreparedImage:
    """Open, integrity-check and normalise an image. Raises ImageLoadError on any failure."""
    p = Path(path)
    if not p.is_file():
        raise ImageLoadError(f"file not found: {p}")
    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ImageLoadError(f"unsupported extension '{p.suffix}': {p.name}")
    if p.stat().st_size == 0:
        raise ImageLoadError(f"empty file: {p.name}")
    try:
        with Image.open(p) as probe:      # structural check (headers/chunks)
            if probe.width * probe.height > max_pixels():
                raise ImageLoadError(f"{p.name} is {probe.width}x{probe.height}, above the "
                                     f"{max_pixels():,}-pixel safety limit")
            probe.verify()
        with Image.open(p) as im:         # verify() invalidates the handle; reopen to decode
            fmt, mode = im.format, im.mode
            im = ImageOps.exif_transpose(im)
            im.load()                     # forces full decode -> catches truncated data
            rgb = to_rgb(im)
    except Image.DecompressionBombError as e:
        raise ImageLoadError(f"{p.name} exceeds the pixel safety limit: {e}") from e
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as e:
        raise ImageLoadError(f"unreadable image {p.name}: {e}") from e
    if rgb.width < 1 or rgb.height < 1:
        raise ImageLoadError(f"zero-sized image: {p.name}")
    return PreparedImage(path=p, rgb=rgb, source_mode=mode, source_format=fmt)


def resize_max_side(img: Image.Image, max_side: int) -> Image.Image:
    """Shrink so the longest side is <= max_side, preserving aspect ratio."""
    w, h = img.size
    scale = max_side / max(w, h)
    if scale >= 1:
        return img.copy()
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def resize_short_side(img: Image.Image, short_side: int, max_long_side: Optional[int] = None) -> Image.Image:
    """
    Resize (up or down) so the shorter side equals short_side, preserving aspect ratio.
    If max_long_side is given, the scale is reduced so the longer side never exceeds it
    (prevents a 4x4000 banner from being upscaled to 600x600000).
    """
    w, h = img.size
    scale = short_side / min(w, h)
    if max_long_side and max(w, h) * scale > max_long_side:
        scale = max_long_side / max(w, h)
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def pad_to_square(img: Image.Image, fill=(255, 255, 255)) -> Image.Image:
    """Letterbox to a square canvas so a centre-crop model input keeps the whole creative."""
    w, h = img.size
    if w == h:
        return img
    side = max(w, h)
    canvas = Image.new("RGB", (side, side), fill)
    canvas.paste(img, ((side - w) // 2, (side - h) // 2))
    return canvas


# --------------------------------------------------------------------------- inputs

def records_from_directory(directory: PathLike, brand: Optional[str] = None) -> List[ImageRecord]:
    """Every supported image under `directory` (recursive); the file stem is used as ad_id."""
    d = Path(directory)
    return [ImageRecord(ad_id=p.stem, brand=brand or (p.parent.name if p.parent != d else None), image_path=p)
            for p in sorted(d.rglob("*")) if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]


def parse_requirements(specs: Optional[Sequence[str]]) -> Dict[str, List[str]]:
    """["final_status=VERIFIED", "image_type=static,video_thumbnail"] -> {col: [allowed, ...]}."""
    req: Dict[str, List[str]] = {}
    for spec in specs or []:
        if "=" not in spec:
            raise ValueError(f"--require expects COLUMN=VALUE[,VALUE...], got {spec!r}")
        col, vals = spec.split("=", 1)
        col, allowed = col.strip(), [v.strip() for v in vals.split(",") if v.strip()]
        if not col or not allowed:
            raise ValueError(f"--require expects COLUMN=VALUE[,VALUE...], got {spec!r}")
        req.setdefault(col, [])
        req[col] = [v for v in req[col] if v in allowed] if req[col] else allowed  # repeated col -> intersect
    return req


def file_sha256(path: PathLike) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_rows(p: Path) -> List[dict]:
    if p.suffix.lower() == ".csv":
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("ads", data.get("records", [])) if isinstance(data, dict) else data


def check_unique_ad_ids(records: Sequence["ImageRecord"]) -> None:
    seen, dups = set(), []
    for r in records:
        if r.ad_id in seen:
            dups.append(r.ad_id)
        seen.add(r.ad_id)
    if dups:
        raise DuplicateAdIdError(f"duplicate ad_id(s) in selection: {sorted(set(dups))} — "
                                 "each ad must map to exactly one feature record")


def select_from_dataset(dataset: PathLike, base_dir: PathLike = ".",
                        requirements: Optional[Dict[str, List[str]]] = None) -> Tuple[List[ImageRecord], Dict]:
    """
    Read ad_id / brand / local_image_path rows from a dataset CSV or JSON ({"ads": [...]} or a list)
    and keep only rows where every `requirements` column holds one of its allowed values.
    This is how unverified creatives are kept out of feature extraction.

    Returns (records, selection) where selection documents what was kept and why rows were
    excluded. Each excluded row is counted once, under the first failing condition (in the
    order given), so n_excluded_by_condition sums to n_rows - n_selected.
    Raises DuplicateAdIdError if a selected ad_id occurs twice.
    """
    p = Path(dataset)
    rows = _read_rows(p)
    requirements = requirements or {}
    base = Path(base_dir)
    out: List[ImageRecord] = []
    excluded: Dict[str, int] = {}
    excluded_ids: List[str] = []
    for r in rows:
        reason = None
        for col, allowed in requirements.items():
            if str(r.get(col, "")) not in allowed:
                reason = f"{col} not in {allowed}"
                break
        img = r.get("local_image_path") or r.get("image_path")
        if reason is None and not img:
            reason = "no image path"
        if reason is None and not r.get("ad_id"):
            reason = "no ad_id"
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
            excluded_ids.append(str(r.get("ad_id", "")))
            continue
        out.append(ImageRecord(ad_id=str(r["ad_id"]), brand=r.get("brand"),
                               image_path=(base / img) if not Path(img).is_absolute() else Path(img),
                               extra={"image_path_raw": img}))
    check_unique_ad_ids(out)
    selection = {"dataset": str(p), "dataset_sha256": file_sha256(p), "requirements": requirements,
                 "n_rows": len(rows), "n_selected": len(out), "n_excluded": len(rows) - len(out),
                 "n_excluded_by_condition": excluded, "excluded_ad_ids": excluded_ids}
    return out, selection


def records_from_dataset(dataset: PathLike, base_dir: PathLike = ".",
                         status_column: Optional[str] = None,
                         allowed_statuses: Optional[List[str]] = None,
                         requirements: Optional[Dict[str, List[str]]] = None) -> List[ImageRecord]:
    """Backward-compatible wrapper: status_column/allowed_statuses become one requirement."""
    req = dict(requirements or {})
    if status_column and allowed_statuses is not None:
        req[status_column] = list(allowed_statuses)
    return select_from_dataset(dataset, base_dir, req)[0]


def iter_loaded(records: List[ImageRecord]) -> Iterator[tuple]:
    """Yield (record, PreparedImage | None, error | None) without ever raising."""
    for rec in records:
        try:
            yield rec, load_image(rec.image_path), None
        except ImageLoadError as e:
            yield rec, None, str(e)
