"""
AdVision AI — Creative Image Capturer
Provides functions to generate and execute browser element-level screenshot capture
for both static images and video preview posters directly from the compositor layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

# JavaScript capture snippet for Playwright browser context
JS_CAPTURE_SNIPPET = """async (page) => {
  const ads = %s;
  const results = [];

  for (const ad of ads) {
    const url = `https://www.facebook.com/ads/library/?id=${ad.id}`;
    const outPath = `creatives/${ad.brandSlug}/${ad.id}.png`;
    
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(2500);

      const tagged = await page.evaluate((ad) => {
        const id = ad.id;
        const all = Array.from(document.querySelectorAll('*'));
        const idEl = all.find(el => 
          !['NOSCRIPT', 'SCRIPT', 'STYLE', 'HEAD', 'META'].includes(el.tagName) &&
          el.children.length === 0 &&
          el.textContent.includes(id)
        );

        let card = null;
        if (idEl) {
          let curr = idEl;
          while (curr && curr !== document.body) {
            const idCount = (curr.innerText.match(/Library ID:/g) || []).length;
            if (idCount === 1) {
              card = curr;
            } else if (idCount > 1) {
              break;
            }
            curr = curr.parentElement;
          }
        }

        const scope = card || document;

        // 1. Check video
        const video = scope.querySelector('video');
        if (video) {
          video.setAttribute('data-target-creative', id);
          return { success: true, type: 'video' };
        }

        // 2. Check images
        const imgs = Array.from(scope.querySelectorAll('img')).filter(img => {
          const w = img.naturalWidth || img.offsetWidth;
          const h = img.naturalHeight || img.offsetHeight;
          return (w > 120 || h > 120) && !img.src.includes('s60x60');
        });

        if (imgs.length > 0) {
          imgs.sort((a, b) => {
            const areaA = (a.naturalWidth || a.offsetWidth) * (a.naturalHeight || a.offsetHeight);
            const areaB = (b.naturalWidth || b.offsetWidth) * (b.naturalHeight || b.offsetHeight);
            return areaB - areaA;
          });
          imgs[0].setAttribute('data-target-creative', id);
          return { 
            success: true, 
            type: 'image', 
            w: imgs[0].naturalWidth || imgs[0].offsetWidth, 
            h: imgs[0].naturalHeight || imgs[0].offsetHeight 
          };
        }

        // 3. Fallback: media card container
        const container = scope.querySelector('div[style*="background-image"], ._7jyr, .x15mokao');
        if (container) {
          container.setAttribute('data-target-creative', id);
          return { success: true, type: 'container' };
        }

        return { success: false, reason: 'No media element found in card' };
      }, ad);

      if (!tagged.success) {
        results.push({ id: ad.id, brand: ad.brand, success: false, reason: tagged.reason });
        continue;
      }

      const target = page.locator(`[data-target-creative="${ad.id}"]`);
      await target.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await target.screenshot({ path: outPath });

      await page.evaluate((id) => {
        const el = document.querySelector(`[data-target-creative="${id}"]`);
        if (el) el.removeAttribute('data-target-creative');
      }, ad.id);

      results.push({
        id: ad.id,
        brand: ad.brand,
        success: true,
        type: tagged.type,
        outPath,
        method: tagged.type === 'video' ? 'browser_element_screenshot_video_preview' : 'browser_element_screenshot_image'
      });
    } catch (err) {
      results.push({ id: ad.id, brand: ad.brand, success: false, error: err.message });
    }
  }

  return results;
}
"""


def generate_capture_script(ads: List[Dict[str, Any]], output_file: Path) -> Path:
    """
    Generate a standalone Playwright JS execution script for a batch of ads.
    """
    formatted_ads = [
        {
            "id": str(ad.get("ad_library_id", ad.get("id"))),
            "brand": ad.get("brand_name", ad.get("brand")),
            "brandSlug": ad.get("brandSlug", ad.get("brand", "").lower().replace(" ", "_")),
            "format": ad.get("creative_format", ad.get("format", "Image"))
        }
        for ad in ads
    ]
    script_content = JS_CAPTURE_SNIPPET % json.dumps(formatted_ads, indent=2)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    return output_file

