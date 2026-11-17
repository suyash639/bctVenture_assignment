"""
Unit tests for src/vision. Synthetic images give exact expected values; a couple of
tests use real local creatives when present. OCR / CLIP tests skip (not fail) when the
backend or its weights are unavailable, so the suite runs offline and under plain Python.

Run:  .venv/bin/python -m pytest tests/test_vision_features.py -v
"""

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config.settings import BASE_DIR
from src.vision.image_features import (
    brightness_contrast,
    colour_distribution,
    dominant_colours,
    extract_image_properties,
    orientation,
    sharpness,
)
from src.vision.layout_classifier import classify_layout
from src.vision.ocr_features import TextBox, text_features
from src.vision.preprocessing import (
    DuplicateAdIdError,
    ImageLoadError,
    ImageRecord,
    iter_loaded,
    load_image,
    pad_to_square,
    parse_requirements,
    records_from_dataset,
    resize_max_side,
    select_from_dataset,
)

# A verified creative (live card advertiser = "Kapiva Performance", see data/quality/live_cards.json).
REAL_CREATIVE = BASE_DIR / "data/quality/staging/1521879793036986.jpg"

try:
    import rapidocr_onnxruntime  # noqa: F401
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

_CLIP = None


def clip_or_skip(tc):
    global _CLIP
    try:
        from src.vision.clip_embeddings import ClipEmbedder, ClipUnavailableError
    except ImportError:
        tc.skipTest("clip module deps missing")
    if _CLIP is None:
        try:
            _CLIP = ClipEmbedder(device="cpu", batch_size=2).load()
        except ClipUnavailableError as e:
            tc.skipTest(f"CLIP unavailable: {e}")
    return _CLIP


class TmpDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def save(self, img, name):
        p = self.tmp / name
        img.save(p)
        return p


class TestPreprocessing(TmpDirCase):
    def test_rgba_composited_on_white(self):
        im = Image.new("RGBA", (10, 10), (255, 0, 0, 0))  # fully transparent red
        out = load_image(self.save(im, "a.png"))
        self.assertEqual(out.rgb.mode, "RGB")
        self.assertEqual(out.source_mode, "RGBA")
        self.assertEqual(out.rgb.getpixel((5, 5)), (255, 255, 255))

    def test_grayscale_and_palette_and_16bit(self):
        self.assertEqual(load_image(self.save(Image.new("L", (8, 8), 128), "g.png")).rgb.getpixel((0, 0)),
                         (128, 128, 128))
        pal = Image.new("RGB", (8, 8), (0, 0, 255)).convert("P")
        self.assertEqual(load_image(self.save(pal, "p.png")).rgb.getpixel((0, 0)), (0, 0, 255))
        g16 = Image.fromarray(np.array([[0, 65535]], dtype=np.uint16))
        out = load_image(self.save(g16, "g16.png")).rgb
        self.assertEqual(out.mode, "RGB")
        self.assertEqual(out.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(out.getpixel((1, 0)), (255, 255, 255))

    def test_corrupt_truncated_empty_missing_unsupported(self):
        bad = self.tmp / "garbage.png"
        bad.write_bytes(b"not an image at all" * 10)
        good = self.save(Image.new("RGB", (200, 200), (10, 200, 30)), "ok.jpg")
        trunc = self.tmp / "trunc.jpg"
        trunc.write_bytes(good.read_bytes()[: len(good.read_bytes()) // 2])
        empty = self.tmp / "empty.png"
        empty.write_bytes(b"")
        txt = self.tmp / "x.txt"
        txt.write_text("hi")
        for p in (bad, trunc, empty, txt, self.tmp / "missing.png"):
            with self.assertRaises(ImageLoadError, msg=str(p)):
                load_image(p)

    def test_iter_loaded_never_raises_and_keeps_order(self):
        ok = self.save(Image.new("RGB", (4, 4)), "1.png")
        bad = self.tmp / "2.png"
        bad.write_bytes(b"\x89PNG broken")
        recs = [ImageRecord("1", "B", ok), ImageRecord("2", "B", bad)]
        out = list(iter_loaded(recs))
        self.assertEqual([r.ad_id for r, _, _ in out], ["1", "2"])
        self.assertIsNotNone(out[0][1])
        self.assertIsNone(out[1][1])
        self.assertIn("unreadable", out[1][2])

    def test_original_file_unchanged(self):
        p = self.save(Image.new("RGBA", (50, 30), (1, 2, 3, 100)), "orig.png")
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        load_image(p).analysis_copy(10)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), before)

    def test_resize_and_pad_preserve_aspect(self):
        im = Image.new("RGB", (1200, 600))
        self.assertEqual(resize_max_side(im, 300).size, (300, 150))
        self.assertEqual(resize_max_side(im, 5000).size, (1200, 600))  # never upscales
        sq = pad_to_square(Image.new("RGB", (100, 40), (0, 0, 0)))
        self.assertEqual(sq.size, (100, 100))
        self.assertEqual(sq.getpixel((50, 0)), (255, 255, 255))
        self.assertEqual(sq.getpixel((50, 50)), (0, 0, 0))

    def test_records_from_dataset_status_filter(self):
        a = self.save(Image.new("RGB", (4, 4)), "a.png")
        csv_path = self.tmp / "d.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, ["ad_id", "brand", "local_image_path", "image_quality_status"])
            w.writeheader()
            w.writerow({"ad_id": "111", "brand": "X", "local_image_path": str(a), "image_quality_status": "PASS"})
            w.writerow({"ad_id": "222", "brand": "X", "local_image_path": str(a), "image_quality_status": "REPLACE"})
        recs = records_from_dataset(csv_path, self.tmp, "image_quality_status", ["PASS"])
        self.assertEqual([r.ad_id for r in recs], ["111"])
        self.assertEqual(len(records_from_dataset(csv_path, self.tmp)), 2)


class TestImageFeatures(unittest.TestCase):
    def test_dimensions_and_orientation(self):
        f = extract_image_properties(Image.new("RGB", (678, 1202), (200, 200, 200)))
        self.assertEqual((f["width"], f["height"]), (678, 1202))
        self.assertAlmostEqual(f["aspect_ratio"], 678 / 1202, places=4)
        self.assertEqual(f["orientation"], "portrait")
        self.assertEqual(orientation(1200, 1202), "square")      # within 5% tolerance
        self.assertEqual(orientation(1200, 628), "landscape")
        self.assertEqual(orientation(1080, 1350), "portrait")    # 4:5 feed ad

    def test_dominant_colours_recover_known_split(self):
        im = Image.new("RGB", (100, 100), (220, 20, 20))
        ImageDraw.Draw(im).rectangle([0, 70, 99, 99], fill=(20, 40, 200))  # bottom 30% blue
        cols = dominant_colours(im, k=3)
        self.assertEqual(cols[0]["hex"], "#dc1414")
        self.assertAlmostEqual(cols[0]["proportion"], 0.70, delta=0.02)
        self.assertAlmostEqual(cols[1]["proportion"], 0.30, delta=0.02)
        self.assertAlmostEqual(sum(c["proportion"] for c in cols), 1.0, places=3)
        self.assertEqual(cols, dominant_colours(im, k=3))  # deterministic

    def test_dominant_colours_single_colour_image(self):
        cols = dominant_colours(Image.new("RGB", (20, 20), (5, 6, 7)), k=5)
        self.assertEqual(len(cols), 1)
        self.assertEqual(cols[0]["proportion"], 1.0)

    def test_colour_distribution(self):
        d = colour_distribution(Image.new("RGB", (10, 10), (255, 255, 255)))
        self.assertEqual(d["white"], 1.0)
        g = colour_distribution(Image.new("RGB", (10, 10), (0, 200, 0)))
        self.assertEqual(g["green"], 1.0)
        self.assertAlmostEqual(sum(g.values()), 1.0, places=3)

    def test_brightness_contrast_sharpness(self):
        self.assertEqual(brightness_contrast(Image.new("RGB", (8, 8), (0, 0, 0)))["brightness"], 0.0)
        self.assertEqual(brightness_contrast(Image.new("RGB", (8, 8), (255, 255, 255)))["brightness"], 1.0)
        self.assertEqual(brightness_contrast(Image.new("RGB", (8, 8), (90, 90, 90)))["contrast"], 0.0)
        checker = Image.fromarray((np.indices((300, 300)).sum(0) // 10 % 2 * 255).astype("uint8")).convert("RGB")
        self.assertGreater(sharpness(checker), 10 * sharpness(checker.filter(ImageFilter.GaussianBlur(6))))

    @unittest.skipUnless(REAL_CREATIVE.exists(), "verified local creative not present")
    def test_real_creative(self):
        f = extract_image_properties(load_image(REAL_CREATIVE).rgb)
        self.assertEqual((f["width"], f["height"], f["orientation"]), (600, 600, "square"))
        self.assertGreater(f["sharpness"], 300)
        self.assertEqual(len(f["dominant_colours"]), 5)


class TestOcrFeatures(unittest.TestCase):
    def box(self, x0, y0, x1, y1, text="T", conf=0.9):
        return TextBox(text, conf, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]])

    def test_density_and_position_from_boxes(self):
        # 100x100 image; one 40x20 box in the top third, overlapping duplicate must not double count
        boxes = [self.box(0, 0, 40, 20, "SALE"), self.box(0, 0, 40, 20, "SALE")]
        f = text_features(boxes, 100, 100)
        self.assertAlmostEqual(f["text_density"], 0.08, delta=0.005)
        self.assertEqual(f["text_position"], "top")
        f = text_features([self.box(0, 80, 100, 100)], 100, 100)
        self.assertEqual(f["text_position"], "bottom")

    def test_low_confidence_counts_for_density_not_text(self):
        f = text_features([self.box(0, 40, 50, 60, "Hello", 0.95), self.box(50, 40, 100, 60, "#@!", 0.2)], 100, 100)
        self.assertEqual(f["ocr_text"], "Hello")
        self.assertEqual((f["ocr_n_text_regions"], f["ocr_n_readable_regions"]), (2, 1))
        self.assertAlmostEqual(f["text_density"], 0.20, delta=0.01)
        self.assertEqual(f["text_position"], "middle")

    def test_reading_order(self):
        f = text_features([self.box(60, 10, 90, 20, "world"), self.box(0, 10, 50, 20, "hello"),
                           self.box(0, 60, 50, 70, "next")], 100, 100)
        self.assertEqual(f["ocr_text"], "hello world next")

    def test_no_text(self):
        f = text_features([], 100, 100)
        self.assertEqual((f["ocr_text"], f["text_density"], f["text_position"]), ("", 0.0, "none"))

    @unittest.skipUnless(HAS_OCR, "rapidocr not installed")
    def test_ocr_reads_rendered_text(self):
        from src.vision.ocr_features import extract_ocr_features
        im = Image.new("RGB", (800, 600), "white")
        ImageDraw.Draw(im).text((60, 420), "FLAT 50% OFF", fill="black", font=ImageFont.load_default(size=80))
        f = extract_ocr_features(im)
        self.assertIn("50%", f["ocr_text"].replace(" ", ""))
        self.assertEqual(f["text_position"], "bottom")
        self.assertGreater(f["text_density"], 0.02)
        blank = extract_ocr_features(Image.new("RGB", (400, 400), "white"))
        self.assertEqual(blank["text_position"], "none")


class TestLayoutClassifier(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(classify_layout("FLAT 50% OFF only Rs 499 use code SAVE", 0.2)["layout_category"], "offer_heavy")
        self.assertEqual(classify_layout("“My skin glows now” - Priya ★★★★★", 0.1)["layout_category"], "testimonial")
        self.assertEqual(classify_layout("Helps digestion. Clinically proven formula with 500 mg", 0.2,
                                         6)["layout_category"], "educational")
        zs_life = {"packshot": .05, "product_closeup": .05, "person_using": .5, "people_scene": .3, "text_poster": .1}
        self.assertEqual(classify_layout("", 0.0, 0, zs_life)["layout_category"], "lifestyle")
        zs_prod = {"packshot": .6, "product_closeup": .2, "person_using": .1, "people_scene": .05, "text_poster": .05}
        self.assertEqual(classify_layout("Shilajit resin", 0.05, 2, zs_prod)["layout_category"], "product_focused")
        self.assertEqual(classify_layout("", None)["layout_category"], "unknown")

    def test_ocr_joined_words_and_pack_labels(self):
        # OCR merges words; offers must still be detected
        self.assertEqual(classify_layout("FROMREPSTO OFFERPRICE MRP--778 599", 0.1)["layout_category"], "offer_heavy")
        # small pack-label text ("30ml", "tested") on a packshot is not educational
        zs_prod = {"packshot": .9, "product_closeup": .09, "person_using": 0, "people_scene": 0, "text_poster": .01}
        r = classify_layout("Face serum 30ml dermatologically tested", 0.03, 11, zs_prod)
        self.assertEqual(r["layout_category"], "product_focused")
        # "off" must not fire inside other words
        self.assertNotIn("offer_words", classify_layout("coffee scoffed", 0.1)["layout_scores"]["offer_cues"])

    def test_reasons_are_reported(self):
        r = classify_layout("Rs 999 deal", 0.1)
        self.assertEqual(r["layout_category"], "offer_heavy")
        self.assertTrue(r["layout_reasons"] and "offer cues" in r["layout_reasons"][0])


class TestClipEmbeddings(unittest.TestCase):
    def test_shape_normalisation_and_determinism(self):
        clip = clip_or_skip(self)
        ims = [Image.new("RGB", (300, 500), (200, 30, 30)), Image.new("RGB", (640, 640), (30, 30, 200)),
               Image.new("L", (100, 100), 128)]
        e = clip.embed_images(ims)
        self.assertEqual(e.shape, (3, clip.dim))
        self.assertEqual(e.dtype, np.float32)
        np.testing.assert_allclose(np.linalg.norm(e, axis=1), 1.0, atol=1e-5)
        np.testing.assert_allclose(e, clip.embed_images(ims), atol=1e-5)  # same input -> same vectors
        self.assertEqual(clip.embed_images([]).shape, (0, clip.dim))

    @unittest.skipUnless(REAL_CREATIVE.exists(), "verified local creative not present")
    def test_semantic_sanity_on_real_creative(self):
        clip = clip_or_skip(self)
        e = clip.embed_images([load_image(REAL_CREATIVE).rgb])
        p = clip.zero_shot(e, ["an advertisement for a health supplement", "a photo of a car on a highway"])
        self.assertGreater(p[0, 0], p[0, 1])


class TestFeaturePipeline(TmpDirCase):
    def run_pipeline(self, use_clip):
        from src.vision.feature_pipeline import run
        a = self.save(Image.new("RGB", (300, 400), (240, 240, 240)), "a.png")
        b = self.save(Image.new("RGBA", (500, 500), (0, 120, 0, 255)), "b.png")
        bad = self.tmp / "c.png"
        bad.write_bytes(b"corrupt")
        recs = [ImageRecord("111", "BrandA", a), ImageRecord("222", "BrandB", bad), ImageRecord("333", "BrandB", b)]
        out_json, out_npy = self.tmp / "vf.json", self.tmp / "emb.npy"
        run(recs, out_json, out_npy, use_clip=use_clip, use_ocr=HAS_OCR, batch_size=2, device="cpu", verbose=False)
        return json.loads(out_json.read_text()), np.load(out_npy)

    def test_records_map_to_input_ids_and_failures_recorded(self):
        data, emb = self.run_pipeline(use_clip=False)
        recs = data["records"]
        self.assertEqual([(r["ad_id"], r["brand"]) for r in recs],
                         [("111", "BrandA"), ("222", "BrandB"), ("333", "BrandB")])
        self.assertEqual(recs[1]["extraction_status"], "failed")
        self.assertIn("unreadable", recs[1]["extraction_error"])
        self.assertIsNone(recs[1]["width"])
        self.assertEqual((recs[0]["width"], recs[0]["height"], recs[0]["orientation"]), (300, 400, "portrait"))
        self.assertEqual(recs[2]["orientation"], "square")
        # CLIP disabled -> no embeddings and no references, but extraction still succeeds
        self.assertEqual(emb.shape[0], 0)
        self.assertTrue(all(r["clip_embedding_reference"] is None for r in recs))
        required = {"ad_id", "brand", "image_path", "width", "height", "aspect_ratio", "orientation",
                    "dominant_colours", "brightness", "contrast", "sharpness", "clip_embedding_reference",
                    "ocr_text", "text_density", "text_position", "layout_category", "extraction_status",
                    "extraction_error"}
        for r in recs:
            self.assertTrue(required <= set(r), required - set(r))

    def test_embedding_rows_match_ad_ids(self):
        clip_or_skip(self)
        data, emb = self.run_pipeline(use_clip=True)
        recs = {r["ad_id"]: r for r in data["records"]}
        self.assertEqual(emb.shape, (2, data["meta"]["clip"]["embedding_dim"]))
        self.assertEqual(data["meta"]["clip"]["row_ad_ids"], ["111", "333"])
        self.assertEqual(recs["111"]["clip_embedding_reference"]["row"], 0)
        self.assertEqual(recs["333"]["clip_embedding_reference"]["row"], 1)
        self.assertIsNone(recs["222"]["clip_embedding_reference"])
        # stored row equals a fresh embedding of the same image
        fresh = _CLIP.embed_images([load_image(self.tmp / "b.png").rgb])[0]
        np.testing.assert_allclose(emb[1], fresh, atol=1e-5)


class TestEdgeCases(TmpDirCase):
    def test_cmyk_jpeg_and_exif_rotation(self):
        Image.new("CMYK", (50, 40), (0, 255, 255, 0)).save(self.tmp / "c.jpg")
        im = load_image(self.tmp / "c.jpg")
        self.assertEqual((im.source_mode, im.rgb.mode), ("CMYK", "RGB"))
        r, g, b = im.rgb.getpixel((5, 5))
        self.assertTrue(r > 200 and g < 60 and b < 60, (r, g, b))  # cyan=0, magenta+yellow=full -> red
        src = Image.new("RGB", (60, 20), (255, 0, 0))
        exif = src.getexif()
        exif[0x0112] = 6  # rotate 90° CW on display
        src.save(self.tmp / "r.jpg", exif=exif)
        self.assertEqual(load_image(self.tmp / "r.jpg").rgb.size, (20, 60))

    def test_float_image_rescaled(self):
        Image.fromarray(np.array([[0.0, 0.5], [1.0, 0.25]], dtype=np.float32), "F").save(self.tmp / "f.tif")
        rgb = load_image(self.tmp / "f.tif").rgb
        self.assertEqual(rgb.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(rgb.getpixel((0, 1)), (255, 255, 255))

    def test_pixel_limit_gives_clear_error(self):
        self.save(Image.new("RGB", (100, 100)), "big.png")
        old = Image.MAX_IMAGE_PIXELS
        try:
            Image.MAX_IMAGE_PIXELS = 1000
            with self.assertRaises(ImageLoadError) as cm:
                load_image(self.tmp / "big.png")
            self.assertIn("pixel safety limit", str(cm.exception))
        finally:
            Image.MAX_IMAGE_PIXELS = old

    def test_extreme_aspect_and_tiny_images_are_cheap_and_safe(self):
        import time
        t = time.time()
        self.assertEqual(sharpness(Image.new("RGB", (4, 4000), (9, 9, 9))), 0.0)
        self.assertLess(time.time() - t, 5.0)  # was ~40 s / 8 GB before the long-side cap
        for size in [(1, 1), (2, 2), (5, 5)]:
            f = extract_image_properties(Image.new("RGB", size, "white"))
            self.assertEqual((f["width"], f["height"], f["sharpness"]), (size[0], size[1], 0.0))


class TestSelection(TmpDirCase):
    def write_csv(self, rows):
        p = self.tmp / "ds.csv"
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, ["ad_id", "brand", "local_image_path", "final_status", "image_type"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return p

    def rows(self):
        img = self.save(Image.new("RGB", (40, 30), (200, 10, 10)), "x.png")
        def mk(i, st, ty, path=str(img)):
            return {"ad_id": i, "brand": "B", "local_image_path": path, "final_status": st, "image_type": ty}
        return [mk("1", "VERIFIED", "static"), mk("2", "REJECTED", "static"),
                mk("3", "VERIFIED", "video_thumbnail"), mk("4", "VERIFIED", "static", ""),
                mk("5", "UNVERIFIED", "video_thumbnail")]

    def test_parse_requirements(self):
        self.assertEqual(parse_requirements(["final_status=VERIFIED", "image_type=static, video_thumbnail"]),
                         {"final_status": ["VERIFIED"], "image_type": ["static", "video_thumbnail"]})
        self.assertEqual(parse_requirements(["a=x,y", "a=y,z"]), {"a": ["y"]})  # repeated column intersects
        for bad in ["final_status", "=x", "col="]:
            with self.assertRaises(ValueError):
                parse_requirements([bad])

    def test_multi_condition_filter_and_exclusion_counts(self):
        ds = self.write_csv(self.rows())
        recs, sel = select_from_dataset(ds, self.tmp, {"final_status": ["VERIFIED"], "image_type": ["static"]})
        self.assertEqual([r.ad_id for r in recs], ["1"])
        self.assertEqual(sel["n_rows"], 5)
        self.assertEqual(sel["n_selected"], 1)
        self.assertEqual(sel["n_excluded_by_condition"], {"final_status not in ['VERIFIED']": 2,
                                                          "image_type not in ['static']": 1,
                                                          "no image path": 1})
        self.assertEqual(sum(sel["n_excluded_by_condition"].values()), sel["n_rows"] - sel["n_selected"])
        self.assertEqual(len(sel["dataset_sha256"]), 64)
        # legacy status_column/allowed_statuses maps onto the same mechanism
        self.assertEqual([r.ad_id for r in records_from_dataset(ds, self.tmp, "final_status", ["VERIFIED"])],
                         ["1", "3"])

    def test_duplicate_ad_ids_rejected(self):
        rows = self.rows()
        rows[2]["ad_id"] = "1"
        ds = self.write_csv(rows)
        with self.assertRaises(DuplicateAdIdError):
            select_from_dataset(ds, self.tmp, {"final_status": ["VERIFIED"]})
        # a duplicate that is filtered out is fine
        recs, _ = select_from_dataset(ds, self.tmp, {"image_type": ["static"], "final_status": ["VERIFIED"]})
        self.assertEqual([r.ad_id for r in recs], ["1"])
        from src.vision.feature_pipeline import run
        r = ImageRecord("9", "B", self.tmp / "x.png")
        with self.assertRaises(DuplicateAdIdError):
            run([r, r], self.tmp / "o.json", self.tmp / "o.npy", use_clip=False, use_ocr=False, verbose=False)


class TestValidator(TmpDirCase):
    def make_run(self, use_clip):
        from src.vision.feature_pipeline import run
        rows = []
        for i, colour in enumerate([(200, 0, 0), (0, 200, 0), (0, 0, 200)]):
            p = self.save(Image.new("RGB", (64 + i, 64), colour), f"{i}.png")
            rows.append({"ad_id": str(100 + i), "brand": "B", "local_image_path": str(p),
                         "final_status": "VERIFIED" if i != 1 else "REJECTED"})
        ds = self.tmp / "ds.csv"
        with open(ds, "w", newline="") as f:
            w = csv.DictWriter(f, list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        recs, sel = select_from_dataset(ds, self.tmp, {"final_status": ["VERIFIED"]})
        out_json, out_npy = self.tmp / "vf.json", self.tmp / "emb.npy"
        run(recs, out_json, out_npy, use_clip=use_clip, use_ocr=False, device="cpu", verbose=False, selection=sel)
        return ds, out_json, out_npy

    def validate(self, ds, j, n):
        from src.vision.feature_pipeline import validate_outputs
        return validate_outputs(j, n, ds, base_dir=self.tmp)

    def test_good_run_passes_without_clip(self):
        ds, j, n = self.make_run(use_clip=False)
        res = self.validate(ds, j, n)
        self.assertTrue(res["ok"], res["errors"])
        self.assertEqual(res["n_records"], 2)
        meta = json.loads(j.read_text())["meta"]
        self.assertEqual(meta["selection"]["n_excluded_by_condition"], {"final_status not in ['VERIFIED']": 1})

    def test_validator_detects_order_leak_and_dataset_change(self):
        ds, j, n = self.make_run(use_clip=False)
        data = json.loads(j.read_text())
        data["records"].reverse()
        j.write_text(json.dumps(data))
        res = self.validate(ds, j, n)
        self.assertFalse(res["checks"]["order_matches_selected_dataset"])
        data["records"].append(dict(data["records"][0], ad_id="101"))  # excluded (REJECTED) row
        j.write_text(json.dumps(data))
        res = self.validate(ds, j, n)
        self.assertFalse(res["checks"]["no_excluded_rows_processed"])
        ds.write_text(ds.read_text() + "\n")
        self.assertFalse(self.validate(ds, j, n)["checks"]["dataset_unchanged_since_run"])

    def test_validator_detects_tampered_embeddings(self):
        clip_or_skip(self)
        ds, j, n = self.make_run(use_clip=True)
        self.assertTrue(self.validate(ds, j, n)["ok"])
        good = np.load(n)
        np.save(n, good * 2)  # breaks normalisation
        self.assertFalse(self.validate(ds, j, n)["checks"]["vectors_l2_normalised"])
        np.save(n, good[:1])  # row count mismatch
        self.assertFalse(self.validate(ds, j, n)["checks"]["npy_rows_match_references"])
        np.save(n, good)
        data = json.loads(j.read_text())
        data["meta"]["clip"]["row_ad_ids"].reverse()  # rows no longer match ad ids
        j.write_text(json.dumps(data))
        self.assertFalse(self.validate(ds, j, n)["checks"]["rows_match_meta_row_ad_ids"])

    def test_cli_validate_exit_codes(self):
        from src.vision.feature_pipeline import main
        ds, j, n = self.make_run(use_clip=False)
        with self.assertRaises(SystemExit) as cm:
            main(["--validate", "--out-json", str(j), "--out-npy", str(n)])
        self.assertEqual(cm.exception.code, 0)
        data = json.loads(j.read_text())
        data["records"].append(data["records"][0])
        j.write_text(json.dumps(data))
        with self.assertRaises(SystemExit) as cm:
            main(["--validate", "--out-json", str(j), "--out-npy", str(n)])
        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
