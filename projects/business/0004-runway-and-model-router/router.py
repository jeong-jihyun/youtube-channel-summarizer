"""AI 1인 기업 운영 흉내: (1) 런웨이 계산기 (2) 작업별 모델 라우터(비용 최적화).
가격·숫자는 모두 가정값(모의)이며 실제 요금이 아니다. 외부 API 호출 없음."""

# 가정값: 1만 토큰당 원화 비용
MODELS = {"large": {"cost_per_10k": 300, "quality": 3},
          "small": {"cost_per_10k": 40, "quality": 2},
          "local": {"cost_per_10k": 0, "quality": 1}}
# 작업별로 필요한 최소 품질
TASKS = {"idea_brainstorm": 3, "code_mvp": 2, "classify_comments": 1, "summarize_trends": 1, "write_ad_copy": 2}

def route(task):
    need = TASKS[task]
    ok = [(m, v) for m, v in MODELS.items() if v["quality"] >= need]
    return min(ok, key=lambda kv: kv[1]["cost_per_10k"])[0]

def daily_cost(tokens_per_task=50_000, always_large=False):
    total = 0
    for t in TASKS:
        m = "large" if always_large else route(t)
        total += MODELS[m]["cost_per_10k"] * tokens_per_task / 10_000
    return total

def runway_days(budget_krw, daily_token_cost, daily_power_krw=1500, daily_rent_krw=0):
    burn = daily_token_cost + daily_power_krw + daily_rent_krw
    return burn, int(budget_krw // burn)


def api(params=None):
    """params: {"budget": "1000000", "tokens": "50000", "power": "1500"}"""
    p = params or {}
    budget, tokens, power = int(p.get("budget", 1_000_000)), int(p.get("tokens", 50_000)), int(p.get("power", 1500))
    routes = {t: route(t) for t in TASKS}
    big, smart = daily_cost(tokens, True), daily_cost(tokens)
    burn, days = runway_days(budget, smart, power)
    return {"ok": smart <= big, "routes": routes, "daily_cost_all_large": big, "daily_cost_routed": smart,
            "saving_percent": round(100 * (big - smart) / big) if big else 0, "daily_burn": burn, "runway_days": days,
            "note": "가격은 가정값(모의)"}

if __name__ == "__main__":
    for t in TASKS:
        print(f"{t:18s} -> {route(t)}")
    big, smart = daily_cost(always_large=True), daily_cost()
    print(f"하루 토큰비: 전부 large {big:.0f}원 / 라우팅 {smart:.0f}원 (절감 {100 * (big - smart) / big:.0f}%)")
    burn, days = runway_days(1_000_000, smart)
    print(f"예산 100만원, 하루 소모 {burn:.0f}원 -> 런웨이 {days}일")
    assert route("classify_comments") == "local" and route("idea_brainstorm") == "large"
    assert smart < big and days > runway_days(1_000_000, big)[1]
    print("성공")
