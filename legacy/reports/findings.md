> **SUPERSEDED (2026-11-13).** This report describes the legacy dataset. Live Ad Library verification showed that many of its images and metadata rows belong to other ads or advertisers. Kept for audit only; see `reports/creative_quality_audit.md` and `docs/`.

# AdVision AI — Multi-Brand Strategic Findings & Ad Intelligence

## 1. Overview
This report provides key analytical insights derived from the 50 analyzed Meta advertisements across 5 leading Indian Direct-to-Consumer (D2C) and wellness brands: **Kapiva**, **OZiva**, **Mamaearth**, **Himalaya Wellness**, and **MuscleBlaze**.

---

## 2. Format Distribution & Creative Strategies

Across the 50 ads collected:
- **Video Creatives:** 28 ads (56.0%)
- **Static Image Creatives:** 22 ads (44.0%)

### Format Breakdown by Brand

| Brand | Video Ads | Image Ads | Video Ratio | Dominant Creative Angle |
| :--- | :---: | :---: | :---: | :--- |
| **Kapiva** | 8 | 2 | 80% | Problem-solution explainers (e.g., blood sugar management, ayurvedic juices). |
| **OZiva** | 5 | 5 | 50% | Balanced mix of celebrity endorsements (Bharti Singh) and quick commerce product showcases. |
| **Mamaearth** | 5 | 5 | 50% | Discount promotions ("Price Drop", "SAVE25"), UGC testimonials, product benefits (Rosemary oil, Multani Mitti). |
| **Himalaya Wellness** | 5 | 5 | 50% | Influencer parenting stories ("kids juggling school pressure"), Quick Commerce Blinkit delivery highlights. |
| **MuscleBlaze** | 5 | 5 | 50% | Celebrity fitness endorsements (Ajith, Vivek), athletic performance, multi-nutrient value propositions. |

---

## 3. Call-to-Action (CTA) Strategy

The analyzed brands show heavy reliance on conversion-focused direct sales CTAs:
- **`Shop Now` / `Shop now`:** 42 ads (84.0%)
- **`Order Now` / `Order now`:** 7 ads (14.0%) — exclusively used when routing traffic to Quick Commerce platforms like Blinkit or Amazon.
- **Unspecified / Native UI CTA:** 1 ad (2.0%)

---

## 4. Destination & Landing Page Routing

Brands utilize three distinct conversion funnels:
1. **D2C Official Storefronts (68%):** Direct links to Shopify/custom webstores (e.g., `kapiva.in`, `oziva.in`, `mamaearth.in`).
2. **Quick Commerce (18%):** Direct links to Blinkit (`link.blinkit.com`) for ultra-fast local delivery of impulse wellness items (e.g., face wash, shilajit, protein snacks).
3. **Marketplace & App Deep Links (14%):** Amazon India storefronts (`amazon.in`) and mobile app deep links (`mbl.app.link`).

All destination links pass through Meta's `l.facebook.com` redirect filter, which our extraction pipeline decodes to uncover the raw merchant destination URL and tracking parameters.

---

## 5. Next Steps for Step 3 & 4
1. **Visual Feature Extraction:** Compute color palette histograms, text density overlays, and visual embedding vectors (e.g., via CLIP or ViT) from the 50 local PNG creative files.
2. **Copy NLP Analysis:** Extract sentiment, pain-point urgency, offer types, and readability scores from ad primary copies.
3. **Multimodal Ad Clustering:** Group ads into functional creative archetypes (e.g., "Celebrity Endorsement", "Quick Commerce Flash Promo", "Scientific Educational Explainer").

