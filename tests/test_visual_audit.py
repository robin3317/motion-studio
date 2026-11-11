#!/usr/bin/env python3
"""Tests for skills/motion-studio/scripts/visual_audit.py that need no browser (stdlib only).

    python tests/test_visual_audit.py

They feed made-up measurements to the rules and check what gets flagged, and check that the
measuring script is added to a COPY of a composition, never to the original.
The full path through HyperFrames is covered by tests/regression.py.
"""
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(REPO, "skills", "motion-studio", "scripts"))
import visual_audit as va  # noqa: E402


def comp(**kw):
    """A well-made pill: 200x80 at (100,100), one line, text centred. Override fields to break it."""
    c = {"k": "c", "t": 2.0, "sel": "span.pill", "cls": "pill", "txt": "Get started", "x": 100, "y": 100, "w": 200,
         "h": 80, "op": 1, "sw": 200, "cw": 200, "sh": 80, "ch": 80, "br": 999, "bw": 0, "fs": 32, "kids": 0,
         "words": 2, "box": 1, "lines": 1, "tx": 130, "ty": 120, "tw": 140, "th": 40, "ink": 140}
    c.update(kw)
    return c


def codes(records):
    return sorted(f["code"] for f in va.judge(records, (1920, 1080)))


class Rules(unittest.TestCase):
    def test_good_pill_is_clean(self):
        self.assertEqual(codes([comp()]), [])

    def test_wrapped_label(self):
        self.assertEqual(codes([comp(lines=2)]), ["label_wrapped"])
        self.assertEqual(codes([comp(lines=3, words=12, txt="a long paragraph of body text inside a card")]), [])

    def test_text_low_in_box(self):
        found = va.judge([comp(ink=150)], (1920, 1080))      # 10 px low in an 80 px box = 12.5%
        self.assertEqual([(f["code"], f["severity"]) for f in found], [("text_off_centre_vertical", "warning")])
        found = va.judge([comp(ink=146)], (1920, 1080))      # 6 px = 7.5%
        self.assertEqual([f["severity"] for f in found], ["review"])
        self.assertEqual(codes([comp(ink=141.5)]), [])       # within tolerance

    def test_lopsided_and_tight_padding(self):
        self.assertIn("text_off_centre_horizontal", codes([comp(tx=170, tw=120)]))
        self.assertIn("tight_padding", codes([comp(tx=104, tw=192)]))

    def test_overflow_and_frame_edge(self):
        self.assertEqual(codes([comp(sw=240)]), ["text_overflow"])
        self.assertEqual(codes([comp(x=1800, tx=1830)]), ["cut_by_frame"])

    def test_half_faded_components_are_not_judged(self):
        self.assertEqual(codes([comp(lines=2, op=0.5)]), [])

    def test_same_class_different_sizes(self):
        self.assertEqual(codes([comp(), comp(txt="Other", h=96, sh=96, ch=96, ink=148)]), ["inconsistent_class"])
        self.assertEqual(codes([comp(), comp(txt="Other", w=260, tw=200)]), [])   # width may differ

    def test_text_over_3d(self):
        o = {"k": "o", "t": 3.0, "sel": "#tagline", "txt": "Tagline", "x": 0, "y": 0, "w": 300, "h": 40}
        self.assertEqual([f["severity"] for f in va.judge([dict(o, cover=43)], (1080, 1920))], ["warning"])
        self.assertEqual([f["severity"] for f in va.judge([dict(o, cover=18)], (1080, 1920))], ["review"])


class ProbeCopy(unittest.TestCase):
    def test_original_is_untouched_and_copy_is_cleaned_up(self):
        tmp = tempfile.mkdtemp(prefix="ms-audit-test-")
        try:
            src = os.path.join(tmp, "composition")
            os.makedirs(os.path.join(src, "node_modules", "gsap"))
            os.makedirs(os.path.join(src, "renders"))
            with open(os.path.join(src, "node_modules", "gsap", "x.js"), "w") as f:
                f.write("//lib")
            html = "<html><body><div id='root'></div></BODY></html>"
            with open(os.path.join(src, "index.html"), "w") as f:
                f.write(html)
            work, cleanup = va.probe_copy(src, [1.5, 3.0], [".pill"])
            with open(os.path.join(work, "index.html")) as f:
                probed = f.read()
            self.assertIn("MSAUDIT", probed)
            self.assertIn('"times": [1.5, 3.0]', probed)
            self.assertLess(probed.index("MSAUDIT"), probed.lower().rindex("</body>"))
            self.assertTrue(os.path.isfile(os.path.join(work, "node_modules", "gsap", "x.js")))
            self.assertFalse(os.path.exists(os.path.join(work, "renders")))
            cleanup()
            self.assertFalse(os.path.exists(work))
            with open(os.path.join(src, "index.html")) as f:
                self.assertEqual(f.read(), html)
            self.assertTrue(os.path.isfile(os.path.join(src, "node_modules", "gsap", "x.js")), "the library folder must survive")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
