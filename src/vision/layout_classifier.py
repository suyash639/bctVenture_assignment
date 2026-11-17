"""
Transparent, rule-based layout labels for ad creatives.

Labels: product_focused, lifestyle, testimonial, offer_heavy, educational, unknown.

Inputs (each optional — rules that lack their input simply cannot fire):
  * OCR text (text visible in the creative, NOT metadata ad copy) -> keyword/regex cue counts
  * text_density / number of OCR text regions
  * CLIP zero-shot probabilities for a small set of scene prompts (VISUAL_PROMPTS)

Decision (first rule that fires wins; every fired cue is returned in `layout_reasons`):
  1. offer_heavy     >= 2 offer cues (price, % off, coupon, deal ...)
  2. testimonial     >= 2 testimonial cues (quotes, first person, rating, "review" ...)
  3. educational     >= 3 educational cues, or >= 2 cues with text_density >= 0.10
                     (small pack-label text on a packshot should not count as educational)
  4. lifestyle       CLIP P(person/scene prompts) >= 0.5 of the visual prompt mass
  5. product_focused CLIP P(packshot prompts) >= 0.5, or text_density < 0.12 with >= 1
                     product cue when CLIP is unavailable
  6. unknown         nothing fired

This is a heuristic, not a trained classifier; it has not been validated against
human labels, and Hindi text that OCR cannot read will not contribute cues.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

LABELS = ["product_focused", "lifestyle", "testimonial", "offer_heavy", "educational", "unknown"]

OFFER_PATTERNS = {
    "price_symbol": r"(₹|rs\.?|inr)\s?\d",
    "percent_off": r"\d{1,2}\s?%\s?(off|discount)?",
    # OCR often drops spaces ("OFFERPRICE"), so long unambiguous words match anywhere;
    # short ones keep word boundaries to avoid hits like "off" in "coffee".
    "offer_words": r"(offer|discount|coupon|cashback)|\b(off|sale|deal|code|save|flat|bogo|free)\b",
    "per_unit_price": r"\bper\s(day|glass|month|serving)\b|/(day|month)\b",
    "mrp": r"mrp",
    "limited": r"\b(limited|today only|hurry|last chance|ends)\b",
}
TESTIMONIAL_PATTERNS = {
    "quote_marks": r"[\"“”‘’]",
    "first_person": r"\b(i|i'm|i've|my|me)\b",
    "rating": r"[★⭐]|\b\d(\.\d)?\s?/\s?5\b|\b(stars?|rated)\b",
    "review_words": r"\b(review|reviews|testimonial|customers?|loved by|verified)\b",
    "attribution": r"(^|\s)[-–—]\s?[A-Z][a-z]+",
}
EDUCATIONAL_PATTERNS = {
    "benefit_verbs": r"\b(helps?|supports?|boosts?|reduces?|improves?|prevents?|fights?|manages?|controls?)\b",
    "science": r"\b(clinically|study|studies|proven|tested|research|formula|ingredients?)\b",
    "dosage": r"\b\d+\s?(mg|mcg|g|ml|iu)\b",
    "steps": r"\b(step|day|week|month)\s?0?\d\b|\bhow (to|it)\b|\bwhy\b",
    "comparison": r"\bvs\.?\b|\bbefore\b.*\bafter\b",
}
PRODUCT_PATTERNS = {
    "pack_words": r"\b(juice|capsules?|tablets?|powder|oil|shampoo|serum|cream|wash|resin|whey|protein|gummies)\b",
}

# Zero-shot prompts: key -> (group, prompt). Groups decide which rule the mass counts toward.
VISUAL_PROMPTS = {
    "packshot": ("product", "a product photo of a bottle, jar or pack on a plain background"),
    "product_closeup": ("product", "a close-up studio shot of a packaged health or beauty product"),
    "person_using": ("lifestyle", "a photo of a person using or holding a product in everyday life"),
    "people_scene": ("lifestyle", "a lifestyle photo of people at home, outdoors or at the gym"),
    "text_poster": ("graphic", "a graphic poster with lots of text and icons"),
}


def count_cues(text: str, patterns: Dict[str, str]) -> List[str]:
    t = text or ""
    flags = re.IGNORECASE
    return [name for name, pat in patterns.items()
            if re.search(pat, t, flags if name != "attribution" else 0)]


def visual_group_scores(zero_shot: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
    if not zero_shot:
        return None
    groups: Dict[str, float] = {}
    for key, p in zero_shot.items():
        g = VISUAL_PROMPTS[key][0]
        groups[g] = groups.get(g, 0.0) + float(p)
    return {g: round(v, 4) for g, v in groups.items()}


def classify_layout(ocr_text: Optional[str], text_density: Optional[float],
                    n_text_regions: Optional[int] = None,
                    zero_shot: Optional[Dict[str, float]] = None) -> Dict:
    text = ocr_text or ""
    offer = count_cues(text, OFFER_PATTERNS)
    testi = count_cues(text, TESTIMONIAL_PATTERNS)
    edu = count_cues(text, EDUCATIONAL_PATTERNS)
    prod = count_cues(text, PRODUCT_PATTERNS)
    vis = visual_group_scores(zero_shot)
    scores = {"offer_cues": offer, "testimonial_cues": testi, "educational_cues": edu,
              "product_cues": prod, "visual_groups": vis}

    def result(label, reasons):
        return {"layout_category": label, "layout_reasons": reasons, "layout_scores": scores}

    if len(offer) >= 2:
        return result("offer_heavy", [f"offer cues: {', '.join(offer)}"])
    if len(testi) >= 2:
        return result("testimonial", [f"testimonial cues: {', '.join(testi)}"])
    if len(edu) >= 3 or (len(edu) >= 2 and (text_density or 0) >= 0.10):
        return result("educational", [f"educational cues: {', '.join(edu)}",
                                      f"text_density {text_density}"])
    if vis is not None:
        if vis.get("lifestyle", 0) >= 0.5:
            return result("lifestyle", [f"CLIP lifestyle prompt mass {vis['lifestyle']:.2f} >= 0.5"])
        if vis.get("product", 0) >= 0.5:
            return result("product_focused", [f"CLIP product prompt mass {vis['product']:.2f} >= 0.5"])
    elif text_density is not None and text_density < 0.12 and prod:
        return result("product_focused", [f"low text density {text_density:.2f}",
                                          f"product cues: {', '.join(prod)}", "CLIP unavailable"])
    return result("unknown", ["no rule threshold met"])
