import agency


def t(cond, msg):
    assert cond, msg


r = agency.api({})
t(r["ok"], "기본 실행")
q = r["quote"]
t(q["videos"] == 24 and abs(q["per_video"] - 275000) < 1, "건당 단가 660만/24")
t("600만원" in r["text"], "660만원 계산 불일치 경고")
# 외주비 0이면 순수익률이 외주 있을 때보다 높다
a = agency.api({"outsource_per_video": "0"})["quote"]["margin_pct"]
b = agency.api({"outsource_per_video": "100000"})["quote"]["margin_pct"]
t(a > b, "외주비가 클수록 순수익률 하락")
# 외주비 3만원: 총이익률은 (6,600,000-720,000)/6,600,000 근처
t(80 < r["quote"]["margin_pct"] < 90, "순수익률 범위 %s" % r["quote"]["margin_pct"])
# 월 4천 점검: 고객 13곳으로는 부족
t("설명되지 않는다" in r["text"], "월 4천 불일치 경고")
# 시간: 13곳 x 8건 x 20분 / 60 / 30 = 1.156
t(abs(q["hours_per_day"] - 13 * 8 * 20 / 60 / 30) < 0.01, "하루 시간")
t("하루 약 1시간이라 했지만" in agency.api({"my_minutes_per_video": "60"})["text"], "시간 경고")
# 금지어 점검
x = agency.api({"forbidden": "스케일링"})["brief"]
t(len(x["bad_titles"]) == 5, "금지어가 제목에 포함되면 모두 잡힘")
t(agency.api({})["brief"]["bad_titles"] == [], "기본은 없음")
t("의료 업종" in agency.api({})["text"], "치과 주의 문구")
t("의료 업종" not in agency.api({"industry": "카페"})["text"], "카페는 의료 문구 없음")
t(len(agency.api({"weeks": "2", "per_week": "2"})["brief"]["dates"]) == 4, "일정 개수")
t("AI 영상" not in agency.api({"ai_video": "N"})["text"], "AI 방식 끄기")
t(agency.api({"videos_per_month": "abc", "months": "x"})["ok"], "잘못된 숫자는 기본값")
print("성공 추가시험 14개")
