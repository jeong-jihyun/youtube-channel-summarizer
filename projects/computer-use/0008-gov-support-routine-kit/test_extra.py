"""공고 판정·업력·서류·프롬프트 수준 추가 시험."""
import datetime
import unittest
from gov_kit import api, evaluate, parse_notices, years_since, build_prompt

T = datetime.date(2026, 11, 12)
PROF = {"today": T, "biz_type": "법인", "region": "인천", "industry": "AI", "founded": datetime.date(2025, 12, 15),
        "years": years_since(datetime.date(2025, 12, 15), T), "want": ["사무", "인건비"],
        "sources": ["정부24"], "age": 40}


def one(line, prof=PROF):
    items, bad = parse_notices(line)
    assert items and not bad, bad
    return evaluate(items[0], prof)


class Extra(unittest.TestCase):
    def test_years(self):
        self.assertAlmostEqual(years_since(datetime.date(2025, 11, 12), T), 1.0, places=1)

    def test_expired(self):
        self.assertEqual(one("a|사무|2026-11-11|7|전국|100|전체")["verdict"], "제외")

    def test_deadline_today_ok(self):
        r = one("a|사무|2026-11-12|7|전국|100|전체")
        self.assertEqual(r["dday"], 0)
        self.assertNotEqual(r["verdict"], "제외")
        self.assertTrue(any("임박" in f for f in r["flags"]))

    def test_years_over_limit(self):
        p = dict(PROF, years=8.0)
        self.assertEqual(one("a|사무|2027-01-01|7|전국|100|전체", p)["verdict"], "제외")

    def test_region_and_target(self):
        self.assertEqual(one("a|사무|2027-01-01|7|부산|100|전체")["verdict"], "제외")
        self.assertEqual(one("a|사무|2027-01-01|7|전국|100|예비")["verdict"], "제외")
        self.assertEqual(one("a|사무|2027-01-01|7|인천|100|법인")["verdict"], "후보")

    def test_unknown_years_hold(self):
        r = one("a|사무|2027-01-01|없음|전국|100|전체")
        self.assertEqual(r["verdict"], "보류")

    def test_wrong_kind_hold(self):
        self.assertEqual(one("a|대출|2027-01-01|7|인천|100|전체")["verdict"], "보류")

    def test_prospective_ignores_years(self):
        p = dict(PROF, biz_type="예비", years=0.0)
        self.assertEqual(one("a|사무|2027-01-01|0|전국|100|예비", p)["verdict"], "후보")

    def test_bad_lines_reported(self):
        r = api({"region": "인천", "notices": "제목만\na|사무|날짜아님|7|전국|100|전체"})
        self.assertTrue(r["ok"])
        self.assertIn("읽지 못한 줄", r["text"])

    def test_levels(self):
        r_min = api({"level": "최소", "region": "인천", "age": "40"})["text"]
        r_det = api({"level": "상세", "region": "인천", "age": "40"})["text"]
        self.assertNotIn("인천 /", r_min.split("[2]")[0])
        self.assertIn("40세", r_det)
        self.assertNotIn("40세", api({"level": "보통", "age": "40"})["text"])

    def test_docs_ready(self):
        r = api({"docs_ready": "사업자등록증,국세 완납증명"})
        self.assertEqual(r["missing_docs"], 3)

    def test_non_corporation_registry_note(self):
        t = api({"biz_type": "개인", "founded": "2016-05-01"})["text"]
        self.assertIn("해당 여부 확인", t)

    def test_input_errors(self):
        self.assertFalse(api({"biz_type": "x"})["ok"])
        self.assertFalse(api({"founded": "2030-01-01"})["ok"])
        self.assertFalse(api({"want": "없음"})["ok"])
        self.assertFalse(api({"biz_type": "법인", "founded": "없음"})["ok"])
        self.assertTrue(api({"biz_type": "예비", "founded": "없음"})["ok"])

    def test_routine_duplicate(self):
        t = api({"routines": "10:00|a\n10:00|b"})["text"]
        self.assertIn("겹침", t)


if __name__ == "__main__":
    unittest.main()
