"""무재고 유통 계산·분석 키트 (영상 7xFQfU_fZUI, money_touch).

영상의 실제 판단 도구 3가지를 입력만 바꿔 쓰게 옮겼다.
  1) 판매가 계산: 영상식 '원가 x 환율 x 1.4' 와, 수수료·마진을 넣어 거꾸로 구하는 방식을 나란히 보여 준다.
  2) 등록 시간 비교: 수동(상품 1개 N분) 대 프로그램(1개 N초). 영상이 말한 '1만 개 = 11년'을 다시 계산한다.
  3) 팔린 이유 4축 분석: 판매 이력을 브랜드·카테고리·키워드·시즌으로 나눠 어느 축이 판매를 가장 잘 설명하는지,
     어느 값을 더 넣어야 하는지 본다(영상: '팔린 이유는 이 네 가지 중 하나').
수수료·마진·환율·판매 이력은 모두 가정값이다. 외부 호출 없음, 표준 라이브러리만 사용."""
import math
import sys

DEFAULT_SALES = """셀프 스피도 물안경 A,스피도,물안경,바캉스/수영,여름,18
스피도 물안경 B,스피도,물안경,수영/성인,여름,12
스피도 수영모,스피도,수영모,수영,여름,9
무명 물안경 C,무명,물안경,수영,여름,2
무명 물안경 D,무명,물안경,바캉스,여름,1
무명 수영모 E,무명,수영모,수영,여름,1
자라 롱코트 F,자라,코트,겨울/선물,겨울,3
자라 숏코트 G,자라,코트,겨울,겨울,2
무명 롱코트 H,무명,코트,겨울,겨울,1
무명 머플러 I,무명,머플러,겨울/선물,겨울,0
무명 머플러 J,무명,머플러,겨울,겨울,1
스피도 가방 K,스피도,가방,수영,여름,8"""
AXES = (("brand", "브랜드", 1), ("category", "카테고리", 2), ("keyword", "키워드", 3), ("season", "시즌", 4))


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


def ceil100(x):
    return int(math.ceil(x / 100.0) * 100)


def price_block(p):
    cost = _num(p.get("cost"), 100, 0)
    rate = _num(p.get("rate"), 1500, 0)
    fee = _num(p.get("fee_pct"), 7, 0) / 100
    margin = _num(p.get("margin_pct"), 20, 0) / 100
    mult = _num(p.get("multiplier"), 1.4, 0)
    ship = _num(p.get("shipping"), 0, 0)
    cost_krw = cost * rate
    lines = ["[1] 판매가 계산 (원가 %s x 환율 %s = %s, 건당 추가비용 %s)" % (
        "{:g}".format(cost), "{:g}".format(rate), won(cost_krw), won(ship))]
    res = {"cost_krw": cost_krw}
    # 방식 A: 영상식 곱하기
    pa = ceil100(cost_krw * mult)
    net_a = pa * (1 - fee) - cost_krw - ship
    ra = net_a / pa if pa else 0
    lines.append("  A. 영상식 x%g: 판매가 %s -> 수수료 %g%% 내고 남는 돈 %s (순마진율 %.1f%%)" % (
        mult, won(pa), fee * 100, won(net_a), ra * 100))
    # 방식 B: 역산
    denom = 1 - fee - margin
    if denom <= 0:
        pb = None
        lines.append("  B. 수수료+마진이 100%% 이상이라 역산 불가")
    else:
        pb = ceil100((cost_krw + ship) / denom)
        net_b = pb * (1 - fee) - cost_krw - ship
        lines.append("  B. 마진 %g%% 목표 역산: 판매가 %s -> 남는 돈 %s (순마진율 %.1f%%)" % (
            margin * 100, won(pb), won(net_b), net_b / pb * 100))
        res["price_reverse"] = pb
    # x배수가 목표 마진을 맞추는지 점검
    need = 1 / denom if denom > 0 else None
    if need:
        verdict = "충분" if mult >= (cost_krw + ship) / cost_krw / denom - 1e-9 else "부족"
        lines.append("  점검: 수수료 %g%% + 마진 %g%% 를 맞추려면 배수 약 %.2f 필요 -> 곱하기 %g 는 %s" % (
            fee * 100, margin * 100, (cost_krw + ship) / cost_krw / denom if cost_krw else 0, mult, verdict))
    res["price_multiplier"] = pa
    res["net_multiplier"] = net_a
    return lines, res


def time_block(p):
    n = _num(p.get("count"), 10000, 1)
    manual_min = _num(p.get("manual_min"), 25, 0.01)
    auto_sec = _num(p.get("auto_sec"), 10, 0.01)
    hours_per_day = _num(p.get("hours_per_day"), 8, 0.1)
    manual_total_min = n * manual_min
    auto_total_h = n * auto_sec / 3600.0
    manual_days_nonstop = manual_total_min / 60.0 / 24
    manual_days_work = manual_total_min / 60.0 / hours_per_day
    lines = ["[2] 등록 시간 비교 (상품 %s개)" % "{:,}".format(int(n))]
    lines.append("  수동 %g분/개: %s시간 = 쉬지 않고 %.1f일, 하루 %g시간 일하면 %.0f일(약 %.1f년)" % (
        manual_min, "{:,.0f}".format(manual_total_min / 60), manual_days_nonstop, hours_per_day,
        manual_days_work, manual_days_work / 365))
    lines.append("  프로그램 %g초/개: %.1f시간 (켜 두면 되는 시간)" % (auto_sec, auto_total_h))
    lines.append("  참고: 영상은 '10분 x 1만 개'를 11년이라고 말했지만 계산하면 100,000분 = 약 %.0f일(쉬지 않을 때)이다. 영상 속 계산 오류로 보인다." % (
        10 * 10000 / 60.0 / 24))
    return lines, {"manual_hours": manual_total_min / 60.0, "auto_hours": auto_total_h}


def parse_sales(text):
    rows = []
    bad = 0
    for ln in (text or "").splitlines():
        if not ln.strip():
            continue
        parts = [x.strip() for x in ln.split(",")]
        if len(parts) < 6:
            bad += 1
            continue
        try:
            sold = float(parts[5])
        except ValueError:
            bad += 1
            continue
        kws = [k.strip() for k in parts[3].split("/") if k.strip()] or ["(없음)"]
        rows.append({"name": parts[0], "brand": parts[1] or "(없음)", "category": parts[2] or "(없음)",
                     "keywords": kws, "season": parts[4] or "(없음)", "sold": sold})
    return rows, bad


def axis_values(row, axis):
    return row["keywords"] if axis == "keyword" else [row[axis]]


def analyze_axis(rows, axis):
    """값별 (상품 수, 판매 합, 판매 점유/등록 점유=lift) 와 축이 판매를 설명하는 정도(eta^2)."""
    total_sold = sum(r["sold"] for r in rows) or 1.0
    n_items = len(rows)
    groups = {}
    for r in rows:
        for v in axis_values(r, axis):
            groups.setdefault(v, []).append(r["sold"])
    out = []
    for v, arr in groups.items():
        sold = sum(arr)
        lift = (sold / total_sold) / (len(arr) / n_items) if n_items else 0
        out.append({"value": v, "items": len(arr), "sold": sold, "avg": sold / len(arr), "lift": lift})
    out.sort(key=lambda x: (-x["lift"], -x["sold"]))
    # eta^2: 값 하나짜리 그룹은 '단독'으로 묶어 과대평가를 막는다
    samples = []
    for v, arr in groups.items():
        label = v if len(arr) >= 2 else "(단독)"
        for s in arr:
            samples.append((label, s))
    mean = sum(s for _, s in samples) / len(samples) if samples else 0
    ss_total = sum((s - mean) ** 2 for _, s in samples)
    g2 = {}
    for lab, s in samples:
        g2.setdefault(lab, []).append(s)
    ss_between = sum(len(a) * (sum(a) / len(a) - mean) ** 2 for a in g2.values())
    eta = ss_between / ss_total if ss_total > 0 else 0.0
    return out, eta


def analysis_block(p):
    rows, bad = parse_sales(p.get("sales", DEFAULT_SALES))
    lines = ["[3] 팔린 이유 4축 분석 (판매 이력 %d개 상품%s)" % (len(rows), ", 읽지 못한 줄 %d" % bad if bad else "")]
    if len(rows) < 6:
        lines.append("  상품이 6개 미만이면 결론이 불안정하다. 판매 이력을 더 넣어 주세요.")
        return lines, {"axes": {}}
    total = sum(r["sold"] for r in rows)
    lines.append("  총 판매 %g건. 점유 대비(lift)=판매 점유 / 등록 점유. 1보다 클수록 '등록 대비 잘 팔림'." % total)
    ranking = []
    detail = {}
    for key, label, _ in AXES:
        vals, eta = analyze_axis(rows, key)
        detail[key] = {"eta": eta, "top": vals[:3]}
        ranking.append((eta, key, label))
    ranking.sort(reverse=True)
    lines.append("  판매를 가장 잘 설명하는 축 순서(설명력, 단독 1개짜리는 묶어서 계산):")
    for eta, key, label in ranking:
        lines.append("    %s %.0f%%" % (label, eta * 100))
    best = ranking[0]
    lines.append("  => 이 데이터에서는 '%s' 축이 가장 크다. 영상 방식: 이 축에서 lift가 높은 값에 등록을 더 늘리고, 낮은 값은 줄여 본다." % best[2])
    for eta, key, label in ranking:
        top = [v for v in detail[key]["top"] if v["items"] >= 2][:2]
        if top:
            lines.append("  %s 상위: %s" % (label, ", ".join(
                "%s(상품 %d개, 판매 %g건, lift %.2f)" % (v["value"], v["items"], v["sold"], v["lift"]) for v in top)))
    lines.append("  주의: 판매 이력이 적으면 우연일 수 있다. 상품 수 2개 이상인 값만 상위에 표시했고, 영상의 '4가지 중 하나' 가설을 검산하는 용도이다.")
    return lines, {"axes": {k: {"eta": detail[k]["eta"]} for k, _, _ in AXES}, "best_axis": best[1]}


def api(params):
    p = params or {}
    try:
        l1, r1 = price_block(p)
        l2, r2 = time_block(p)
        l3, r3 = analysis_block(p)
    except Exception as e:  # 입력 오류도 한국어로 돌려준다
        return {"ok": False, "text": "계산 중 오류: %s" % e}
    text = "\n".join(l1 + [""] + l2 + [""] + l3 + ["", "※ 가정값 계산기이며 수익을 보장하거나 투자·사업을 권하지 않습니다. 브랜드 이미지·상표 사용은 마켓 정책과 법적 확인이 필요합니다."])
    return {"ok": True, "text": text, "price": r1, "time": r2, "analysis": r3}


if __name__ == "__main__":
    r = api({})
    assert r["ok"], r
    # 영상 숫자 확인: 100유로 x 1500 x 1.4 = 21만원
    assert r["price"]["price_multiplier"] == 210000, r["price"]
    assert round(r["time"]["auto_hours"], 1) == 27.8
    assert r["analysis"]["best_axis"] in ("brand", "season", "category", "keyword")
    bad = api({"cost": "abc", "fee_pct": "x", "sales": "깨진 줄"})
    assert bad["ok"], bad
    print(r["text"])
    print("성공")
    sys.exit(0)
