"""
Interpretable image-property features (Pillow + numpy only, no model downloads).

  width / height / aspect_ratio / orientation
  brightness   mean luma (ITU-R 601) scaled to 0..1
  contrast     RMS contrast = std of luma, scaled to 0..1
  sharpness    variance of the 4-neighbour Laplacian after resizing the short side to 600px,
               so values are comparable between a 600px and a 1200px copy of the same ad.
               Rough guide for ad creatives: < 100 visibly soft, > 300 crisp.
  colourfulness  Hasler & Süsstrunk (2003) metric (0 = greyscale, > 60 strongly colourful)
  dominant_colours  k-means (k=5, k-means++ init, fixed seed) on a downsampled copy
  colour_distribution  share of pixels in 12 hue bins + white / black / grey buckets
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
from PIL import Image

from src.vision.preprocessing import resize_max_side, resize_short_side

HUE_BINS = ["red", "orange", "yellow", "yellow_green", "green", "green_cyan",
            "cyan", "azure", "blue", "violet", "magenta", "rose"]  # 30° each, centred on 0°, 30°, ...
SQUARE_TOLERANCE = 0.05  # |w/h - 1| <= 5% counts as square


def orientation(width: int, height: int, tol: float = SQUARE_TOLERANCE) -> str:
    r = width / height
    if abs(r - 1.0) <= tol:
        return "square"
    return "landscape" if r > 1 else "portrait"


def brightness_contrast(img: Image.Image) -> Dict[str, float]:
    luma = np.asarray(img.convert("L"), dtype=np.float64) / 255.0
    return {"brightness": round(float(luma.mean()), 4), "contrast": round(float(luma.std()), 4)}


def sharpness(img: Image.Image, short_side: int = 600, max_long_side: int = 2400) -> float:
    """Laplacian variance at a normalised scale. Extreme aspect ratios (> 4:1) are capped at
    max_long_side so a thin banner cannot be upscaled to hundreds of thousands of pixels."""
    g = np.asarray(resize_short_side(img, short_side, max_long_side).convert("L"), dtype=np.float64)
    if g.shape[0] < 3 or g.shape[1] < 3:
        return 0.0
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return round(float(lap.var()), 2)


def colourfulness(img: Image.Image) -> float:
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    rg = a[..., 0] - a[..., 1]
    yb = 0.5 * (a[..., 0] + a[..., 1]) - a[..., 2]
    return round(float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean())), 2)


def _kmeans(x: np.ndarray, k: int, iters: int = 25, seed: int = 0):
    rng = np.random.default_rng(seed)
    k = min(k, len(np.unique(x, axis=0)))
    centres = [x[rng.integers(len(x))]]
    for _ in range(1, k):  # k-means++ seeding
        d = np.min(((x[:, None, :] - np.array(centres)[None]) ** 2).sum(-1), axis=1)
        centres.append(x[rng.choice(len(x), p=d / d.sum())] if d.sum() > 0 else x[rng.integers(len(x))])
    c = np.array(centres, dtype=np.float64)
    for _ in range(iters):
        labels = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), axis=1)
        new = np.array([x[labels == j].mean(0) if np.any(labels == j) else c[j] for j in range(k)])
        if np.allclose(new, c, atol=0.5):
            break
        c = new
    labels = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), axis=1)
    return c, labels


def dominant_colours(img: Image.Image, k: int = 5, sample_side: int = 100) -> List[Dict]:
    """Top-k colours as [{hex, rgb, proportion}], largest share first."""
    small = resize_max_side(img.convert("RGB"), sample_side)
    x = np.asarray(small, dtype=np.float64).reshape(-1, 3)
    centres, labels = _kmeans(x, k)
    counts = np.bincount(labels, minlength=len(centres)) / len(labels)
    out = []
    for j in np.argsort(-counts):
        rgb = [int(round(v)) for v in centres[j]]
        out.append({"hex": "#{:02x}{:02x}{:02x}".format(*rgb), "rgb": rgb,
                    "proportion": round(float(counts[j]), 4)})
    return out


def colour_distribution(img: Image.Image) -> Dict[str, float]:
    """Pixel shares: neutral buckets (white/black/grey) plus 12 hue bins for chromatic pixels."""
    hsv = np.asarray(img.convert("RGB").convert("HSV"), dtype=np.float64) / 255.0
    h, s, v = hsv[..., 0].ravel(), hsv[..., 1].ravel(), hsv[..., 2].ravel()
    n = h.size
    black = v < 0.15
    white = (~black) & (v > 0.85) & (s < 0.12)
    grey = (~black) & (~white) & (s < 0.20)
    chroma = ~(black | white | grey)
    bins = (np.floor(((h[chroma] * 360 + 15) % 360) / 30)).astype(int)
    hist = np.bincount(bins, minlength=12) / n
    out = {"white": round(float(white.sum() / n), 4), "black": round(float(black.sum() / n), 4),
           "grey": round(float(grey.sum() / n), 4)}
    out.update({name: round(float(hist[i]), 4) for i, name in enumerate(HUE_BINS)})
    return out


def extract_image_properties(rgb: Image.Image, analysis_max_side: int = 512,
                             sharpness_short_side: int = 600, n_colours: int = 5) -> Dict:
    w, h = rgb.size
    small = resize_max_side(rgb, analysis_max_side)
    feats = {"width": w, "height": h, "aspect_ratio": round(w / h, 4), "orientation": orientation(w, h)}
    feats.update(brightness_contrast(small))
    feats["sharpness"] = sharpness(rgb, sharpness_short_side)
    feats["colourfulness"] = colourfulness(small)
    feats["dominant_colours"] = dominant_colours(small, n_colours)
    feats["colour_distribution"] = colour_distribution(small)
    return feats
