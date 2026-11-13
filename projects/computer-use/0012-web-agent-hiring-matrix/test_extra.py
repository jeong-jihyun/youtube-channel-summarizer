"""에이전트 순위·불가 조건·루틴 겹침·손익분기 추가 시험."""
import unittest
from hiring_matrix import api, score_agents, routine_table, breakeven, ig_prompt, handoff_rules, _yn


class Extra(unittest.TestCase):
    def test_app_need_leaves_only_computer_use(self):
        self.assertEqual(api({"need_app": "Y"})["ranking"], ["컴퓨터 유즈"])

    def test_phone_only_cloud_agents(self):
        r = api({"phone_only": "Y"})["ranking"]
        self.assertEqual(len(r), 2)
        self.assertTrue(all(x.startswith(("뮤즈", "피클")) for x in r))

    def test_login_sensitive_demotes_cloud(self):
        res = score_agents(False, False, True, False, False, True, "무료", False)
        self.assertLess(res["muse"][1], res["chrome_ext"][1])

    def test_multi_model_dev_prefers_egolite(self):
        r = api({"multi_model": "Y", "is_dev": "Y", "pc_spec": "높음", "login_sensitive": "Y"})
        self.assertTrue(r["ranking"][0].startswith("에고라이트"))

    def test_low_pc_penalizes_heavy(self):
        hi = score_agents(False, False, False, True, False, True, "무료", False)["aside"][1]
        lo = score_agents(False, False, False, True, False, False, "무료", False)["aside"][1]
        self.assertEqual(hi - lo, 20)

    def test_routine_clash_and_bad(self):
        rows, clash, bad = routine_table("9:00|a\n09:00|b\n8:30|c\n99:00|x\nabc")
        self.assertEqual([t for t, _ in rows], ["08:30", "09:00", "09:00"])
        self.assertIn("09:00", clash)
        self.assertEqual(len(bad), 2)

    def test_breakeven(self):
        m, net = breakeven(10_000_000, 300_000, 2_500_000)
        self.assertAlmostEqual(m, 10_000_000 / 2_200_000)
        self.assertEqual(breakeven(1, 5, 3)[0], None)

    def test_ig_gaps(self):
        _, gaps = ig_prompt("", "", "", "", "")
        self.assertEqual(len(gaps), 3)

    def test_handoff_default_agents(self):
        t = handoff_rules([], "x.txt")
        self.assertIn("x.txt", t)
        self.assertIn("Claude", t)

    def test_bad_inputs(self):
        self.assertFalse(api({"pc_spec": "??"})["ok"])
        self.assertFalse(api({"budget": "??"})["ok"])
        self.assertTrue(api({"machine_won": "abc"})["ok"])

    def test_yn(self):
        self.assertTrue(_yn("예"))
        self.assertFalse(_yn("모름"))


if __name__ == "__main__":
    unittest.main()
