import shorts


def t(c, m):
    assert c, m


r = shorts.api({})
t(r["ok"] and r["fits"], "예시는 60초 이내")
t(25 < r["seconds"] < 40, "예시 추정 초 %s" % r["seconds"])
t(shorts.keyword("업체를 예약했다. 업체가 왔다. 업체에 연락") == "업체", "조사 제거 키워드")
# 배속이 높을수록 짧다
t(shorts.api({"speed": "2"})["seconds"] < shorts.api({"speed": "1"})["seconds"], "배속")
# 쉼이 길수록 길다
t(shorts.api({"pause_sec": "1"})["seconds"] > shorts.api({"pause_sec": "0"})["seconds"], "쉼")
# 길이 초과 안내
long_story = " ".join(["이것은 길이를 늘리기 위한 문장입니다."] * 40)
x = shorts.api({"story": long_story})
t(not x["fits"] and "초과" in x["text"], "초과 안내")
# 장면 수
t(shorts.split_scenes(shorts.sentences(long_story), 13).__len__() == 13, "장면 13개")
t(shorts.api({"story": "한 문장뿐입니다."})["scenes"] == 1, "문장 하나면 장면 하나")
# 개인정보
y = shorts.api({"story": "연락은 010-1234-5678 로 주세요. 메일은 a.b@test.co.kr 입니다."})
t(len(y["flags"]) == 2, "전화·이메일 발견 %s" % y["flags"])
t(shorts.api({"story": "서울시 강남구 테헤란로 12 에서 만났다."})["flags"], "주소 형태")
# 유사도: 그대로 베끼면 경고, 다르게 쓰면 통과
s1 = shorts.SAMPLE
same = shorts.api({"story": s1, "script": s1})
t(same["same_ratio"] == 1.0 and "더 바꿀 것" in same["text"], "그대로 복사 경고")
diff = shorts.api({"story": s1, "script": "후기 좋은 청소 업체에 맡겼는데 결과가 아쉬웠다. 창틀 때와 테이프가 남아 있었고 업체 반응이 불쾌했다. 그래서 다시 쓰지 않기로 했다."})
t(diff["same_ratio"] < 0.3 and "충분히 다름" in diff["text"], "다른 대본")
# 수익: 100편 x 30 x 10000 x 160/1000
z = shorts.api({"uploads_per_day": "10", "avg_views": "10000", "rpm_won": "100"})
t(abs(z["month_revenue"] - 10 * 30 * 10000 / 1000 * 100) < 1, "수익 계산")
t(abs(r["ref_rpm"] - 161.9) < 0.5, "영상 환산 RPM")
t("RPM 167원" in r["text"], "영상 주장 요구 RPM")
t(shorts.api({"story": "", "speed": "abc"})["ok"], "잘못된 입력은 기본값")
t(not shorts.api({"story": "   ", "script": " "}).get("ok") is False, "공백만이어도 예시 사용")
print("성공 추가시험 17개")
