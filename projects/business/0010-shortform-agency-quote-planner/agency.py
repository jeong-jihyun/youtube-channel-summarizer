"""숏폼 대행 견적·기획서 도구 (영상 t3-xEAagHDs, money_touch).

영상의 핵심은 두 가지다.
  1) 선입금 패키지(월 8건 x 3개월 등)를 받고 편집은 외주로 돌려 순수익 60~70%를 남기는 구조
  2) 고객에게 보내는 기획서(제목·스토리보드·촬영 가이드·대본·캡션)를 AI로 빨리 만드는 절차
이 도구는 (1) 견적·순수익·시간·'영상 속 주장 점검'을, (2) 기획서 뼈대·ChatGPT 요청 문구·
AI 시작/끝 이미지 프롬프트·업로드 일정을 만든다. 기획서 문장은 규칙 기반 뼈대이며
사람이 업종 사실로 채워야 한다. 모든 금액·시간은 가정 입력이다. 표준 라이브러리만 사용."""
import datetime
import sys


def _num(v, default, lo=None):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return default
    if lo is not None and x < lo:
        return default
    return x


def won(x):
    return "{:,}원".format(int(round(x)))


def quote(p):
    n = int(_num(p.get("videos_per_month"), 8, 1))
    months = int(_num(p.get("months"), 3, 1))
    total = _num(p.get("package_total"), 6600000, 1)
    out_cost = _num(p.get("outsource_per_video"), 30000, 0)
    minutes = _num(p.get("my_minutes_per_video"), 20, 1)
    clients = int(_num(p.get("clients"), 13, 1))
    tools = _num(p.get("tool_cost_month"), 100000, 0)
    claim_net = _num(p.get("claim_net_month"), 40000000, 0)
    claim_margin = _num(p.get("claim_margin_pct"), 65, 1) / 100.0
    videos = n * months
    per_video = total / videos
    out_total = out_cost * videos
    gross = total - out_total
    month_rev = total / months
    month_net = month_rev - out_cost * n - tools / max(clients, 1)
    margin = (total - out_total - tools / max(clients, 1) * months) / total * 100
    hours = n * minutes / 60.0
    hourly = month_net / hours if hours else 0
    # 전 고객 합계
    all_rev = month_rev * clients
    all_net = all_rev - out_cost * n * clients - tools
    all_hours_day = n * minutes * clients / 60.0 / 30.0
    res = {"videos": videos, "per_video": per_video, "month_net_per_client": month_net,
           "margin_pct": margin, "all_net": all_net, "hours_per_day": all_hours_day}
    L = ["[견적·순수익 계산] (모든 값은 입력한 가정)",
         "패키지: 월 %d건 x %d개월 = %d건, 총 %s -> 영상 1건당 %s" % (n, months, videos, won(total), won(per_video)),
         "외주 편집비(건당 %s) 합계 %s -> 외주 뺀 총이익 %s" % (won(out_cost), won(out_total), won(gross)),
         "고객 1곳 월 순이익 %s (월 매출 %s, 외주·툴비 배분 반영), 순수익률 약 %.0f%%" % (won(month_net), won(month_rev), margin),
         "내가 쓰는 시간: 고객 1곳 월 %.1f시간 -> 시간당 %s" % (hours, won(hourly)),
         "고객 %d곳 전체: 월 매출 %s, 월 순이익 %s, 하루 작업 %.1f시간(기획·검수·전달만)" % (clients, won(all_rev), won(all_net), all_hours_day)]
    L.append("")
    L.append("[영상 주장 점검]")
    if n * months and abs(total - 6600000) < 1 and months == 3:
        L.append("- 영상은 '월 8건, 200만원씩 3개월 = 660만원'이라 했는데 200만원 x 3 = 600만원이다. 월 220만원이면 660만원이 맞다. 계약서 금액은 반드시 직접 계산하라.")
    need_rev = claim_net / claim_margin
    need_clients = need_rev / month_rev if month_rev else 0
    L.append("- 월 순수익 목표 %s을 순수익률 %.0f%%로 내려면 월 매출 약 %s이 필요하고, 이 패키지(월 %s) 기준 고객 약 %.0f곳이다. 영상이 말한 고객은 %d곳이다%s." % (
        won(claim_net), claim_margin * 100, won(need_rev), won(month_rev), need_clients, clients,
        " -> 영상 숫자만으로는 월 4천이 설명되지 않는다(건당 단가가 더 높거나 고객이 더 많거나 일회성 수입이 섞였을 수 있음)" if need_clients > clients * 1.3 else ""))
    if all_hours_day > 1.5:
        L.append("- 영상은 하루 약 1시간이라 했지만 입력한 시간(건당 %.0f분)으로는 하루 %.1f시간이다. 건당 시간이나 고객 수를 다시 보라." % (minutes, all_hours_day))
    else:
        L.append("- 하루 작업 %.1f시간은 영상의 '하루 1시간 안팎' 주장과 비슷한 수준이다(건당 시간이 짧다는 가정)." % all_hours_day)
    if margin < 50:
        L.append("- 순수익률 %.0f%%는 영상이 말한 60~70%%보다 낮다. 외주비를 건당 얼마로 주느냐가 가장 큰 변수다." % margin)
    L.append("- 외주비를 올리면: 건당 %s -> %s일 때 순수익률은 %.0f%%." % (
        won(out_cost), won(out_cost * 1.5),
        (total - out_cost * 1.5 * videos - tools / max(clients, 1) * months) / total * 100))
    return res, "\n".join(L)


HOOKS = ["{topic}, 모르면 손해 보는 3가지", "{industry} 사장님들이 {topic}에서 놓치는 것", "{topic} 하기 전에 이것부터 보세요",
         "{topic}, 숫자로 보면 이렇습니다", "'{topic}' 질문, 답은 의외로 간단합니다"]


def brief(p):
    industry = (p.get("industry") or "치과").strip()
    topic = (p.get("topic") or "스케일링 주기").strip()
    trend = (p.get("trend") or "질문하고 바로 답하는 형식").strip()
    dur = int(_num(p.get("duration_sec"), 30, 10))
    forbid = [w.strip() for w in (p.get("forbidden") or "최고,100%,완치").split(",") if w.strip()]
    ai = str(p.get("ai_video", "Y")).upper().startswith("Y")
    weeks = int(_num(p.get("weeks"), 4, 1))
    per_week = int(_num(p.get("per_week"), 2, 1))
    start = p.get("start_date") or "2026-11-16"
    try:
        d0 = datetime.date.fromisoformat(start)
    except ValueError:
        d0 = datetime.date(2026, 11, 16)
    titles = [h.format(topic=topic, industry=industry) for h in HOOKS]
    bad_titles = [t for t in titles if any(w in t for w in forbid)]
    t1, t2, t3, t4 = [round(dur * x) for x in (0.1, 0.35, 0.8, 1.0)]
    L = ["[고객용 기획서 뼈대] 업종: %s / 주제: %s / 길이 %d초 / 참고 트렌드: %s" % (industry, topic, dur, trend),
         "제목 후보(경험칙 틀 5종, 사람이 다듬을 것):"]
    L += ["  %d) %s" % (i + 1, t) for i, t in enumerate(titles)]
    L.append("스토리보드(길이 %d초 기준 비율):" % dur)
    L += ["  0~%d초 훅: 질문 한 줄 + 가장 움직임 큰 컷 (영상 조언: 초반 3초가 중요)" % t1,
          "  %d~%d초 문제 제시: %s에서 사람들이 겪는 상황 1개" % (t1, t2, industry),
          "  %d~%d초 해결·근거: %s에 대한 핵심 답 1~2개 (수치·출처는 고객에게 확인)" % (t2, t3, topic),
          "  %d~%d초 마무리: 예약/문의 행동 한 줄 (고객 연락처는 캡션에)" % (t3, t4)]
    L.append("촬영 가이드(고객이 찍을 컷): 1) 원장·사장 정면 한 줄 인사 2) 현장 손동작 클로즈업 3) 간판 또는 공간 1컷 4) 세로 9:16, 조명 밝게, 소리 조용한 곳")
    L.append("캡션: [%s 한 줄 요약] / 궁금한 점은 댓글·DM으로 문의 주세요. / #%s #%s #%s" % (topic, industry.replace(" ", ""), topic.replace(" ", ""), "릴스"))
    L.append("금지 표현 점검(%s): %s" % (", ".join(forbid), "제목 후보 중 포함됨 %d개 -> 바꿀 것" % len(bad_titles) if bad_titles else "제목 후보에는 없음. 대본·캡션은 사람이 다시 확인"))
    if industry in ("치과", "병원", "의원", "한의원", "피부과", "성형외과"):
        L.append("의료 업종 주의: 의료광고는 사전 심의·표현 제한(과장·치료 효과 단정 등)이 있을 수 있어 고객 병원이 확인해야 한다(영상은 이 부분을 다루지 않음).")
    L.append("")
    L.append("[ChatGPT에 보낼 요청 공식] (영상의 '이런 제목을 짓고 싶은데 뭐라고 물어보면 돼?' 방식)")
    L.append("나는 %s 릴스 대행을 한다. 아래 참고 릴스(제목을 캡처해 첨부)와 같은 느낌으로 '%s' 주제의 릴스 제목 후보 5개, 첫 3초 대사, %d초 대본, 캡션 3줄을 써 줘. 쓰면 안 되는 표현: %s. 먼저 이 요청을 가장 잘 받는 질문 템플릿을 만들어 줘." % (industry, topic, dur, ", ".join(forbid)))
    if ai:
        L.append("")
        L.append("[AI 영상: 시작/끝 이미지 방식] 영상의 순서: 이미지 2장(전/후) -> 시작·끝 프레임으로 지정해 움직임 영상 -> 편집앱에서 컷·속도·음악")
        L.append("시작 이미지 프롬프트: %s 장면, 시작 상태(%s 전), 세로 9:16, 사실적 조명, 인물 얼굴 특정하지 않음" % (industry, topic))
        L.append("끝 이미지 프롬프트: 같은 인물·같은 배경, 끝 상태(%s 후), 같은 화풍(고객이 원하는 스타일 지정)" % topic)
        L.append("움직임 프롬프트: 시작 이미지에서 끝 이미지로 자연스럽게 이어지게, 카메라는 천천히 가까이")
        L.append("고객 본인 사진·로고는 사용 동의를 받는다. 배경음악은 인스타·유튜브가 허용한 음악만 쓴다.")
    L.append("")
    L.append("[편집자 전달 체크] 첫 컷은 움직임 큰 구간부터 / 느리면 속도 1.2배 / 자막 한 줄 12자 안팎 / 음악 라이선스 확인 / 고객 승인 후 전달")
    L.append("")
    L.append("[업로드 일정] 주 %d회 x %d주 (시작 %s, 월·목 위주 예시)" % (per_week, weeks, d0.isoformat()))
    dates = []
    for w in range(weeks):
        for k in range(per_week):
            dates.append(d0 + datetime.timedelta(days=7 * w + (0 if k == 0 else 3) + (k > 1) * (k - 1) * 2))
    L.append("  " + ", ".join(x.strftime("%m/%d(%a)") for x in dates))
    return {"titles": titles, "dates": [x.isoformat() for x in dates], "bad_titles": bad_titles}, "\n".join(L)


def api(params):
    p = params or {}
    r1, t1 = quote(p)
    r2, t2 = brief(p)
    return {"ok": True, "text": t1 + "\n\n" + t2, "quote": r1, "brief": r2,
            "note": "가정값 기반 계산이며 수익을 보장하지 않는다. 투자·사업 권유가 아니다."}


if __name__ == "__main__":
    r = api({})
    assert r["ok"] and "[견적" in r["text"] and "[고객용 기획서" in r["text"]
    assert r["quote"]["videos"] == 24 and abs(r["quote"]["per_video"] - 275000) < 1
    assert len(r["brief"]["dates"]) == 8
    print(r["text"])
    print("성공")
