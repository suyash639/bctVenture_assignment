"""
Score creative images: resolution, sharpness, contrast, brightness, dHash.

Usage: python scripts/score_creatives.py <out.json> <image> [<image> ...]
(Library code: src/quality/creative_metrics.py)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.quality import metrics  # noqa: E402
from src.quality.creative_metrics import contact_sheet, dhash, hamming  # noqa: E402,F401  (re-exported)

if __name__ == "__main__":
    out = Path(sys.argv[1])
    res = [metrics(Path(p)) for p in sys.argv[2:]]
    out.write_text(json.dumps(res, indent=1))
    for r in res:
        print(f"{Path(r['path']).stem:18} {r['w']}x{r['h']} sharp={r['sharpness']:7} "
              f"contrast={r['contrast']} brightness={r['brightness']}")
