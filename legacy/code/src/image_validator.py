"""
Image Validator Utility
Validates PNG file integrity, magic byte signatures, dimensions, and file sizes
without requiring heavy external dependencies (pure Python standard library).
Compatible with Python 3.9+.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

PNG_MAGIC_BYTES = b"\x89PNG\r\n\x1a\n"


def inspect_png_header(file_path: Union[Path, str]) -> Tuple[bool, int, Optional[int], Optional[int]]:
    """
    Inspect a PNG file for validity and dimension extraction.
    
    Returns:
        (is_valid, file_size_bytes, width, height)
    """
    path = Path(file_path)
    if not path.is_file():
        return False, 0, None, None

    file_size = path.stat().st_size
    if file_size < 24:
        return False, file_size, None, None

    try:
        with open(path, "rb") as f:
            header = f.read(24)
        if header[:8] != PNG_MAGIC_BYTES:
            return False, file_size, None, None

        width, height = struct.unpack(">LL", header[16:24])
        return True, file_size, width, height
    except Exception:
        return False, file_size, None, None


def validate_creative_images(creatives_dir: Union[Path, str], brands: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate all PNG files in brand creative directories.

    Args:
        creatives_dir: Root creatives directory
        brands: Optional list of brand slugs to check (defaults to all subdirectories)

    Returns:
        Structured dictionary with brand-by-brand and overall validation metrics.
    """
    root = Path(creatives_dir)
    if not root.exists():
        return {"error": f"Directory not found: {root}", "total_valid": 0, "total_files": 0}

    if brands is None:
        target_dirs = [d for d in root.iterdir() if d.is_dir() and not d.is_symlink()]
    else:
        target_dirs = [root / b for b in brands if (root / b).exists()]

    brand_results = {}
    total_valid = 0
    total_files = 0

    for bdir in sorted(target_dirs):
        brand_name = bdir.name
        png_files = sorted(bdir.glob("*.png"))
        count = len(png_files)
        total_files += count

        valid_in_brand = 0
        sizes_kb = []
        details = []

        for p in png_files:
            is_valid, size, w, h = inspect_png_header(p)
            if is_valid and size > 1000 and w and h:
                valid_in_brand += 1
                total_valid += 1
                sizes_kb.append(size / 1024.0)
                details.append({
                    "filename": p.name,
                    "valid": True,
                    "size_kb": round(size / 1024.0, 1),
                    "dimensions": f"{w}x{h}"
                })
            else:
                details.append({
                    "filename": p.name,
                    "valid": False,
                    "size_kb": round(size / 1024.0, 1) if size else 0,
                    "dimensions": "invalid"
                })

        avg_size = round(sum(sizes_kb) / len(sizes_kb), 1) if sizes_kb else 0.0
        min_size = round(min(sizes_kb), 1) if sizes_kb else 0.0
        max_size = round(max(sizes_kb), 1) if sizes_kb else 0.0

        brand_results[brand_name] = {
            "total_files": count,
            "valid_files": valid_in_brand,
            "corrupt_files": count - valid_in_brand,
            "avg_size_kb": avg_size,
            "min_size_kb": min_size,
            "max_size_kb": max_size,
            "is_all_valid": (count > 0 and valid_in_brand == count),
            "files": details
        }

    return {
        "total_files": total_files,
        "total_valid": total_valid,
        "total_corrupt": total_files - total_valid,
        "success_rate": f"{(total_valid / total_files * 100):.1f}%" if total_files > 0 else "0%",
        "brands": brand_results
    }
