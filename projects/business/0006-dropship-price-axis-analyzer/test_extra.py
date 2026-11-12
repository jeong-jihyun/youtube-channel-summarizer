"""영상 속 숫자와 4축 분석 추가 시험."""
import unittest
from dropship import api, parse_sales, analyze_axis, ceil100


class Extra(unittest.TestCase):
    def test_video_price_21man(self):
        r = api({"cost": "100", "rate": "1500", "multiplier": "1.4"})
        self.assertEqual(r["price"]["price_multiplier"], 210000)

    def test_reverse_price_meets_margin(self):
        r = api({"cost": "10000", "rate": "1", "fee_pct": "10", "margin_pct": "20"})
        p = r["price"]["price_reverse"]
        net = p * 0.9 - 10000
        self.assertGreaterEqual(net / p, 0.2 - 1e-9)

    def test_impossible_margin(self):
        r = api({"fee_pct": "60", "margin_pct": "50"})
        self.assertTrue(r["ok"])
        self.assertIn("역산 불가", r["text"])

    def test_shipping_lowers_net(self):
        a = api({"shipping": "0"})["price"]["net_multiplier"]
        b = api({"shipping": "5000"})["price"]["net_multiplier"]
        self.assertAlmostEqual(a - b, 5000)

    def test_time_math(self):
        r = api({"count": "10000", "manual_min": "10", "auto_sec": "10"})
        self.assertAlmostEqual(r["time"]["manual_hours"], 100000 / 60.0)

    def test_brand_axis_is_best_in_default(self):
        self.assertEqual(api({})["analysis"]["best_axis"], "brand")

    def test_season_axis_wins_when_only_season_matters(self):
        rows = []
        for i in range(6):
            rows.append("여름%d,브랜드%d,카테고리%d,키워드%d,여름,10" % (i, i, i % 3, i))
        for i in range(6):
            rows.append("겨울%d,브랜드%d,카테고리%d,키워드%d,겨울,1" % (i, i + 10, i % 3, i + 10))
        self.assertEqual(api({"sales": "\n".join(rows)})["analysis"]["best_axis"], "season")

    def test_too_few_rows(self):
        r = api({"sales": "a,b,c,d,e,1"})
        self.assertTrue(r["ok"])
        self.assertIn("6개 미만", r["text"])

    def test_bad_lines_counted(self):
        rows, bad = parse_sales("a,b,c,d,e,1\n깨진줄\nx,y,z,k,s,숫자")
        self.assertEqual((len(rows), bad), (1, 2))

    def test_ceil100(self):
        self.assertEqual(ceil100(205501), 205600)
