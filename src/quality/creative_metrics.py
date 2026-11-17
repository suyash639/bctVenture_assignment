"""
Objective image-quality metrics for creative assets.

  metrics(path)   resolution, sharpness (Laplacian variance at a 600 px short side),
                  contrast, brightness, 64-bit difference hash
  dhash / hamming perceptual near-duplicate detection
  contact_sheet   labelled thumbnail grid for visual review
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
from PIL import Image, ImageDraw

from src.vision.image_features import brightness_contrast, sharpness
from src.vision.preprocessing import load_image


def dhash(im: Image.Image, n: int = 8) -> str:
    a = np.asarray(im.convert("L").resize((n + 1, n), Image.LANCZOS), dtype=np.int16)
    return "".join("1" if b else "0" for b in (a[:, 1:] > a[:, :-1]).flatten())


def metrics(path: Path) -> dict:
    im = load_image(path).rgb
    w, h = im.size
    bc = brightness_contrast(im)
    return {"path": str(path), "w": w, "h": h, "short_side": min(w, h),
            "sharpness": sharpness(im), "contrast": bc["contrast"], "brightness": bc["brightness"],
            "dhash": dhash(im)}


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def contact_sheet(paths: List[Path], labels: List[str], out: Path, cols: int = 5, t: int = 300) -> None:
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * t, rows * (t + 18)), "white")
    d = ImageDraw.Draw(sheet)
    for k, (p, lab) in enumerate(zip(paths, labels)):
        im = Image.open(p).convert("RGB")
        im.thumbnail((t, t))
        x, y = (k % cols) * t, (k // cols) * (t + 18)
        sheet.paste(im, (x + (t - im.width) // 2, y))
        d.text((x + 3, y + t + 3), lab, fill="black")
    sheet.save(out)
