"""AI 1인 기업 운영 키트 (영상 VD9OCNkJ8Dw, THE FOUNDER EP.1).

영상의 핵심을 계산기로 옮겼다.
  1) 런웨이: 예산 / (하루 토큰비 + 전기 + 월세) = 며칠 버티는지, 그 날짜까지 성과가 없으면 중단(kill)하는 마감일
  2) 작업별 모델 라우팅: 품질이 덜 필요한 일은 작은 모델·로컬 AI로 보내 비용 줄이기
  3) 컴퓨터 역할 나누기: 램이 큰 컴퓨터는 3D·렌더, 가벼운 컴퓨터는 코딩·분석
  4) 투자자 관점 포트폴리오: 100개를 만들고 몇 개만 성공하면 되는지(성공 확률 1%→3%→5%)
  5) 하루 루틴표: 아침 8시 회의 → 기획·개발·마케팅·운영 4사이클
가격·확률·램은 모두 '가정값'이다. 내 실제 값으로 바꿔서 쓰도록 입력으로 받는다. 외부 API 호출 없음."""
import datetime
import sys

DEFAULT_MODELS = "large: 300, 3\nsmall: 40, 2\nlocal: 0, 1"
DEFAULT_TASKS = "아이디어 브레인스토밍: 3\n광고 문구 쓰기: 2\n바이브 코딩 MVP: 2\n댓글 분류: 1\n트렌드 요약: 1"
DEFAULT_MACHINES = "맥 스튜디오 울트라: 128\n맥 스튜디오 프로: 64\n맥북 프로: 32\n작은 서버: 8"
JOBS = (("3D 모델링·렌더(블렌더)", 96), ("영상·이미지 로컬 생성", 48), ("바이브 코딩", 16), ("댓글·트렌드 분석(작은 모델)", 8))


def _pairs(text, cast_second=float):
    out = []
    for ln in (text or "").splitlines():
        a, _, b = ln.partition(":")
        if a.strip() and b.strip():
            out.append((a.strip(), b.strip()))
    return out


def parse_models(text):
    m = {}
    for name, rest in _pairs(text):
        cost, _, q = rest.partition(",")
        m[name] = {"cost_per_10k": float(cost), "quality": int(q)}
    return m


def parse_tasks(text):
    return {n: int(v) for n, v in _pairs(text)}


def route(task_need, models):
    ok = [(n, v) for n, v in models.items() if v["quality"] >= task_need]
    return min(ok, key=lambda kv: (kv[1]["cost_per_10k"], kv[1]["quality"]))[0]


def assign_machines(machines):
    """작업은 램이 큰 것부터, 각 작업을 '들어가는 가장 작은 컴퓨터'에 배정(큰 컴퓨터는 큰 일에 남긴다)."""
    free = sorted(machines, key=lambda kv: kv[1])
    out = []
    for job, need in sorted(JOBS, key=lambda j: -j[1]):
        fit = next((m for m in free if m[1] >= need), None)
        out.append({"작업": job, "필요 램(GB)": need, "배정": fit[0] if fit else "램 부족(클라우드·구독 AI로)"})
    return out


def portfolio(ideas, p, cost, payoff):
    one = 1 - (1 - p) ** ideas
    total = ideas * cost
    exp_win = ideas * p
    return {"아이디어 수": ideas, "성공 확률": f"{p * 100:g}%", "기대 성공 수": round(exp_win, 2),
            "한 개 이상 성공할 확률": round(one * 100, 1), "총 투입(원)": int(total),
            "기대 수익(원)": int(exp_win * payoff - total),
            "손익분기 성공당 수익(원)": int(cost / p) if p else None}


ROUTINE = (
    "08:00 아침 회의: AI가 가져온 아이디어 확인 -> 오늘 만들 것 1~2개 지시, 어제 성과(조회·방문·매출)와 문제점 확인\n"
    "09:00 기획: 시장·경쟁 서비스 조사, 만들 범위를 MVP 한 가지로 줄이기(좋은 모델 불필요)\n"
    "10:00 개발: 바이브 코딩으로 MVP 만들고 배포\n"
    "13:00 마케팅: 같은 브랜드로 인스타·스레드·블로그·유튜브 콘텐츠 만들기(가능하면 로컬 AI로 비용 절약)\n"
    "17:00 운영: 어제 것 데이터 분석, 안 되는 것은 중단 기준일 확인 후 버리기\n"
    "22:00 밤샘 작업 걸어 두기: 렌더·로컬 생성 같은 오래 걸리는 일"
)


def api(params=None):
    p = params or {}
    try:
        budget = float(p.get("budget") or 1_000_000)
        tokens = float(p.get("tokens") or 50_000)
        power = float(p.get("power") or 1500)
        rent = float(p.get("rent") or 0)
        ideas = int(float(p.get("ideas") or 100))
        succ = float(p.get("success_percent") or 3) / 100
        cost = float(p.get("cost_per_idea") or 10_000)
        payoff = float(p.get("payoff") or 1_000_000)
        start = datetime.date.fromisoformat(str(p.get("start") or "2026-11-12"))
        models = parse_models(p.get("models") or DEFAULT_MODELS)
        tasks = parse_tasks(p.get("tasks") or DEFAULT_TASKS)
        machines = [(n, float(v)) for n, v in _pairs(p.get("machines") or DEFAULT_MACHINES)]
    except (ValueError, TypeError) as e:
        return {"ok": False, "error": "입력 형식을 확인하세요: " + str(e)}
    if not models or not tasks or not machines or budget <= 0 or ideas <= 0 or not (0 < succ < 1):
        return {"ok": False, "error": "예산·아이디어 수는 0보다 크고, 성공 확률은 0~100 사이(%)여야 하며 모델·작업·컴퓨터 표가 비어 있으면 안 됩니다."}

    def cost_of(always_best):
        top = max(models, key=lambda n: models[n]["quality"])
        return sum(models[top if always_best else route(need, models)]["cost_per_10k"] * tokens / 10_000 for need in tasks.values())

    big, smart = cost_of(True), cost_of(False)
    burn = smart + power + rent / 30
    days = int(budget // burn) if burn else 0
    kill = start + datetime.timedelta(days=days)
    routes = {t: route(n, models) for t, n in tasks.items()}
    scen = [portfolio(ideas, s, cost, payoff) for s in (0.01, 0.03, 0.05)]
    mine = portfolio(ideas, succ, cost, payoff)
    mach = assign_machines(machines)
    lines = [
        f"[런웨이] 예산 {budget:,.0f}원 / 하루 소모 {burn:,.0f}원 = {days}일 버팀",
        f"  하루 소모 = 토큰비 {smart:,.0f} + 전기 {power:,.0f} + 월세 {rent / 30:,.0f}.  이 날({kill})까지 성과가 없으면 중단.",
        f"[모델 라우팅] 전부 최고 모델 {big:,.0f}원/일 -> 작업별 분배 {smart:,.0f}원/일 (절감 {round(100 * (big - smart) / big) if big else 0}%)",
    ] + [f"  {t} -> {m}" for t, m in routes.items()] + ["[컴퓨터 역할]"] + [
        f"  {m['작업']}({m['필요 램(GB)']}GB) -> {m['배정']}" for m in mach] + [
        f"[투자자 관점] 아이디어 {ideas}개, 성공 확률 {succ * 100:g}%: 한 개 이상 성공할 확률 {mine['한 개 이상 성공할 확률']}%, "
        f"기대 성공 {mine['기대 성공 수']}개, 기대 수익 {mine['기대 수익(원)']:,}원 (성공당 수익 {payoff:,.0f}원 가정)",
        f"  손익분기: 성공 1개가 {mine['손익분기 성공당 수익(원)']:,}원 이상 벌어야 본전",
        "  확률별: " + " / ".join(f"{s['성공 확률']} -> 1개 이상 {s['한 개 이상 성공할 확률']}%" for s in scen),
        "[하루 루틴]", *["  " + r for r in ROUTINE.splitlines()],
        "※ 가격·확률·램은 가정값입니다. 내 값으로 바꿔 쓰세요.",
    ]
    return {"ok": smart <= big, "text": "\n".join(lines), "runway_days": days, "kill_date": kill.isoformat(),
            "daily_burn": round(burn), "daily_cost_all_large": round(big), "daily_cost_routed": round(smart),
            "saving_percent": round(100 * (big - smart) / big) if big else 0, "routes": routes,
            "machines": mach, "portfolio": mine, "scenarios": scen, "routine": ROUTINE.splitlines()}


if __name__ == "__main__":
    r = api({})
    print(r["text"])
    assert r["ok"] and r["routes"]["댓글 분류"] == "local" and r["routes"]["아이디어 브레인스토밍"] == "large"
    assert r["daily_cost_routed"] < r["daily_cost_all_large"] and r["runway_days"] > 0 and r["kill_date"] > "2026-11-12"
    m = {x["작업"]: x["배정"] for x in r["machines"]}
    assert m["3D 모델링·렌더(블렌더)"] == "맥 스튜디오 울트라" and m["바이브 코딩"] == "맥북 프로"
    s = {x["성공 확률"]: x["한 개 이상 성공할 확률"] for x in r["scenarios"]}
    assert s["1%"] == 63.4 and s["5%"] == 99.4 and r["portfolio"]["손익분기 성공당 수익(원)"] == 333333
    assert api({"success_percent": "0"})["ok"] is False and api({"budget": "abc"})["ok"] is False
    print("성공")
    sys.exit(0)
