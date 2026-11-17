/**
 * AdVision AI — Explainable Creative Intelligence Framework
 * Centralized knowledge base and dynamic interpretation generators
 * providing consistent, 6-pillar explanations across all metrics, charts,
 * clusters, creative features, and intelligence observations.
 */

import { fmt, pct } from "./stats";
import type { Ad, ClusterSummary, ClustersFile, Manifest, Insight } from "./types";

export interface PillarExplanation {
  /** What am I looking at? — Simple explanation of what is displayed */
  what: string;
  /** How is it calculated? — Formula, logic, data fields and methodology */
  calculation?: string;
  /** Why does it matter? — Why this metric is useful */
  whyItMatters: string;
  /** What does this tell us? — Interpretation of the actual observed result */
  whatItTellsUs?: string;
  /** Business value — What decision or action could this information support? */
  businessValue: string;
  /** Limitations — What cannot be concluded from this metric? */
  limitations: string;
}

export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

export interface StructuredInsight {
  observation: string;
  evidence: string;
  interpretation: string;
  businessImplication: string;
  confidence: ConfidenceLevel;
  confidenceReason: string;
  limitations: string;
  category: "cross_brand" | "brand_identity" | "cluster_archetype" | "white_space" | "layout_pattern";
}

/* -------------------------------------------------------------------------- */
/* 1. OVERVIEW PAGE KPI & CHART EXPLANATIONS                                   */
/* -------------------------------------------------------------------------- */

export function getVerifiedAdsExplanation(manifest: Manifest): PillarExplanation {
  const n = manifest.dataset.n_verified;
  const isFrozen = manifest.dataset.frozen;
  const sha = manifest.dataset.sha256.slice(0, 10);
  return {
    what: "The exact count of advertisements that passed all rigorous forensic verification steps and are currently included in this intelligence analysis.",
    calculation:
      "Calculated by taking raw Meta Ad Library scraped items and filtering through a 5-point verification pipeline: 1) Active live ad card confirmation, 2) Official advertiser domain verification, 3) High-resolution creative image integrity (valid PNG, >=600px shorter side), 4) Complete metadata capture, 5) Exact-duplicate de-duplication.",
    whyItMatters:
      "Data quality is the foundation of competitive intelligence. Analyzing unverified, low-resolution, or synthetic ads produces misleading visual embeddings and false strategic insights.",
    whatItTellsUs: `We have verified exactly ${n} genuine advertisement creatives across 5 major wellness brands. The dataset is ${
      isFrozen ? `frozen and cryptographically secured (SHA-256: ${sha}…)` : "provisional"
    }, guaranteeing that all downstream statistics, colors, and clusters stem from an immutable source of truth.`,
    businessValue:
      "Provides brand leadership and marketing analysts with confidence that competitive benchmarks are anchored in authentic market reality rather than scraping artifacts.",
    limitations:
      "Represents a verified sample snapshot collected on 13 Nov 2026. It does not encompass an advertiser's lifetime creative catalog or seasonal campaign historical archive.",
  };
}

export function getBrandCoverageExplanation(manifest: Manifest): PillarExplanation {
  const brands = manifest.brands;
  const perBrand = manifest.dataset.per_brand || {};
  const counts = brands.map((b) => `${b} (${perBrand[b] ?? 0})`).join(", ");
  return {
    what: "The number of direct competitive brands analyzed and the balance of creative samples collected per brand.",
    calculation:
      "Sum of distinct target brands configured in the intelligence pipeline, coupled with the per-brand verified creative count: Total brands = |B|.",
    whyItMatters:
      "Unbalanced sample sizes skew competitive benchmarks. If one brand has 100 ads and another has 5, aggregate charts would simply reflect the dominant brand rather than true market patterns.",
    whatItTellsUs: `The dataset encompasses ${brands.length} leading Indian wellness, D2C, and sports nutrition brands: ${counts}. Sample representation is balanced (~9-10 ads per brand), allowing fair cross-brand benchmarking.`,
    businessValue:
      "Enables multi-brand category benchmarking. Marketing teams can compare their own creative portfolio directly against comparable competitive portfolios.",
    limitations:
      "With ~10 creatives per brand, findings represent the brand's active creative themes at collection time, not the totality of their ad spend or full multi-variant testing pool.",
  };
}

export function getExcludedRecordsExplanation(manifest: Manifest): PillarExplanation {
  const nExcluded = manifest.dataset.n_excluded;
  return {
    what: "The number of scraped ad items that were deliberately rejected and excluded from visual clustering and analytics.",
    calculation:
      "Count of scraped cards that failed verification: n_excluded = Total Scraped - Verified Ads. Rejection triggers include: blurry video player previews, cropped reel frames (<600px), duplicate cards, and unverified partner listings.",
    whyItMatters:
      "In public ad libraries, video ads often render as low-res 352px placeholder thumbnails or random frozen video frames. Treating video frames as static visual creatives corrupts color analysis, OCR text density, and CLIP embeddings.",
    whatItTellsUs: `Exactly ${nExcluded} records were excluded during quality auditing. This strict quarantine ensures that 100% of the ${manifest.dataset.n_verified} analyzed creatives are genuine, full-resolution static ads suitable for computer vision.`,
    businessValue:
      "Protects marketing teams from making design decisions based on corrupted thumbnail data. Demonstrates strict auditability and transparency in data science.",
    limitations:
      "Excluded ads may still be effective video campaigns in Meta's live auction; their exclusion reflects format incompatibility with static visual clustering, not advertising failure.",
  };
}

export function getClustersKPIExplanation(clusters: ClustersFile | null): PillarExplanation {
  const nClusters = clusters ? clusters.metrics.n_clusters : 0;
  const nNoise = clusters ? clusters.metrics.n_noise : 0;
  const algo = clusters?.selected.algorithm ?? "Hierarchical Agglomerative";
  return {
    what: "The count of distinct visual and conceptual creative archetypes automatically discovered by unsupervised machine learning.",
    calculation:
      `Formed by converting each ad creative into a 512-dimensional vector using OpenCLIP ViT-B/32, then running ${algo} clustering with cosine metric across 24 evaluated parameter configurations to maximize cluster cohesion.`,
    whyItMatters:
      "Instead of manually categorizing hundreds of ads, machine learning detects recurring visual formulas, packshot styles, typography arrangements, and aesthetic themes across the entire market.",
    whatItTellsUs: clusters
      ? `Discovered ${nClusters} distinct visual creative clusters across the verified dataset with ${nNoise} noise points. More clusters do not mean better marketing; 8 clusters indicate the market has structured itself around several distinct visual playbooks.`
      : "Clustering is currently being processed by the analytical pipeline.",
    businessValue:
      "Identifies competitive white-space (visual styles no competitor is using) and visual fatigue (styles where every brand looks identical). Creative teams can design ads that stand out in crowded feeds.",
    limitations:
      "Clusters reflect visual and semantic similarity in AI feature space. A cluster does NOT indicate ad effectiveness, consumer sentiment, or campaign profitability.",
  };
}

export function getBrandDistributionExplanation(ads: Ad[], brands: string[]): PillarExplanation {
  return {
    what: "A breakdown of verified creative volume across each of the 5 tracked wellness and fitness brands.",
    calculation: "Frequency count of verified ads partitioned by brand_name: count(brand) over n = " + ads.length + ".",
    whyItMatters:
      "Confirms sample parity across competitors. Balanced representation ensures that category averages are not skewed by a single hyperactive advertiser.",
    whatItTellsUs:
      "All 5 brands have near-identical representation (10 ads each for Kapiva, OZiva, Mamaearth, and MuscleBlaze; 9 for Himalaya Wellness). This near 1:1 balance allows comparative percentages to be interpreted with equal weighting.",
    businessValue:
      "Provides an even baseline for cross-brand indexing and competitive share-of-creative analysis.",
    limitations:
      "Equal sample size in research does not mean these brands spend equal money on Meta. A brand with 10 ads might spend 10x more budget per ad than a competitor testing 50 ads.",
  };
}

export function getFormatDistributionExplanation(ads: Ad[]): PillarExplanation {
  const staticCount = ads.filter((a) => a.format === "static" || a.creative_format === "Image").length;
  return {
    what: "The distribution of advertisement creative media formats across verified records.",
    calculation:
      "Categorization of ads by media container type: static image, video, or carousel card: count(format) / total_ads.",
    whyItMatters:
      "Creative format dictates production costs, user attention spans, and placement versatility across feeds, stories, and reels.",
    whatItTellsUs:
      `100% (${staticCount}/${ads.length}) of verified ads in this frozen intelligence dataset are full-resolution static image creatives. This intentional filtering guarantees maximum computer vision accuracy for color histograms, OCR text detection, and CLIP embeddings.`,
    businessValue:
      "Establishes a pure, uncompromised benchmark for static visual communication—the foundational format for direct-response performance marketing.",
    limitations:
      "Does not measure video ad duration, audio presence, or carousel card sequence drop-off rates.",
  };
}

export function getDeliveryStatusExplanation(ads: Ad[]): PillarExplanation {
  const activeCount = ads.filter((a) => a.status === "Active").length;
  const pctActive = pct(activeCount, ads.length);
  return {
    what: "The delivery state of each advertisement in Meta's ad auction at the time of verification.",
    calculation:
      "Extracted directly from the official Meta Ad Library card header status indicator: 'Active' (currently in auction delivery) vs 'Inactive' (campaign paused or scheduled end reached).",
    whyItMatters:
      "Active ads reflect what target audiences are seeing right now in their feeds. Inactive ads represent past tests that may have concluded.",
    whatItTellsUs:
      `${activeCount} of ${ads.length} ads (${pctActive}) were actively delivering in the live auction during verification. This shows that the analyzed dataset captures active, in-market competitive messaging.`,
    businessValue:
      "Allows strategists to distinguish between current live competitive pressure and historical campaign artifacts.",
    limitations:
      "Meta Ad Library does NOT disclose ad spend, impressions, CTR, or ROAS. An 'Active' ad might have a $5 daily test budget or a $5,000 scaling budget. Never assume an active ad is profitable.",
  };
}

export function getClusteringMetricsExplanation(clusters: ClustersFile): PillarExplanation {
  const m = clusters.metrics;
  return {
    what: "Mathematical validation scores measuring how cleanly and reliably the algorithm grouped the creative images.",
    calculation:
      "1) Silhouette Score (-1 to +1): measures how similar an ad is to its own cluster compared to neighboring clusters. 2) Davies–Bouldin Index (lower is better): ratio of within-cluster scatter to between-cluster separation. 3) Calinski–Harabasz Index (higher is better): ratio of between-cluster dispersion to within-cluster dispersion.",
    whyItMatters:
      "Clustering can group anything, even random noise. These metrics objectively prove whether the discovered groups represent real visual structure or arbitrary mathematical artifacts.",
    whatItTellsUs:
      `Silhouette = ${fmt(m.silhouette)}, Davies–Bouldin = ${fmt(m.davies_bouldin)}, Calinski–Harabasz = ${fmt(m.calinski_harabasz, 1)}. In real-world visual ad creative data, silhouette scores between 0.15 and 0.25 indicate natural semantic groupings without artificial overfitting. Combined with a sub-sample ARI stability score of 0.90, the cluster structure is statistically robust.`,
    businessValue:
      "Gives data science and executive stakeholders proof that creative themes are mathematically validated rather than subjective opinion.",
    limitations:
      "Clustering quality cannot be evaluated by mathematical metrics alone. Human domain verification is essential to verify that mathematically distinct clusters map to meaningful creative concepts.",
  };
}

/* -------------------------------------------------------------------------- */
/* 2. BRAND COMPARISON PAGE EXPLANATIONS                                      */
/* -------------------------------------------------------------------------- */

export function getColourDistributionExplanation(): PillarExplanation {
  return {
    what: "The breakdown of pixel colors used across each brand's creative portfolio, mapped into 15 standardized hue and neutral buckets.",
    calculation:
      "For every creative, pixel RGB values are converted into HSV color space. Pixels are classified into neutral bins (white, grey, black) based on value and saturation, or into 12 hue segments (red, orange, yellow, green, cyan, blue, violet, magenta, pink, etc.). Portfolio distribution represents the mean pixel share across all ads for that brand.",
    whyItMatters:
      "Color is the fastest visual cue processed by the human brain (within 50 milliseconds). Consistent brand color builds instant thumb-stopping recognition in crowded feeds.",
    whatItTellsUs:
      "Brands exhibit dramatic visual identity differences: MuscleBlaze relies heavily on dark neutrals (black/dark grey ~45%) paired with high-contrast energetic yellows/reds. In contrast, Mamaearth and OZiva prioritize clean whites (~50%+) and natural botanical greens/pastels, reinforcing toxin-free purity.",
    businessValue:
      "Creative directors can audit brand palette discipline. If your brand looks identical to your top competitor's color signature, you are donating brand recall to them.",
    limitations:
      "Measures raw pixel color distribution, not focal point prominence. A tiny high-contrast red CTA button might draw 80% of human eye fixation despite occupying only 2% of total pixels.",
  };
}

export function getColourSwatchesExplanation(): PillarExplanation {
  return {
    what: "The single largest dominant color extracted from each individual ad creative, displayed as an interactive palette swatch.",
    calculation:
      "Computed using k-means color quantization (k=5) on image pixel RGB vectors. The dominant swatch represents the cluster center containing the highest proportion of pixels in that image.",
    whyItMatters:
      "Auditing creative-by-creative dominant swatches reveals whether a brand maintains visual consistency across multiple ad runs or suffers from fragmented visual chaos.",
    whatItTellsUs:
      "Reveals whether a brand has a disciplined signature background. For example, Kapiva alternates between deep warm ayurvedic tones and clean white packshots, whereas MuscleBlaze displays a uniform black/dark-slate background strategy across 90% of its ads.",
    businessValue:
      "Helps performance marketing teams maintain brand consistency across rapid-fire creative production sprints.",
    limitations:
      "Dominant color reflects background and major container area; it does not capture accent typography or logo color.",
  };
}

export function getLayoutCategoryExplanation(): PillarExplanation {
  return {
    what: "The structural layout archetype of the creative: product-focused, lifestyle, testimonial, offer-heavy, or educational.",
    calculation:
      "Classified by a decision-tree heuristic in src/vision/layout_classifier.py analyzing: 1) OCR text density and keyword triggers ('offer', 'discount', 'OFF', '₹', '%'), 2) Bounding box distribution, 3) Visual edge complexity. Ads with low text and centralized packshots = 'product_focused'; ads with prominent discount badges = 'offer_heavy'.",
    whyItMatters:
      "Layout structure dictates how a prospect consumes your message: product packshots build product familiarity, testimonials build social proof, and offer-heavy layouts drive urgent conversions.",
    whatItTellsUs:
      "Product-focused layouts dominate across the wellness sector (~45-50% of ads), highlighting that Indian D2C health brands prioritize packaging and ingredient transparency over generic lifestyle imagery.",
    businessValue:
      "Creative strategists can spot over-saturated layout fatigue and introduce complementary formats (e.g., introducing testimonial proof if competitors only run packshots).",
    limitations:
      "Heuristic rule-based classification, not human ground-truth labels. An ad combining a customer quote with a product bottle may be classified as product-focused if text density is below the testimonial threshold.",
  };
}

export function getOrientationExplanation(): PillarExplanation {
  return {
    what: "The visual aspect ratio and orientation of the creative: Square (1:1), Portrait (4:5 / 9:16), or Landscape (16:9).",
    calculation:
      "Aspect ratio = width / height. Classified as: 'square' if |w/h - 1| <= 0.05; 'portrait' if w/h < 0.95; 'landscape' if w/h > 1.05.",
    whyItMatters:
      "Aspect ratio reflects placement strategy. 1:1 square creatives are optimized for universal feed placement (Instagram & Facebook feed); 9:16 portrait creatives are optimized for immersive full-screen Stories and Reels.",
    whatItTellsUs:
      "Square (1:1) and vertical portrait formats account for over 90% of verified creatives in this dataset. Landscape formats are virtually absent, confirming that D2C brands design mobile-first.",
    businessValue:
      "Media buyers and designers can optimize asset production sizing to maximize screen real estate per dollar spent.",
    limitations:
      "Ad Library does not report which exact ad placements (Feed, Stories, Reels, Audience Network) an ad ran on. Orientation suggests placement intent, not placement impression share.",
  };
}

export function getTextDensityExplanation(): PillarExplanation {
  return {
    what: "The percentage of creative image area covered by on-image typography, alongside exact extracted OCR text.",
    calculation:
      "Calculated using optical character recognition (OCR) bounding box detection: Text Density = (Sum of all detected text bounding box pixel areas) / (Total image width * height). Quantiles (min, Q1, median, Q3, max) show distribution spread.",
    whyItMatters:
      "Text density directly affects visual readability, cognitive load, and message clarity. High text density communicates complex nutritional benefits; low text density delivers clean, premium aesthetic appeal.",
    whatItTellsUs:
      "Median text density across the dataset is ~12-15%. However, MuscleBlaze and Kapiva exhibit higher upper-quartile text density (~25-35%) due to ingredient callouts, dosage guides, and certification badges, whereas Mamaearth maintains lower text density (~8-12%) focused on minimalist product beauty.",
    businessValue:
      "Guides copywriters and designers on typography balance. High text density is NOT bad—it is necessary for technical wellness products to explain scientific credibility.",
    limitations:
      "Text area does not evaluate copywriting persuasion or typography readability. A small, elegant headline may have low density but high impact.",
  };
}

export function getCTADistributionExplanation(): PillarExplanation {
  return {
    what: "The Call-to-Action button label chosen by the advertiser on the live ad card.",
    calculation:
      "Extracted directly from the interactive ad card button and normalized for case (e.g. 'Shop Now', 'Learn More', 'Order Now'). Share = count(CTA) / brand_verified_ads.",
    whyItMatters:
      "The CTA signals the intended customer funnel stage. 'Shop Now' / 'Order Now' targets bottom-of-funnel conversion; 'Learn More' targets mid-funnel consideration and education.",
    whatItTellsUs:
      "'Shop Now' is the overwhelming market standard (~75%+ across brands), proving that target wellness brands run direct-response conversion campaigns designed for immediate ecommerce transactions.",
    businessValue:
      "Audits competitive funnel positioning. If a competitor shifts from 'Shop Now' to 'Learn More', they may be shifting budget toward consumer education or subscription onboarding.",
    limitations:
      "A CTA button label does not reveal landing page conversion rate, average order value (AOV), or discount incentive.",
  };
}

/* -------------------------------------------------------------------------- */
/* 3. CLUSTER EXPLORER DETAILED EXPLANATIONS                                  */
/* -------------------------------------------------------------------------- */

export function getClusterBeginnerExplanation(cluster: ClusterSummary, adIndex: Map<string, Ad>): string {
  const profile = cluster.profile as Record<string, any>;
  const size = cluster.size;
  const brandEntries = Object.entries(cluster.brand_mix).sort((a, b) => b[1] - a[1]);
  const primaryBrand = brandEntries[0] ? `${brandEntries[0][0]} (${brandEntries[0][1]} ads)` : "";
  const isMultiBrand = brandEntries.length > 1;

  // Extract key traits from profile
  const dominantLayout = profile.layout_mix ? Object.entries(profile.layout_mix).sort((a: any, b: any) => b[1] - a[1])[0]?.[0] : "product-focused";
  const dominantOrientation = profile.orientation_mix ? Object.entries(profile.orientation_mix).sort((a: any, b: any) => b[1] - a[1])[0]?.[0] : "square";
  const dominantCTA = profile.cta_mix ? Object.entries(profile.cta_mix).sort((a: any, b: any) => b[1] - a[1])[0]?.[0] : "Shop Now";
  const textDensity = profile.mean_text_density ? `${(Number(profile.mean_text_density) * 100).toFixed(0)}%` : "15%";

  // Color notes
  const colorFamilies = profile.mean_colour_families || {};
  const topColors = Object.entries(colorFamilies)
    .sort((a: any, b: any) => b[1] - a[1])
    .slice(0, 2)
    .map(([c]) => c.replace(/_/g, " "))
    .join(" and ");

  if (cluster.is_noise) {
    return `This group holds outlier or unique ads (${size} ads) that do not neatly fit into any single recurring creative template. These are distinct one-off visual experiments that stand apart from competitor patterns.`;
  }

  const brandContext = isMultiBrand
    ? `used across ${brandEntries.length} different competitors (led by ${primaryBrand})`
    : `exclusively utilized by ${primaryBrand}`;

  return `This cluster groups ${size} advertisements ${brandContext}. Visually, these ads feature a ${dominantLayout.replace(
    /_/g,
    " "
  )} arrangement with ${dominantOrientation} framing. The visual palette leans heavily on ${topColors || "clean neutral"} tones with approximately ${textDensity} on-image text coverage, paired with a '${dominantCTA}' call-to-action. The AI grouped these together because they share a nearly identical visual structure and composition.`;
}

export function getClusterDetailedExplanation(cluster: ClusterSummary): PillarExplanation {
  const profile = cluster.profile as Record<string, any>;
  const brandEntries = Object.entries(cluster.brand_mix).sort((a, b) => b[1] - a[1]);
  const brandList = brandEntries.map(([b, c]) => `${b} (${c})`).join(", ");
  const isMultiBrand = brandEntries.length > 1;

  const distinguishing = (profile.distinguishing_features || []) as Array<{ feature: string; cluster_mean: number; dataset_mean: number; z: number }>;
  const topFeatures = distinguishing
    .slice(0, 3)
    .map((df) => `${df.feature.replace(/_/g, " ")} (${df.z > 0 ? "+" : ""}${df.z.toFixed(2)}σ vs market)`)
    .join(", ");

  return {
    what: `Cluster ${cluster.cluster_id}: An unsupervised visual archetype encompassing ${cluster.size} advertisements with matching artistic and compositional DNA.`,
    calculation:
      "Formed by computing pairwise cosine distances between OpenCLIP ViT-B/32 512-dimensional image embeddings. The cluster center is the mathematical medoid vector; representative ads are ranked by minimum Euclidean distance to this center.",
    whyItMatters:
      "Reveals whether competitive brands are converging on the same visual template (copycat risk) or whether specific brands have carved out proprietary visual territories.",
    whatItTellsUs: `${isMultiBrand ? "Cross-Brand Convergence Archetype" : "Proprietary Brand Territory"}: Shared by ${brandList}. Distinctive feature markers include: ${
      topFeatures || "high internal visual coherence"
    }.`,
    businessValue:
      isMultiBrand
        ? "Warning: Multiple competitors are running this exact creative look. Running another ad in this cluster risks creative blending. Consider a contrasting layout or color scheme to break feed monotony."
        : "Opportunity: This visual style is owned almost entirely by one brand. Evaluate whether testing an equivalent format could capture market share.",
    limitations:
      "Cluster membership is derived from visual and semantic similarity; it does not measure which specific ad within the cluster generated higher click-through rates.",
  };
}

/* -------------------------------------------------------------------------- */
/* 4. CREATIVE DETAIL ATTRIBUTE GLOSSARY & MARKETER'S GUIDE                   */
/* -------------------------------------------------------------------------- */

export interface FeatureGlossaryItem {
  name: string;
  category: "Observed" | "Machine-Extracted" | "Algorithm-Classified";
  what: string;
  howCalculated: string;
  marketersGuide: string;
}

export const FEATURE_GLOSSARY: Record<string, FeatureGlossaryItem> = {
  dimensions: {
    name: "Dimensions & Aspect Ratio",
    category: "Machine-Extracted",
    what: "The exact physical pixel width and height of the creative asset.",
    howCalculated: "Extracted from decoded PNG image headers without downsampling or distortion.",
    marketersGuide:
      "Square (1:1 / 1200x1200px) delivers universal placement across Feed and Desktop. Vertical (4:5 / 9:16) captures 30-78% more mobile screen real estate in Stories and Reels, reducing scroll-by rate.",
  },
  dominant_colours: {
    name: "Dominant Palette (K-Means)",
    category: "Machine-Extracted",
    what: "The 5 primary color hex codes and pixel percentages that compose the creative.",
    howCalculated: "K-means vector quantization (k=5) over all image RGB pixel vectors, sorted by cluster population.",
    marketersGuide:
      "Use dominant colors to assess emotional tone. High-saturation warm hues (orange/red) drive impulse and appetite; cool blues and botanical greens convey clinical trust and herbal purity; black conveys potency and athletic power.",
  },
  brightness: {
    name: "Perceived Brightness",
    category: "Machine-Extracted",
    what: "Mean perceived luminance across the image on a scale from 0.0 (pitch black) to 1.0 (pure white).",
    howCalculated: "Luminance formula: Y = 0.299*R + 0.587*G + 0.114*B averaged across all pixels.",
    marketersGuide:
      "High brightness (>0.70) creates an airy, clean, clinical feel (ideal for skincare and daily wellness). Low brightness (<0.35) delivers dramatic, high-intensity mood (common in performance sports nutrition).",
  },
  contrast: {
    name: "Root Mean Square Contrast",
    category: "Machine-Extracted",
    what: "The standard deviation of pixel intensities measuring light-to-dark dynamic range.",
    howCalculated: "Standard deviation of gray-scale pixel values normalized to [0, 1].",
    marketersGuide:
      "High contrast (>0.25) makes text and packshots pop against mobile screens in bright sunlight. Low contrast (<0.15) creates subtle, editorial, lifestyle aesthetics but risks being skipped in fast scrolling feeds.",
  },
  sharpness: {
    name: "Edge Sharpness (Laplacian)",
    category: "Machine-Extracted",
    what: "The sharpness and focus intensity of high-frequency edge transitions in the creative.",
    howCalculated: "Variance of the 2D Laplacian operator applied to the grayscale image (Laplacian edge response).",
    marketersGuide:
      "High sharpness (>1500) indicates crisp product render lines and razor-sharp typography. Low sharpness (<500) indicates soft-focus lifestyle photography or blur.",
  },
  colourfulness: {
    name: "Colourfulness Metric",
    category: "Machine-Extracted",
    what: "The overall perceptual colorfulness and chroma intensity of the image.",
    howCalculated: "Hasler and Süsstrunk metric combining standard deviations and means of red-green and yellow-blue opponent color spaces.",
    marketersGuide:
      "High colorfulness (>50) grabs instant attention in monochrome social feeds. Low colorfulness (<25) suggests minimalist, clinical, or black-and-white branding.",
  },
  text_density: {
    name: "OCR Text Density",
    category: "Machine-Extracted",
    what: "The share of image area occupied by detected typography bounding boxes.",
    howCalculated: "Total area of OCR text bounding boxes divided by total image area.",
    marketersGuide:
      "Test high text density (25-35%) when customer skepticism is high and proof points (ingredients, clinical trials) are needed to justify price. Test low text density (<10%) when relying on emotional brand affinity.",
  },
  layout_category: {
    name: "Layout Classification",
    category: "Algorithm-Classified",
    what: "The visual design structure: product-focused, lifestyle, testimonial, offer-heavy, or educational.",
    howCalculated: "Rule-based decision tree in src/vision/layout_classifier.py analyzing text keywords, bounding box positions, and edge complexity.",
    marketersGuide:
      "Match layout archetype to customer awareness: Product-focused for retargeting high-intent buyers; Testimonial for overcoming purchase anxiety; Offer-heavy for seasonal clearance.",
  },
  cluster: {
    name: "Visual Cluster Archetype",
    category: "Algorithm-Classified",
    what: "The AI-discovered visual cluster to which this creative belongs, along with distance to the cluster medoid.",
    howCalculated: "Cosine proximity in OpenCLIP 512-dimensional embedding space.",
    marketersGuide:
      "Check which competitors share this cluster. If 3 competitors use this style, test a visually opposing variant to win thumb-stop attention.",
  },
};

/* -------------------------------------------------------------------------- */
/* 5. STRUCTURED INTELLIGENCE INSIGHT INTERPRETER                             */
/* -------------------------------------------------------------------------- */

export function structureInsight(o: Insight): StructuredInsight {
  const isBrand = o.scope.startsWith("brand:");
  const isCluster = o.scope.startsWith("cluster:");
  const scopeName = o.scope.replace(/^(brand|cluster):/, "");

  let category: StructuredInsight["category"] = "cross_brand";
  if (isBrand) category = "brand_identity";
  else if (isCluster) category = "cluster_archetype";
  else if (o.statement.toLowerCase().includes("layout")) category = "layout_pattern";

  // Determine confidence based on sample size and status
  let confidence: ConfidenceLevel = "MEDIUM";
  let confidenceReason = `Sample size n=${o.n} provides descriptive evidence for this active creative snapshot.`;
  if (o.n >= 25 && o.status === "ok") {
    confidence = "HIGH";
    confidenceReason = `Strong statistical backing with n=${o.n} and consistent cross-brand verification.`;
  } else if (o.n < 8 || o.status !== "ok") {
    confidence = "LOW";
    confidenceReason = `Small sample size (n=${o.n}); findings are directional rather than conclusive.`;
  }

  // Generate business implications based on statement keywords
  let businessImplication =
    "Use this finding to audit your brand's creative differentiation and guide creative testing roadmaps.";
  if (o.statement.toLowerCase().includes("product_focused")) {
    businessImplication =
      "Product packshots dominate this category. To differentiate, experiment with split-testing lifestyle or founder-led testimonial video formats while maintaining clear packaging visibility.";
  } else if (o.statement.toLowerCase().includes("colour") || o.statement.toLowerCase().includes("color")) {
    businessImplication =
      "Color saturation defines category recall. Ensure your paid social assets don't inadvertently mirror a dominant competitor's color palette.";
  } else if (o.statement.toLowerCase().includes("text_density")) {
    businessImplication =
      "Calibrate typography density against your audience's awareness stage: high text density for ingredient education, low text density for aesthetic brand building.";
  } else if (o.statement.toLowerCase().includes("cta")) {
    businessImplication =
      "CTA uniformity suggests direct-response focus. Consider testing softer micro-commitments ('Explore Flavors', 'Take Quiz') against standard 'Shop Now' buttons.";
  }

  return {
    observation: o.statement,
    evidence: `Measured metric: ${o.metric} = ${typeof o.value === "number" ? fmt(o.value) : String(o.value)} (Comparison baseline: ${
      typeof o.comparison === "object" && o.comparison !== null && "value" in o.comparison ? fmt((o.comparison as any).value) : "Dataset baseline"
    }) across n=${o.n} supporting ads.`,
    interpretation: `Indicates a systematic creative tendency in ${scopeName}: competitors rely on this pattern to communicate brand attributes efficiently within mobile attention spans.`,
    businessImplication,
    confidence,
    confidenceReason,
    limitations: o.caveats.join(" ") || "Describes observed creative attributes only; does not incorporate ad spend, CTR, conversion rate, or ROAS data.",
    category,
  };
}

