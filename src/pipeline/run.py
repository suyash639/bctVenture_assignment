"""
AdVision AI — end-to-end analysis pipeline.

    python -m src.pipeline.run --config config/analysis_pipeline.json
    python -m src.pipeline.run --stages validate            # just check inputs
    python -m src.pipeline.run --allow-provisional          # dev run on an unfrozen dataset

Stages (in order; --stages runs a subset):
  validate      dataset + freeze marker + feature outputs (src.vision validator)
  extract       optional: run src.vision.feature_pipeline (config.extraction.enabled)
  features      src.features: bundle + fused matrix per variant
  clustering    src.clustering: parameter sweep, stability, multi-criteria selection
  analytics     src.analytics: figures + ad-ID manifests
  intelligence  src.intelligence: traceable observations + cluster profiles
  report        markdown run report + run_manifest.json (hashes, config, versions, timings)

Freeze rule: a final run needs data/processed/DATASET_FROZEN.json whose sha256 matches the
dataset file. Without it the pipeline refuses, unless --allow-provisional is passed. In that
case every output goes under <outputs.root>/provisional/ and every report is stamped PROVISIONAL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STAGES = ["validate", "extract", "features", "clustering", "analytics", "intelligence", "report"]
log = logging.getLogger("advision.pipeline")


class PipelineError(RuntimeError):
    """A stage failed in a way the user must fix (bad input, missing freeze, failed validation)."""


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def relpath(p) -> str:
    """Repo-relative path when inside the repo, else the absolute path (never raises)."""
    p = Path(p).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def resolve(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


class Context:
    def __init__(self, cfg: dict, cfg_path: Path, allow_provisional: bool):
        self.cfg, self.cfg_path = cfg, cfg_path
        self.allow_provisional = allow_provisional
        self.provisional = False
        self.inp = {k: (resolve(v) if isinstance(v, str) else v) for k, v in cfg["inputs"].items()}
        self.out_root = resolve(cfg["outputs"]["root"])
        self.timings, self.summary, self.artifacts = {}, {}, {}
        self.bundle = self.matrices = self.assignments = None

    @property
    def out(self) -> Path:
        return self.out_root / "provisional" if self.provisional else self.out_root


# ----------------------------------------------------------------------------- stages

def stage_validate(ctx: Context):
    ds = ctx.inp["dataset_csv"]
    if not ds.is_file():
        raise PipelineError(f"dataset not found: {ds}")
    import csv
    rows = list(csv.DictReader(open(ds, encoding="utf-8")))
    req = ctx.inp.get("require") or {}
    sel = [r for r in rows if all(r.get(k) == v for k, v in req.items())]
    ids = [r["ad_id"] for r in sel]
    if not sel:
        raise PipelineError(f"no dataset rows satisfy {req}")
    if len(ids) != len(set(ids)):
        raise PipelineError("duplicate ad_id among selected dataset rows")
    ctx.summary["dataset"] = {"path": relpath(ds), "sha256": sha256(ds), "n_rows": len(rows),
                              "n_selected": len(sel), "require": req,
                              "per_brand": {b: sum(1 for r in sel if r["brand"] == b)
                                            for b in sorted({r["brand"] for r in sel})}}
    marker = ctx.inp["freeze_marker"]
    frozen = marker.is_file() and json.loads(marker.read_text()).get("dataset_sha256") == sha256(ds)
    if not frozen:
        why = "freeze marker missing" if not marker.is_file() else "dataset changed since it was frozen (sha256 mismatch)"
        if not ctx.allow_provisional:
            raise PipelineError(f"dataset is not frozen ({why}). Freeze it with "
                                f"`python -m src.pipeline.freeze` or pass --allow-provisional for a development run.")
        ctx.provisional = True
        log.warning("PROVISIONAL run: %s; outputs go to %s", why, ctx.out)
    ctx.summary["frozen"] = frozen
    if ctx.cfg.get("extraction", {}).get("enabled"):
        return  # features are (re)built by the extract stage, validated there
    _validate_features(ctx, ids)


def _validate_features(ctx: Context, expected_ids):
    fj, npy = ctx.inp["features_json"], ctx.inp["embeddings_npy"]
    if not fj.is_file() or not npy.is_file():
        raise PipelineError(f"feature outputs missing ({fj.name}, {npy.name}); enable extraction or run "
                            "src.vision.feature_pipeline first")
    from src.vision.feature_pipeline import validate_outputs
    req = {k: [v] if isinstance(v, str) else list(v) for k, v in (ctx.inp.get("require") or {}).items()}
    res = validate_outputs(fj, npy, ctx.inp["dataset_csv"], requirements=req or None, base_dir=ROOT)
    if not res.get("ok"):
        raise PipelineError(f"feature output validation failed: {res.get('errors')}")
    if res.get("failed_records"):
        log.warning("feature extraction failed for %d records: %s", len(res["failed_records"]), res["failed_records"])
    got = [r["ad_id"] for r in json.loads(fj.read_text())["records"]]
    if got != list(expected_ids):
        raise PipelineError("visual_features.json records do not match the selected dataset rows "
                            f"(features {len(got)}, dataset {len(expected_ids)}); re-run extraction")
    ctx.summary["features_validation"] = {"passed": True, "n_records": len(got)}


def stage_extract(ctx: Context):
    ex = ctx.cfg.get("extraction", {})
    if not ex.get("enabled"):
        log.info("extraction disabled in config; using existing feature outputs")
        return
    from src.vision import feature_pipeline as fp
    argv = ["--dataset", str(ctx.inp["dataset_csv"]), "--out-json", str(ctx.inp["features_json"]),
            "--out-npy", str(ctx.inp["embeddings_npy"]), "--device", ex.get("device", "cpu"),
            "--batch-size", str(ex.get("batch_size", 16))]
    for k, v in (ctx.inp.get("require") or {}).items():
        argv += ["--require", f"{k}={v}"]
    fp.main(argv)
    import csv
    ids = [r["ad_id"] for r in csv.DictReader(open(ctx.inp["dataset_csv"], encoding="utf-8"))
           if all(r.get(k) == v for k, v in (ctx.inp.get("require") or {}).items())]
    _validate_features(ctx, ids)


def stage_features(ctx: Context):
    from src.features import FusionConfig, build_feature_matrix, load_feature_bundle
    ctx.bundle = load_feature_bundle(ctx.inp["features_json"], ctx.inp["embeddings_npy"],
                                     ctx.inp["dataset_csv"], require_dataset_status=ctx.inp.get("require"))
    variants = {"clip": ctx.cfg["features"], **ctx.cfg.get("feature_variants", {})}
    ctx.matrices = {}
    for name, fc in variants.items():
        fm = build_feature_matrix(ctx.bundle, FusionConfig.from_dict(fc))
        fm.save(ctx.out / "features" / name)
        ctx.matrices[name] = fm
        if fm.excluded:
            log.warning("features[%s]: %d records excluded: %s", name, len(fm.excluded), fm.excluded)
    ctx.summary["features"] = {n: {"n_rows": len(fm.ad_ids), "n_dims": int(fm.X.shape[1]),
                                   "excluded": [list(e) for e in fm.excluded]} for n, fm in ctx.matrices.items()}
    ctx.summary["feature_issues"] = len(getattr(ctx.bundle, "issues", []))


def stage_clustering(ctx: Context):
    from src.clustering import ClusterConfig, default_grid, run_sweep, select_configuration, write_all
    cc = ctx.cfg.get("clustering", {})
    seed = ctx.cfg.get("seed", 0)
    ctx.summary["clustering"] = {}
    ctx.assignments = {}
    for name, fm in ctx.matrices.items():
        # the clustering engine reads brands from fm.brands for the assignments table
        fm.brands = {a: (ctx.bundle.records[a].get("brand") or (ctx.bundle.records[a].get("dataset") or {}).get("brand"))
                     for a in fm.ad_ids}
        if cc.get("grid", "default") == "default":
            grid = default_grid(len(fm.ad_ids), seed)
        else:
            grid = [ClusterConfig(g["algorithm"], g.get("params", {}), g.get("seed", seed)) for g in cc["grid"]]
        sweep = run_sweep(fm, grid, stability_seeds=cc.get("stability_seeds", [0, 1, 2, 3, 4]), seed=seed)
        choice = select_configuration(sweep)
        out = ctx.out / "clustering" / name
        paths = write_all(sweep, choice, out)
        if choice.config is None or "assignments" not in paths:
            raise PipelineError(f"clustering[{name}]: no acceptable configuration. {choice.rationale}")
        ctx.assignments[name] = paths["assignments"]
        ctx.summary["clustering"][name] = {"selected": choice.config.config_id, "warnings": choice.warnings,
                                           "n_configs": len(grid),
                                           "outputs": {k: relpath(v)
                                                       for k, v in paths.items()}}


def stage_analytics(ctx: Context):
    from src.analytics import generate_all
    ctx.summary["analytics"] = {}
    acfg = ctx.cfg.get("analytics", {})
    for name, fm in ctx.matrices.items():
        manifest = generate_all(ctx.bundle, fm, ctx.assignments[name], out_dir=ctx.out / "analytics" / name,
                                base_dir=ROOT, k_representatives=acfg.get("representatives_per_cluster", 3),
                                seed=ctx.cfg.get("seed", 0))
        arts = manifest.get("artifacts", []) if isinstance(manifest, dict) else manifest
        ctx.summary["analytics"][name] = {
            "n_artifacts": len(arts),
            "skipped": [a.get("path") or a.get("name") for a in arts if str(a.get("status", "")).startswith("skipped")]}


def stage_intelligence(ctx: Context):
    from src.intelligence import IntelligenceConfig, build_observations
    ctx.summary["intelligence"] = {}
    icfg = IntelligenceConfig(**ctx.cfg.get("intelligence", {}))
    for name in ctx.matrices:
        obs = build_observations(ctx.bundle, ctx.assignments[name], out_dir=ctx.out / "intelligence" / name,
                                 embeddings=getattr(ctx.bundle, "embeddings", None), config=icfg)
        statuses = {}
        for o in obs:
            st = getattr(o, "status", None) or (o.get("status") if isinstance(o, dict) else None) or "ok"
            statuses[st] = statuses.get(st, 0) + 1
        ctx.summary["intelligence"][name] = {"n_observations": len(obs), "by_status": statuses}


def stage_report(ctx: Context):
    import importlib.metadata as md
    versions = {}
    for pkg in ("numpy", "scikit-learn", "torch", "open_clip_torch", "rapidocr_onnxruntime", "matplotlib", "pillow"):
        try:
            versions[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            versions[pkg] = None
    manifest = {"provisional": ctx.provisional, "config_path": relpath(ctx.cfg_path),
                "config_sha256": sha256(ctx.cfg_path), "config": ctx.cfg,
                "inputs": {k: {"path": relpath(v), "sha256": sha256(v)}
                           for k, v in ctx.inp.items() if isinstance(v, Path) and v.is_file()},
                "summary": ctx.summary, "timings_s": ctx.timings, "python": platform.python_version(),
                "platform": platform.platform(), "versions": versions,
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    ctx.out.mkdir(parents=True, exist_ok=True)
    (ctx.out / "run_manifest.json").write_text(json.dumps(manifest, indent=1, default=str))
    report = resolve(ctx.cfg["outputs"]["report"])
    if ctx.provisional:
        report = ctx.out / "analysis_run_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(manifest))
    log.info("report written: %s", report)


def render_report(m: dict) -> str:
    s = m["summary"]
    head = ["# Analysis Run Report", ""]
    if m["provisional"]:
        head += ["> **PROVISIONAL**: the dataset was not frozen. These outputs are for development "
                 "only and must not be cited as findings.", ""]
    ds = s.get("dataset", {})
    lines = head + [
        f"- Finished: {m['finished_at']} · config `{m['config_path']}` (sha256 `{m['config_sha256'][:12]}`)",
        f"- Dataset: `{ds.get('path')}` sha256 `{(ds.get('sha256') or '')[:12]}`, "
        f"{ds.get('n_selected')} selected of {ds.get('n_rows')} rows ({ds.get('require')})",
        f"- Per brand: {ds.get('per_brand')}", "",
        "## Stages", "", "| Stage | Seconds |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in m["timings_s"].items()]
    lines += ["", "## Summary", "", "```json", json.dumps({k: v for k, v in s.items() if k != "dataset"},
                                                          indent=1, default=str), "```", ""]
    return "\n".join(lines)


STAGE_FUNCS = {"validate": stage_validate, "extract": stage_extract, "features": stage_features,
               "clustering": stage_clustering, "analytics": stage_analytics,
               "intelligence": stage_intelligence, "report": stage_report}
DEPENDS = {"features": ["validate"], "clustering": ["features"], "analytics": ["clustering"],
           "intelligence": ["clustering"], "report": []}


def run(cfg_path: Path, stages=None, allow_provisional=False) -> Context:
    cfg = json.loads(Path(cfg_path).read_text())
    ctx = Context(cfg, Path(cfg_path).resolve(), allow_provisional)
    wanted = stages or STAGES
    # in-memory dependencies: pull in prerequisite stages automatically
    order = []
    def add(s):
        for d in DEPENDS.get(s, []):
            add(d)
        if s not in order:
            order.append(s)
    for s in wanted:
        add(s)
    order = [s for s in STAGES if s in order]
    if "validate" not in order:
        order.insert(0, "validate")
    for s in order:
        t = time.time()
        log.info("stage %s: start", s)
        STAGE_FUNCS[s](ctx)
        ctx.timings[s] = round(time.time() - t, 2)
        log.info("stage %s: done in %.2fs", s, ctx.timings[s])
    return ctx


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=ROOT / "config/analysis_pipeline.json")
    ap.add_argument("--stages", nargs="+", choices=STAGES)
    ap.add_argument("--allow-provisional", action="store_true")
    ap.add_argument("--log-level", default=None, help="default: $LOG_LEVEL or INFO")
    a = ap.parse_args(argv)
    cfg_path = resolve(a.config)
    from src.utils.logging import setup_logging
    setup_logging(a.log_level, ROOT / "data/outputs/logs" / f"pipeline_{time.strftime('%Y%m%d_%H%M%S')}.log")
    try:
        run(cfg_path, a.stages, a.allow_provisional)
    except PipelineError as e:
        log.error("%s", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
