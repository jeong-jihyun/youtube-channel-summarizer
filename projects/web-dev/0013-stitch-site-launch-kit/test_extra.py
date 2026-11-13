"""대비비·결제 조건·페이지 지시문·체크리스트 추가 시험."""
import unittest
from site_kit import (api, contrast, design_md, page_prompts, payment_compare, redesign_prompt,
                      dev_prompts, SETUP, QA, PAGES_DEFAULT, _rgb)

PROVS = [
    {"name": "PayPal", "pct": 4.0, "fixed": 500, "setup": 0, "korea_direct": True, "region": "해외"},
    {"name": "Stripe", "pct": 3.5, "fixed": 300, "setup": 700000, "korea_direct": False, "region": "해외"},
    {"name": "토스", "pct": 3.0, "fixed": 0, "setup": 0, "korea_direct": True, "region": "한국"},
]


class Extra(unittest.TestCase):
    def test_contrast_known_values(self):
        self.assertAlmostEqual(contrast("#000000", "#ffffff"), 21.0, places=2)
        self.assertAlmostEqual(contrast("#ffffff", "#ffffff"), 1.0, places=2)
        self.assertIsNone(contrast("red", "#fff"))

    def test_rgb(self):
        self.assertEqual(_rgb("#ff2d78"), (255, 45, 120))
        self.assertIsNone(_rgb("#12"))

    def test_low_contrast_warns(self):
        _, w = design_md("a", "", "", "#facc15", "#ffffff", "#9ca3af", "", "")
        self.assertEqual(len(w), 2)

    def test_global_excludes_toss_and_charges_setup(self):
        ok, bad = payment_compare(19900, 30, PROVS, True)
        self.assertEqual([r["name"] for r in ok], ["PayPal", "Stripe"])
        self.assertEqual([r["name"] for r in bad], ["토스"])
        stripe = ok[1]
        self.assertAlmostEqual(stripe["month_eff"], stripe["month"] - 700000 / 12.0)
        self.assertIn("조건부", stripe["status"])

    def test_big_volume_flips_to_stripe(self):
        ok, _ = payment_compare(19900, 3000, PROVS, True)
        self.assertEqual(ok[0]["name"], "Stripe")

    def test_domestic_only_prefers_toss(self):
        ok, bad = payment_compare(19900, 30, PROVS, False)
        self.assertEqual(ok[0]["name"], "토스")
        self.assertEqual(bad, [])

    def test_page_prompts_count_and_consistency(self):
        t = page_prompts("B", "P", PAGES_DEFAULT)
        for pg in PAGES_DEFAULT:
            self.assertIn(pg, t)
        self.assertEqual(t.count("헤더·푸터·버튼 모양을 똑같이"), 4)
        self.assertIn("가상화폐 결제는 넣지 않는다", t)

    def test_checklists_cover_video_flow(self):
        times = [t for t, _, _ in SETUP]
        self.assertEqual(times[0], "2:25")
        self.assertEqual(times[-1], "26:08")
        self.assertTrue(any("가상화폐" in q for q in QA))

    def test_prompts(self):
        self.assertIn("Design.md", redesign_prompt(""))
        self.assertEqual(len(dev_prompts("x")), 5)
        self.assertIn("React", dev_prompts("x")[1])

    def test_api_errors(self):
        self.assertFalse(api({"primary": "red"})["ok"])
        self.assertFalse(api({"bg": "12"})["ok"])
        self.assertTrue(api({"price": "abc", "sales": ""})["ok"])


if __name__ == "__main__":
    unittest.main()
