"""지시문 빠진 칸·겹침·모델 비용 계산 추가 시험."""
import unittest
from routine_planner import api, build_instruction, check_conflicts, model_options, _hhmm, EFFORT


def A(**k):
    base = {"name": "Brown", "goal": "글쓰기", "when": "매일 8시", "where": ["구글", "블로그"],
            "steps": ["구글에서 뉴스를 찾는다", "사실 확인 후 블로그에 쓴다"], "promo": "", "mode": "초안",
            "subs": [], "runs": 30, "tokens": 100000, "price": 5.0, "krw": 1400, "effort": "중간", "local_ok": False}
    base.update(k)
    return base


class Extra(unittest.TestCase):
    def test_hhmm(self):
        self.assertEqual(_hhmm("08:30"), 510)
        self.assertEqual(_hhmm("8:05"), 485)
        self.assertIsNone(_hhmm("25:00"))
        self.assertIsNone(_hhmm("abc"))

    def test_complete_has_no_gaps(self):
        _, gaps = build_instruction(A())
        self.assertEqual(gaps, [])

    def test_gaps_found(self):
        _, gaps = build_instruction(A(name="", goal="", when="", where=[], steps=[]))
        text = " ".join(gaps)
        for w in ("누가", "왜", "언제", "어디서", "어떻게"):
            self.assertIn(w, text)

    def test_no_fact_check_warning(self):
        _, gaps = build_instruction(A(steps=["구글에서 뉴스를 찾는다", "블로그에 쓴다"], goal="뉴스 글"))
        self.assertTrue(any("사실 확인" in g for g in gaps))

    def test_where_not_in_steps(self):
        _, gaps = build_instruction(A(where=["유튜브", "블로그"], steps=["뉴스를 찾는다", "사실 확인하고 블로그에 쓴다"]))
        self.assertTrue(any("유튜브" in g for g in gaps))

    def test_mode_text(self):
        ins, _ = build_instruction(A(mode="초안"))
        self.assertIn("초안", ins[-1])
        ins, _ = build_instruction(A(mode="자동"))
        self.assertIn("자동 발행", ins[-1])

    def test_conflict_same_time_target(self):
        ex = [{"time": 480, "name": "x", "target": "블로그"}]
        self.assertTrue(check_conflicts({"time": 480, "target": "블로그"}, ex))
        self.assertTrue(any("분 간격" in c for c in check_conflicts({"time": 510, "target": "블로그"}, ex)))
        self.assertEqual(check_conflicts({"time": 700, "target": "블로그"}, ex), [])
        self.assertTrue(any("다른 루틴" in c for c in check_conflicts({"time": 480, "target": "다른곳"}, ex)))

    def test_api_cost_math(self):
        # 30회 x 100000토큰 x 5달러/백만 = 15달러, 환율 1400 -> 21000원
        opts, rec, usd = model_options(A())
        self.assertAlmostEqual(usd, 15.0)
        self.assertTrue(any("21,000원" in o for o in opts))
        self.assertIn("API", rec)

    def test_effort_multiplier(self):
        _, _, usd = model_options(A(effort="최대"))
        self.assertAlmostEqual(usd, 15.0 * EFFORT["최대"])
        _, rec, _ = model_options(A(effort="최대"))
        self.assertIn("20달러", rec)

    def test_gemini_not_synced(self):
        opts, rec, _ = model_options(A(subs=["gemini"]))
        self.assertTrue(any("Gemini" in o and "API" in o for o in opts))
        self.assertNotIn("구독 연결", rec)

    def test_supported_sub_recommended(self):
        _, rec, _ = model_options(A(subs=["chatgpt", "gemini"]))
        self.assertIn("ChatGPT", rec)

    def test_input_errors(self):
        self.assertFalse(api({"effort": "x"})["ok"])
        self.assertFalse(api({"mode": "x"})["ok"])
        self.assertFalse(api({"run_time": "99:99"})["ok"])

    def test_default_run_ok(self):
        r = api({})
        self.assertTrue(r["ok"])
        self.assertTrue(r["conflicts"])


if __name__ == "__main__":
    unittest.main()
