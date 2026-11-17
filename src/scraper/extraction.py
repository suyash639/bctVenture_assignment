"""
AdVision AI — Ad Data Extraction Utilities
Provides parsing functions for CTA text, redirect URL decoding, and format detection.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

# Standard Meta Ad CTA verbs (exact case prioritized)
KNOWN_CTAS = [
    "Shop now", "Shop Now",
    "Order now", "Order Now",
    "Learn more", "Learn More",
    "Get offer", "Get Offer",
    "Sign up", "Sign Up",
    "Subscribe",
    "Download",
    "Book now", "Book Now",
    "Contact us", "Contact Us",
    "Watch more", "Watch More",
    "Apply now", "Apply Now",
]


def decode_fb_redirect(url: Optional[str]) -> Optional[str]:
    """
    Extract the actual external merchant landing URL from an l.facebook.com redirect URL.
    
    Example:
        Input:  https://l.facebook.com/l.php?u=https%3A%2F%2Fkapiva.in%2Fjuice
        Output: https://kapiva.in/juice
    """
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if "l.facebook.com" in parsed.netloc or "l.facebook.com" in url:
            qs = parse_qs(parsed.query)
            u_vals = qs.get("u", [])
            if u_vals:
                return unquote(u_vals[0])
    except Exception:
        pass
    return url


def extract_cta(text: Optional[str]) -> Optional[str]:
    """
    Extract standard Call-to-Action (CTA) string from link text or headline.
    Preserves exact casing if matched at the end of the text.
    """
    if not text:
        return None

    cleaned = text.strip()
    # 1. Exact suffix match
    for cta in KNOWN_CTAS:
        if cleaned.endswith(cta):
            return cta

    # 2. Case-insensitive word boundary match
    for cta in KNOWN_CTAS:
        if re.search(r'\b' + re.escape(cta) + r'\b', cleaned, re.IGNORECASE):
            return cta

    # 3. Fallback: last two words if ending in a known action verb
    words = cleaned.split()
    if len(words) >= 2 and words[-1].lower() in ["now", "more", "today", "here"]:
        return " ".join(words[-2:])

    return None


def detect_creative_format(has_video: bool, has_carousel: bool = False) -> str:
    """
    Detect the ad creative format based on DOM media elements.
    """
    if has_carousel:
        return "Carousel"
    if has_video:
        return "Video"
    return "Image"
