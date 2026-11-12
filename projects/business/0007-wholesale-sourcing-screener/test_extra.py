"""순마진·유통기한·시나리오 추가 시험."""
import datetime
import unittest
from screener import api, parse_items, evaluate

_CFG = {"fee": 0.1, "ship": 3000, "pack": 500, "return_rate": 0, "return_loss": 0, "target": 0.2,
       "min_months": 6, "min_price": 10000, "today": datetime.date(2026, 11, 12)}


def one(line, cfg=_CFG):
    items, _ = parse_items(line)
    return evaluate(items[0], cfg)


class Extra(unittest.TestCase):
    def test_net_math(self):
        r = one("a,1000,3,10000,없음,N")  # 10000 - 1000(수수료) - 3000(매입) - 3000 - 500 = 2500
        self.assertAlmostEqual(r["net"], 2500)
        self.assertAlmostEqual(r["net_rate"], 0.25)
        self.assertEqual(r["verdict"], "후보")

    def test_expired_excluded(self):
        self.assertEqual(one("a,1000,1,30000,2026-10-01,Y")["verdict"], "제외")

    def test_short_expiry_hold(self):
        r = one("a,1000,1,30000,2027-01-10,Y")
        self.assertEqual(r["verdict"], "보류")
        self.assertTrue(any("유통기한" in f for f in r["flags"]))

    def test_loss_excluded(self):
        self.assertEqual(one("a,9000,1,12000,없음,N")["verdict"], "제외")

    def test_low_margin_hold(self):
        # 순이익 = 20000 - 2000 - 14000 - 3500 = 500 -> 2.5% < 20% 이면 보류
        self.assertEqual(one("a,14000,1,20000,없음,N")["verdict"], "보류")

    def test_bundle_beats_single(self):
        r = one("a,1000,3,10000,없음,N")
        self.assertGreater(r["net"], r["single_net"])

    def test_returns_reduce_net(self):
        c = dict(_CFG, return_rate=0.1, return_loss=0.5)
        self.assertLess(one("a,1000,3,10000,없음,N", c)["net"], one("a,1000,3,10000,없음,N")["net"])

    def test_scenario_and_stock_cash(self):
        r = api({"items": "a,1000,3,10000,없음,N", "monthly_sales": "10000000", "stock_months": "2"})
        s = r["summary"]
        self.assertAlmostEqual(s["monthly_net"], 10000000 * s["avg_net_rate"])
        self.assertAlmostEqual(s["stock_cash"], (10000000 / 10000) * 3000 * 2)

    def test_bad_input(self):
        self.assertFalse(api({"items": "깨진줄"})["ok"])
        self.assertFalse(api({"today": "어제"})["ok"])
        r = api({"items": "a,1000,1,30000,없음,Y\n깨진줄"})
        self.assertTrue(r["ok"])
        self.assertIn("읽지 못한 줄", r["text"])

    def test_no_candidates(self):
        r = api({"items": "a,9000,1,12000,없음,N"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["summary"]["candidates"], 0)
