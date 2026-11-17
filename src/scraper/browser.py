"""
AdVision AI — Playwright Browser Manager
Manages browser lifecycle, stealth viewport settings, and network error handling
for permitted public access to the Meta Ad Library.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from config.settings import BROWSER_CONFIG

logger = logging.getLogger(__name__)

# Check if playwright is installed in the Python environment
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@asynccontextmanager
async def launch_browser(
    headless: bool = True,
    timeout_ms: int = 30000
) -> AsyncGenerator[Any, None]:
    """
    Context manager that launches Chromium with anti-bot friendly defaults.
    
    Yields:
        page: Initialized Playwright Page object
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "Playwright is not installed. Please install it with:\n"
            "  pip install playwright && playwright install chromium"
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless or BROWSER_CONFIG["headless"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=BROWSER_CONFIG["user_agent"],
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = await context.new_page()
        page.set_default_timeout(timeout_ms or BROWSER_CONFIG["timeout_ms"])

        try:
            yield page
        finally:
            await context.close()
            await browser.close()

