"""
Text that is *visually present inside the creative* (OCR), as distinct from the ad copy /
headline fields in the metadata, which Meta renders around the creative.

Backend: RapidOCR (PaddleOCR models on ONNX Runtime; pip-only, CPU, Apple Silicon OK).
  - Detection is script-agnostic, so every detected text line counts toward density and
    placement, including Devanagari.
  - Recognition models are Chinese/English: Latin text and digits/₹ prices are read well;
    Hindi/Marathi text is usually dropped or garbled. Only recognitions with confidence
    >= min_confidence are included in `ocr_text`.

text_density (explainable approximation):
  union area of the axis-aligned bounding rectangles of all detected text lines
  divided by the image area (0..1). Rectangles are rasterised onto a mask so overlapping
  boxes are not double counted.

text_position:
  the image is split into horizontal thirds; each band's share of the text mask area is
  reported in text_position_distribution, and text_position is the band with the largest
  share ("none" when no text is detected).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from PIL import Image


class OcrUnavailableError(RuntimeError):
    pass


@dataclass
class TextBox:
    text: str
    confidence: float
    box: List[List[float]]  # 4 (x, y) corner points in original image pixels

    @property
    def rect(self):
        xs, ys = [p[0] for p in self.box], [p[1] for p in self.box]
        return min(xs), min(ys), max(xs), max(ys)


class RapidOcrBackend:
    name = "rapidocr_onnxruntime"

    def __init__(self):
        self._engine = None

    def load(self) -> "RapidOcrBackend":
        if self._engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
            except ImportError as e:
                raise OcrUnavailableError("rapidocr_onnxruntime not installed") from e
            self._engine = RapidOCR()
        return self

    def detect(self, rgb: Image.Image) -> List[TextBox]:
        self.load()
        bgr = np.ascontiguousarray(np.asarray(rgb.convert("RGB"))[..., ::-1])
        result, _ = self._engine(bgr)
        return [TextBox(text=str(t), confidence=float(s), box=[[float(x), float(y)] for x, y in b])
                for b, t, s in (result or [])]


def _reading_order(boxes: List[TextBox]) -> List[TextBox]:
    """Top-to-bottom, then left-to-right within lines whose vertical centres are close."""
    if not boxes:
        return []
    heights = [b.rect[3] - b.rect[1] for b in boxes]
    line_tol = max(4.0, 0.5 * float(np.median(heights)))
    return sorted(boxes, key=lambda b: (round(((b.rect[1] + b.rect[3]) / 2) / line_tol), b.rect[0]))


def text_mask(boxes: List[TextBox], width: int, height: int, scale: float = 0.25) -> np.ndarray:
    mw, mh = max(1, int(width * scale)), max(1, int(height * scale))
    mask = np.zeros((mh, mw), dtype=bool)
    for b in boxes:
        x0, y0, x1, y1 = b.rect
        c0, r0 = max(0, int(np.floor(x0 * scale))), max(0, int(np.floor(y0 * scale)))
        c1, r1 = min(mw, int(np.ceil(x1 * scale))), min(mh, int(np.ceil(y1 * scale)))
        if c1 > c0 and r1 > r0:
            mask[r0:r1, c0:c1] = True
    return mask


def text_features(boxes: List[TextBox], width: int, height: int,
                  min_confidence: float = 0.5) -> Dict:
    mask = text_mask(boxes, width, height)
    total = int(mask.sum())
    thirds = np.array_split(mask, 3, axis=0)
    shares = [int(t.sum()) / total if total else 0.0 for t in thirds]
    bands = ["top", "middle", "bottom"]
    readable = [b for b in _reading_order(boxes) if b.confidence >= min_confidence and b.text.strip()]
    return {
        "ocr_text": " ".join(b.text.strip() for b in readable),
        "ocr_n_text_regions": len(boxes),
        "ocr_n_readable_regions": len(readable),
        "ocr_mean_confidence": round(float(np.mean([b.confidence for b in boxes])), 4) if boxes else None,
        "text_density": round(total / mask.size, 4),
        "text_position": bands[int(np.argmax(shares))] if total else "none",
        "text_position_distribution": {b: round(s, 4) for b, s in zip(bands, shares)},
    }


def extract_ocr_features(rgb: Image.Image, backend: Optional[RapidOcrBackend] = None,
                         min_confidence: float = 0.5) -> Dict:
    backend = backend or RapidOcrBackend()
    boxes = backend.detect(rgb)
    return text_features(boxes, rgb.width, rgb.height, min_confidence)
