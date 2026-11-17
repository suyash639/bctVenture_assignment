"""
AdVision AI — Meta Ad Library Scraper Engine
Extracts public advertisement metadata from Meta Ad Library without requiring login,
strictly using publicly permitted accessibility tree and DOM inspection.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

from config.settings import (
    DEFAULT_ACTIVE_STATUS,
    DEFAULT_AD_TYPE,
    DEFAULT_COUNTRY_CODE,
    META_AD_DETAIL_URL_TEMPLATE,
    META_AD_LIBRARY_BASE_URL,
)
from src.scraper.extraction import extract_cta

logger = logging.getLogger(__name__)


def build_search_url(
    query: str,
    country_code: str = DEFAULT_COUNTRY_CODE,
    ad_type: str = DEFAULT_AD_TYPE,
    active_status: str = DEFAULT_ACTIVE_STATUS,
) -> str:
    """Construct Meta Ad Library search URL for a given brand query."""
    encoded_query = quote_plus(query)
    return (
        f"{META_AD_LIBRARY_BASE_URL}?"
        f"active_status={active_status}&ad_type={ad_type}&country={country_code}"
        f"&q={encoded_query}&search_type=keyword_unordered"
    )


def extract_ad_from_node(node: Dict[str, Any], brand_name: str) -> Optional[Dict[str, Any]]:
    """
    Extract ad fields from an accessibility snapshot node representing an ad card.
    """
    name = node.get("name", "") or ""
    if "Library ID:" not in name:
        return None

    # 1. Extract Library ID
    id_match = re.search(r'Library ID:\s*(\d+)', name)
    if not id_match:
        return None
    library_id = id_match.group(1).strip()

    # 2. Extract Status
    status = "Active" if "Active" in name[:100] else ("Inactive" if "Inactive" in name[:100] else "Active")

    # 3. Extract Start Date
    date_match = re.search(r'Started running on\s+([A-Za-z0-9,\s]+?)(?:\s*·|\s*$|\n)', name)
    start_date = date_match.group(1).strip() if date_match else None

    # 4. Check multiple versions
    has_multiple_versions = "multiple versions" in name.lower() or "use creative and text" in name.lower()

    # 5. Extract links, CTA, landing URL
    links = []
    def find_links(n: Dict[str, Any]):
        if n.get("role") == "link" or n.get("role") == "button":
            links.append(n.get("name", "") or "")
        for child in n.get("children", []):
            if isinstance(child, dict):
                find_links(child)
    find_links(node)

    cta = None
    landing_url = None
    landing_url_redirect = None
    link_headline = None

    for link_text in links:
        detected_cta = extract_cta(link_text)
        if detected_cta and not cta:
            cta = detected_cta
        if any(dom in link_text for dom in [".in", ".com", "http", "www."]):
            link_headline = link_text

    # 6. Format detection
    format_type = "Video" if "video" in name.lower() else "Image"

    return {
        "brand_name": brand_name,
        "page_name": brand_name,
        "ad_library_id": library_id,
        "ad_library_url": META_AD_DETAIL_URL_TEMPLATE.format(ad_id=library_id),
        "status": status,
        "start_date": start_date,
        "end_date": None,
        "ad_copy": None,
        "link_headline": link_headline,
        "cta": cta or "Shop Now",
        "creative_format": format_type,
        "has_multiple_versions": has_multiple_versions,
        "landing_page_url": landing_url,
        "landing_url_fb_redirect": landing_url_redirect,
        "creative_image_url": None,
        "collection_date": str(date.today()),
        "country": "India",
        "data_source": "Meta Ad Library (public, no login)",
    }

