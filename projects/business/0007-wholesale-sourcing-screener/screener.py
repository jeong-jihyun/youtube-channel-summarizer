"""도매 소싱 후보 점검기 (영상 JYmuv39Ka64, money_touch).

영상이 보여 준 '창고 가격 vs 쿠팡 판매가' 장면에는 판단 기준이 숨어 있다.
  - 마진율(영상: 보통 20% 이상, 묶음 팔면 30~50%)
  - 묶음 판매(단품보다 묶음이 마진이 큼)
  - 객단가가 높은 품목(건강식품·화장품)과 재구매
  - 유통기한이 한참 남았는지
영상이 거의 말하지 않은 판매 수수료·배송비·포장비·반품 손실을 가정값 입력으로 넣어
'영상 속 총마진'과 '비용을 넣은 순마진'을 나란히 비교한다. 월 매출 x 순마진 시나리오와
먼저 사 두는 재고 자금(창고 소싱은 선매입이다)도 계산한다.
모든 수수료·비용·기준값은 가정이다. 표준 라이브러리만 사용, 외부 호출 없음."""
import datetime
import sys

DEFAULT_ITEMS = """수세미 모음 세트,1000,3,10000,없음,N
다이어트 건강식품,9900,1,55000,2027-11-30,Y
영양제 3개 묶음,3300,3,30000,2027-06-30,Y
샴푸,4900,1,32000,2027-09-30,Y
바디로션 3종,9900,1,30000,2027-04-30,Y
마스크팩 10매,4900,1,15000,2027-03-31,N
스크럽 스폰지 세트,100,3,15000,없음,N
유통기한 임박 영양제,3000,1,20000,2026-12-20,Y"""


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


def parse_items(text):
    items, bad = [], []
    for ln in (text or "").splitlines():
        if not ln.strip():
            continue
        c = [x.strip() for x in ln.split(",")]
        try:
            if len(c) < 6:
                raise ValueError("칸이 6개 미만")
            exp = None
            if c[4] and c[4] not in ("없음", "-", "해당없음"):
                exp = datetime.date.fromisoformat(c[4])
            items.append({"name": c[0], "unit_cost": float(c[1]), "bundle": max(1, int(float(c[2]))),
                          "price": float(c[3]), "expiry": exp, "repeat": c[5].upper().startswith("Y")})
        except (ValueError, TypeError) as e:
            bad.append("%s (%s)" % (ln.strip()[:30], e))
    return items, bad


def evaluate(it, cfg):
    cost = it["unit_cost"] * it["bundle"]
    price = it["price"]
    fee = price * cfg["fee"]
    exp_ret = cfg["return_rate"] * (2 * cfg["ship"] + cfg["return_loss"] * cost)
    net = price - fee - cost - cfg["ship"] - cfg["pack"] - exp_ret
    video_gross = (price - cost) / price if price else 0
    # 단품으로 팔 때(묶음 효과 비교): 개당 가격으로 1개씩 주문받는다고 가정
    single_price = price / it["bundle"]
    single_net = single_price * (1 - cfg["fee"]) - it["unit_cost"] - cfg["ship"] - cfg["pack"] \
        - cfg["return_rate"] * (2 * cfg["ship"] + cfg["return_loss"] * it["unit_cost"])
    months = None
    if it["expiry"]:
        months = (it["expiry"] - cfg["today"]).days / 30.0
    flags = []
    if months is not None and months < 0:
        flags.append("유통기한 지남")
    elif months is not None and months < cfg["min_months"]:
        flags.append("유통기한 %.1f개월(기준 %g개월 미만)" % (months, cfg["min_months"]))
    if price < cfg["min_price"]:
        flags.append("객단가 %s 미만" % won(cfg["min_price"]))
    net_rate = net / price if price else 0
    if (months is not None and months < 0) or net <= 0:
        verdict = "제외"
    elif flags or net_rate < cfg["target"]:
        verdict = "보류"
    else:
        verdict = "후보"
    if net_rate < cfg["target"] and net > 0:
        flags.append("순마진 %.0f%% < 목표 %.0f%%" % (net_rate * 100, cfg["target"] * 100))
    if it["bundle"] == 1 and price and (price - cost) / price > 0 and net_rate < cfg["target"]:
        flags.append("묶음 판매로 배송비 비중을 낮춰 볼 것")
    return {"name": it["name"], "cost": cost, "price": price, "net": net, "net_rate": net_rate,
            "video_gross": video_gross, "single_net": single_net, "months": months, "flags": flags,
            "verdict": verdict, "repeat": it["repeat"]}


def api(params):
    p = params or {}
    try:
        today = datetime.date.fromisoformat(str(p.get("today", "2026-11-12")).strip())
    except ValueError:
        return {"ok": False, "text": "기준일은 YYYY-MM-DD 형식으로 입력하세요."}
    cfg = {"fee": _num(p.get("fee_pct"), 10, 0) / 100, "ship": _num(p.get("shipping"), 3000, 0),
           "pack": _num(p.get("packing"), 500, 0), "return_rate": _num(p.get("return_pct"), 3, 0) / 100,
           "return_loss": _num(p.get("return_loss_pct"), 30, 0) / 100, "target": _num(p.get("target_pct"), 20, 0) / 100,
           "min_months": _num(p.get("min_months"), 6, 0), "min_price": _num(p.get("min_price"), 10000, 0), "today": today}
    items, bad = parse_items(p.get("items", DEFAULT_ITEMS))
    if not items:
        return {"ok": False, "text": "읽은 품목이 없습니다. 한 줄 형식: 이름,개당 매입가,묶음 개수,묶음 판매가,유통기한(YYYY-MM-DD 또는 없음),재구매(Y/N)" +
                ("\n읽지 못한 줄: " + "; ".join(bad) if bad else "")}
    res = [evaluate(i, cfg) for i in items]
    order = {"후보": 0, "보류": 1, "제외": 2}
    res.sort(key=lambda r: (order[r["verdict"]], -r["net_rate"]))
    L = ["[1] 품목 점검 (수수료 %g%%, 배송 %s, 포장 %s, 반품 %g%% x 손실 %g%%, 목표 순마진 %g%%, 기준일 %s)" % (
        cfg["fee"] * 100, won(cfg["ship"]), won(cfg["pack"]), cfg["return_rate"] * 100, cfg["return_loss"] * 100,
        cfg["target"] * 100, today.isoformat())]
    for r in res:
        L.append("  [%s] %s: 매입 %s -> 판매 %s | 영상식 총마진 %.0f%% -> 순마진 %.0f%% (%s)%s%s" % (
            r["verdict"], r["name"], won(r["cost"]), won(r["price"]), r["video_gross"] * 100, r["net_rate"] * 100,
            won(r["net"]), " | 재구매 품목" if r["repeat"] else "",
            (" | 주의: " + ", ".join(r["flags"])) if r["flags"] else ""))
    if bad:
        L.append("  읽지 못한 줄: " + "; ".join(bad))
    cand = [r for r in res if r["verdict"] == "후보"]
    L.append("")
    L.append("[2] 묶음 효과 (같은 상품을 개당으로 1개씩 팔 때의 건당 순이익 대비)")
    for r in res:
        if r["verdict"] != "제외":
            L.append("  %s: 묶음 %s vs 단품 1개 주문 %s" % (r["name"], won(r["net"]), won(r["single_net"])))
    sales = _num(p.get("monthly_sales"), 20000000, 0)
    stock_m = _num(p.get("stock_months"), 1, 0)
    L.append("")
    L.append("[3] 월 시나리오 (월 매출 %s, 후보 %d개 평균 기준)" % (won(sales), len(cand)))
    summary = {"candidates": len(cand), "total": len(res)}
    if cand:
        avg_rate = sum(r["net_rate"] for r in cand) / len(cand)
        avg_gross = sum(r["video_gross"] for r in cand) / len(cand)
        avg_price = sum(r["price"] for r in cand) / len(cand)
        avg_cost = sum(r["cost"] for r in cand) / len(cand)
        orders = sales / avg_price if avg_price else 0
        L.append("  영상식 총마진 평균 %.0f%% 로 보면 월 이익 %s 이지만, 비용을 넣은 순마진 %.0f%% 로는 %s 입니다." % (
            avg_gross * 100, won(sales * avg_gross), avg_rate * 100, won(sales * avg_rate)))
        L.append("  필요한 주문: 월 약 %s건(하루 %.0f건, 평균 판매가 %s)." % (
            "{:,.0f}".format(orders), orders / 30, won(avg_price)))
        L.append("  먼저 사 둘 재고 자금: 월 %s건 x 평균 매입 %s x %g개월치 = %s (창고 소싱은 선매입이라 팔리지 않으면 재고가 남음)." % (
            "{:,.0f}".format(orders), won(avg_cost), stock_m, won(orders * avg_cost * stock_m)))
        L.append("  일관성 점검: 영상 속 창고가-쿠팡가 격차(총마진 평균 %.0f%%)와 영상이 말한 실제 마진(20%% 이상)은 크게 다르다. 실제 판매가가 비교가보다 낮거나 비용·재고 손실이 크다는 뜻일 수 있으니 '쿠팡 정가'가 아니라 내가 팔 가격을 넣어 보세요." % (avg_gross * 100))
        L.append("  영상 점검: 매출 2,000만원 x 마진 20%% = %s (영상의 '월 순수익 400만원' 계산과 같은 식. 배송·수수료 반영 여부는 영상에서 확인되지 않음)." % won(20000000 * 0.2))
        summary.update({"avg_net_rate": avg_rate, "avg_gross": avg_gross, "monthly_net": sales * avg_rate,
                        "stock_cash": orders * avg_cost * stock_m})
    else:
        L.append("  후보가 없어 시나리오를 만들지 않습니다. 수수료·배송 가정이나 품목을 바꿔 보세요.")
    L += ["", "※ 가정값 계산기이며 수익을 보장하거나 투자·사업을 권하지 않습니다. 정품 여부·유통기한 표시·건강기능식품 판매 신고 등 법적 요건은 따로 확인하세요."]
    return {"ok": True, "text": "\n".join(L), "items": [{k: v for k, v in r.items() if k != "flags"} for r in res], "summary": summary}


if __name__ == "__main__":
    r = api({})
    assert r["ok"], r
    v = {x["name"]: x["verdict"] for x in r["items"]}
    assert v["유통기한 임박 영양제"] in ("보류", "제외"), v
    assert r["summary"]["candidates"] >= 1
    assert api({"items": "깨진 줄"})["ok"] is False
    print(r["text"])
    print("성공")
    sys.exit(0)
