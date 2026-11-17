"""
CLIP image embeddings (open_clip), CPU/MPS friendly.

* Model, pretrained tag, device and batch size are configurable (config.VISION_CONFIG,
  ADVISION_CLIP_* env vars, or constructor args).
* Each creative is letter-boxed to a square before CLIP's own resize + centre-crop, so
  tall 4:5 / 9:16 ads are embedded whole instead of losing their top/bottom text.
* Embeddings are L2-normalised float32, so cosine similarity == dot product.
* Missing weights / no network raise ClipUnavailableError with an actionable message;
  callers decide whether to continue without embeddings.
"""

from __future__ import annotations

import os
from typing import List, Optional, Sequence

import numpy as np
from PIL import Image

from src.vision.preprocessing import pad_to_square, resize_max_side

# CLIP's input is 224 px; shrinking first keeps pad_to_square cheap for very large or
# extreme-aspect images (the letterbox canvas would otherwise be max(w, h)^2 pixels).
PRE_PAD_MAX_SIDE = 1024


class ClipUnavailableError(RuntimeError):
    pass


def resolve_device(requested: str = "cpu") -> str:
    import torch
    if requested == "auto":
        if torch.cuda.is_available():
            return "cuda"
        return "mps" if torch.backends.mps.is_available() else "cpu"
    if requested == "mps" and not torch.backends.mps.is_available():
        return "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return requested


def l2_normalise(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return (x / np.clip(n, 1e-12, None)).astype(np.float32)


class ClipEmbedder:
    def __init__(self, model_name: Optional[str] = None, pretrained: Optional[str] = None,
                 device: Optional[str] = None, batch_size: Optional[int] = None):
        from config.settings import VISION_CONFIG as C
        self.model_name = model_name or C["clip_model"]
        self.pretrained = pretrained or C["clip_pretrained"]
        self.requested_device = device or C["clip_device"]
        self.batch_size = batch_size or C["clip_batch_size"]
        self._model = self._preprocess = self._tokenizer = None
        self.device = None

    def load(self) -> "ClipEmbedder":
        if self._model is not None:
            return self
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        try:
            import open_clip
            import torch
        except ImportError as e:
            raise ClipUnavailableError(
                "torch/open_clip not installed: pip install torch open_clip_torch") from e
        self.device = resolve_device(self.requested_device)
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                self.model_name, pretrained=self.pretrained, device=self.device)
        except Exception as e:  # network failure, unknown tag, corrupt cache ...
            raise ClipUnavailableError(
                f"could not load CLIP {self.model_name}/{self.pretrained}: {e}. Weights are downloaded "
                "from Hugging Face on first use; connect once or pre-populate ~/.cache/huggingface.") from e
        model.eval()
        torch.manual_seed(0)
        self._model, self._preprocess = model, preprocess
        self._tokenizer = open_clip.get_tokenizer(self.model_name)
        return self

    @property
    def model_id(self) -> str:
        return f"open_clip:{self.model_name}/{self.pretrained}"

    @property
    def dim(self) -> int:
        self.load()
        return int(self._model.visual.output_dim)

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        """(N, D) float32, L2-normalised. Processes in batches of self.batch_size."""
        import torch
        self.load()
        if not images:
            return np.zeros((0, self.dim), dtype=np.float32)
        out: List[np.ndarray] = []
        with torch.no_grad():
            for i in range(0, len(images), self.batch_size):
                batch = torch.stack([self._preprocess(pad_to_square(resize_max_side(im.convert("RGB"), PRE_PAD_MAX_SIDE)))
                                     for im in images[i:i + self.batch_size]]).to(self.device)
                out.append(self._model.encode_image(batch).float().cpu().numpy())
        return l2_normalise(np.concatenate(out))

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        import torch
        self.load()
        with torch.no_grad():
            t = self._tokenizer(list(texts)).to(self.device)
            return l2_normalise(self._model.encode_text(t).float().cpu().numpy())

    def zero_shot(self, image_emb: np.ndarray, prompts: Sequence[str]) -> np.ndarray:
        """Softmax over prompts for each image (CLIP's logit scale of 100)."""
        logits = 100.0 * image_emb @ self.embed_texts(prompts).T
        logits -= logits.max(axis=1, keepdims=True)
        e = np.exp(logits)
        return e / e.sum(axis=1, keepdims=True)
