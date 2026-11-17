/**
 * AdVision AI — Playwright Creative Image Capturer Script
 * Navigates to individual ad archive URLs and captures element-level screenshots
 * of decoded compositor frames (<video> preview poster or high-res <img> creative).
 */

const fs = require('fs');
const path = require('path');

async (page) => {
  // Read ads from data/processed/all_brands_ads.json if available
  let ads = [];
  const processedPath = 'data/processed/all_brands_ads.json';

  if (fs.existsSync(processedPath)) {
    const raw = JSON.parse(fs.readFileSync(processedPath, 'utf8'));
    ads = (raw.ads || []).map(a => ({
      id: a.ad_library_id,
      brand: a.brand_name,
      brandSlug: a.brand_name.toLowerCase().replace(' wellness', '').replace(' ', '_'),
      format: a.creative_format
    }));
  }

  const results = [];
  console.log(`Starting capture for ${ads.length} ads...`);

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
};

