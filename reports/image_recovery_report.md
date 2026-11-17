# Image Recovery Report

## Method

1. Open the public single-ad Ad Library URL with full query parameters (`?active_status=all&ad_type=all&country=IN&id=<ad_id>&media_type=all`). The legacy pipeline used the bare `?id=<ad_id>` form, which opens a generic results page rather than the ad. That is the root cause of the legacy image/ID mismatches.
2. Find the card whose text is exactly `Library ID: <ad_id>`, then climb to the largest ancestor that contains only that one Library ID.
3. Take that card's own creative: the first `<img>` ≥ 200 px (static / carousel first frame) or the `<video>` poster.
4. Download the asset bytes as served, in the same browser session. No screenshot, crop, re-encode or upscale is applied, so original and final dimensions are identical.
5. Record source URL, method, dimensions, SHA-256 and timestamp (`data/quality/recovery_manifest.csv`).

Implementation: `scripts/verify_creatives.py` (2 concurrent browser workers; stops if a login wall appears).

## Results

- Legacy IDs: 50/50 cards found, 50/50 assets recovered.
- Replacement candidates: 51/74 cards found, 51/74 assets recovered.
- Verified assets saved to `data/creatives/verified/<brand>/<ad_id>.<ext>`: 77

| Retrieval method | Assets |
|---|---|
| ad_library_card_img_src | 76 |
| ad_library_card_video_poster | 1 |

| Original = final dimensions | Assets |
|---|---|
| 600x600 | 42 |
| 480x600 | 14 |
| 338x600 | 13 |
| 600x314 | 2 |
| 600x599 | 2 |
| 337x600 | 1 |
| 1080x1350 | 1 |
| 491x600 | 1 |
| 600x318 | 1 |

## Strategies considered

| Strategy | Used? | Why |
|---|---|---|
| Public single-ad Ad Library page | Yes (primary) | Only source that ties an image to an exact Library ID and advertiser. |
| Advertiser's own Ad Library page listing (`view_all_page_id`) | Yes (replacement discovery) | Finds more same-brand ads; each one is then re-verified on its single-ad card. |
| Assets linked from the verified card (img src / video poster) | Yes | The card's own CDN asset, fetched in-session. |
| Advertiser websites / landing pages / campaign pages | No | Their images are product or catalogue assets that cannot be proven to be the creative of a given ad ID. |
| Search-engine images | No | Unverifiable provenance. |

## Failures

| Ad ID | Problem |
|---|---|
| 3942273605992757 | Page.evaluate: TypeError: Cannot read properties of null (reading 'innerText')     at eval (eval at evaluate (:302:30), <anonymous>:5:29)     at UtilityScript.evaluate (<anonymous>:309:18)     at UtilityScript.<anonymous> (<anonymous>:1:44) |
| 544783681900114 | Page.evaluate: TypeError: Cannot read properties of null (reading 'innerText')     at eval (eval at evaluate (:302:30), <anonymous>:5:29)     at UtilityScript.evaluate (<anonymous>:309:18)     at UtilityScript.<anonymous> (<anonymous>:1:44) |
| 1579052636955093 | card not found |
| 3526298977663233 | card not found |
| 1097801136024451 | card not found |
| 2612536639198625 | card not found |
| 2310669636438172 | card not found |
| 1788123239183968 | card not found |
| 1470753151777892 | card not found |
| 3347973938709454 | card not found |
| 1437067365050369 | card not found |
| 1578000820578757 | card not found |
| 4628013647521578 | card not found |
| 1066942962578472 | card not found |
| 1457602113067237 | card not found |
| 2168708153787350 | card not found |
| 3331088307078038 | card not found |
| 2318675842080786 | card not found |
| 1118461621041447 | card not found |
| 3299989700185233 | card not found |
| 1113048104460031 | card not found |
| 1997071155012631 | card not found |
| 1083648937651215 | card not found |
