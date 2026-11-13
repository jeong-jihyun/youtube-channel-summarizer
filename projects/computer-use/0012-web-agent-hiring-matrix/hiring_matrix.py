"""웹 AI 에이전트 고용 비교표 (영상 p7KaCOuJP2M, AI 야학당 '웹 잘하는 AI 에이전트, 누구를 고용할까?').

영상은 같은 '웹 잘하는 직원' 6명(뮤즈·피클·크롬 익스텐션·어사이드·에고라이트·컴퓨터 유즈)을
'어디서 일하나(미국 클라우드 / 내 컴퓨터)'와 '서로 어떻게 소통하나'로 가르고 장단점을 말한다.
이 도구는 그 말을 점검 가능한 규칙으로 옮겼다.
  1) 내 상황(앱 제어 필요, 폰만 있음, 로그인 민감, 여러 모델, 개발 도구 사용, PC 사양, 예산, 속도)을
     넣으면 6명을 점수와 이유로 순위를 매긴다. '불가' 조건은 영상이 직접 말한 것(앱 제어·폰 전용)이다.
  2) 인스타그램 'CODE 댓글' 실습(27:38~30:50) 지시문을 내 값으로 만든다.
  3) 에이전트가 여럿일 때 바탕화면 텍스트 파일로 소통시키는 규칙(23:29)을 템플릿으로 만든다.
  4) 하루 루틴(영상 후반: 10시 운동 영상, 12시 명상 …)을 시각순 표로 만들고 겹침을 잡는다.
  5) 맥 스튜디오(영상: 약 1천만 원) 대비 인건비 손익분기를 가정값으로 계산한다.
점수 숫자는 영상에 없다. 영상의 정성적 발언(저렴하다/느리다/무겁다 등)을 내가 점수로 바꾼 경험칙이다.
영상 시점 설명이므로 각 제품의 기능·요금은 바뀔 수 있다. 표준 라이브러리만 사용."""
import re

AGENTS = {
    "muse": {
        "name": "뮤즈(Muse, 메타)", "where": "미국 클라우드", "cost": "무료~저렴", "speed": "느림",
        "phone": True, "app": False, "pc_needed": False, "region_risk": True, "multi_model": False,
        "dev": False, "heavy": False,
        "pros": "내 컴퓨터가 필요 없다. 루틴(시각 지정)이 있다. 거의 무료.",
        "cons": "느리다. 미국에서 접속해 인스타·유튜브가 '이상한 접속' 경고·차단을 할 수 있다. 앱은 못 연다.",
        "src": "4:58~8:00",
    },
    "pickle": {
        "name": "피클(Pickle)", "where": "미국 클라우드", "cost": "무료~저렴", "speed": "느림",
        "phone": True, "app": False, "pc_needed": False, "region_risk": True, "multi_model": False,
        "dev": False, "heavy": False,
        "pros": "스마트폰에서 명령해도 남의 컴퓨터가 일한다. 간편하고 저렴하다.",
        "cons": "뮤즈와 같은 한계: 느림, 접속 지역 문제, 내 폰의 앱은 못 연다.",
        "src": "5:26~9:21",
    },
    "chrome_ext": {
        "name": "크롬 익스텐션(클로드·ChatGPT 확장)", "where": "내 컴퓨터 크롬 안", "cost": "구독 기준", "speed": "빠름",
        "phone": False, "app": False, "pc_needed": True, "region_risk": False, "multi_model": False,
        "dev": False, "heavy": False,
        "pros": "내 크롬·내 로그인 그대로라 접속 지역 문제가 없다. 하나만 쓰면 빠르고 좋다.",
        "cons": "확장끼리 서로 소통이 안 된다(클로드가 한 말을 ChatGPT가 모른다). 모델 3개면 창 3개.",
        "src": "10:13~16:18",
    },
    "aside": {
        "name": "어사이드(Aside)", "where": "내 컴퓨터(전용 브라우저)", "cost": "무료 일부+모델 비용", "speed": "보통",
        "phone": False, "app": False, "pc_needed": True, "region_risk": False, "multi_model": True,
        "dev": False, "heavy": True,
        "pros": "한 집에서 ChatGPT·클로드·로컬 AI(LM 스튜디오·올라마)를 초대하고 대화 기록이 공유되어 모델을 바꿔도 기억이 이어진다.",
        "cons": "신생이라 최적화가 덜 되어 메모리를 많이 쓴다(여러 개 동시에 켜면 느려짐).",
        "src": "16:18~20:50",
    },
    "egolite": {
        "name": "에고라이트(Ego-lite)", "where": "내 컴퓨터(가벼운 브라우저)", "cost": "무료 일부+모델 비용", "speed": "빠름",
        "phone": False, "app": False, "pc_needed": True, "region_risk": False, "multi_model": True,
        "dev": True, "heavy": False,
        "pros": "가볍다. 쓰던 도구(안티그래비티·Claude Code·Codex)에 스킬을 설치해 원격 조종한다. 텍스트 파일로 서로 소통시킬 수 있다.",
        "cons": "개발 도구에 익숙한 사람용이다(영상 표현).",
        "src": "20:50~25:30",
    },
    "computer_use": {
        "name": "컴퓨터 유즈", "where": "내 컴퓨터 전체", "cost": "비쌈", "speed": "매우 느림",
        "phone": False, "app": True, "pc_needed": True, "region_risk": False, "multi_model": False,
        "dev": False, "heavy": True,
        "pros": "웹뿐 아니라 마우스·폴더·앱까지 컴퓨터 전체를 움직인다. 앱 스토어 같은 앱 작업이 된다.",
        "cons": "화면 픽셀을 분석해 클릭하므로 느리고 입력이 많아 비용이 크다(영상의 '콧대 높은 차장').",
        "src": "25:30~27:07",
    },
}

YN = {"y": True, "yes": True, "예": True, "네": True, "응": True, "true": True, "1": True,
      "n": False, "no": False, "아니오": False, "아니요": False, "false": False, "0": False, "": False}


def _yn(v):
    return YN.get(str(v or "").strip().lower(), False)


def _num(v, default, lo=0.0):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return default
    return x if x >= lo else default


def score_agents(need_app, phone_only, login_sensitive, multi_model, is_dev, pc_heavy_ok, budget, speed_first):
    """각 에이전트의 (불가 이유 또는 None, 점수, 이유 목록)을 돌려준다. 점수는 경험칙."""
    res = {}
    for key, a in AGENTS.items():
        reasons, score, block = [], 50, None
        if need_app and not a["app"]:
            block = "데스크톱 앱을 열어야 하는데 이 에이전트는 웹 브라우저 안에서만 일한다(영상 9:21 '앱은 왜 못 열까')."
        if phone_only and a["pc_needed"]:
            block = "컴퓨터 없이 폰만 있다고 했는데 이 에이전트는 내 컴퓨터가 있어야 한다."
        if need_app and a["app"]:
            score += 30
            reasons.append("앱까지 제어 가능(+30)")
        if phone_only and a["phone"]:
            score += 25
            reasons.append("폰에서 명령 가능(+25)")
        if login_sensitive:
            if a["region_risk"]:
                score -= 25
                reasons.append("미국 접속이라 인스타·유튜브 보안 경고 위험(-25)")
            else:
                score += 10
                reasons.append("내 컴퓨터·내 지역에서 접속(+10)")
        if multi_model:
            if a["multi_model"]:
                score += 20
                reasons.append("여러 AI 모델 연결(+20)")
            elif key == "chrome_ext":
                score -= 10
                reasons.append("확장끼리 소통 안 됨(-10)")
        if is_dev and a["dev"]:
            score += 15
            reasons.append("개발 도구에 스킬로 붙임(+15)")
        if not is_dev and a["dev"]:
            score -= 10
            reasons.append("개발 도구 경험이 없으면 진입 장벽(-10)")
        if not pc_heavy_ok and a["heavy"]:
            score -= 20
            reasons.append("메모리·연산을 많이 써 PC 사양이 낮으면 느려짐(-20)")
        if budget == "무료":
            if a["cost"].startswith("무료"):
                score += 15
                reasons.append("무료로 시작 가능(+15)")
            elif a["cost"] == "비쌈":
                score -= 20
                reasons.append("비용이 큼(-20)")
        if speed_first:
            sp = {"빠름": 15, "보통": 0, "느림": -15, "매우 느림": -25}[a["speed"]]
            score += sp
            reasons.append("속도 %s(%+d)" % (a["speed"], sp))
        res[key] = (block, max(0, min(100, score)), reasons)
    return res


def ig_prompt(account, post_url, keyword, reply, dm):
    """영상 27:38~30:50 'CODE 댓글' 실습을 내 값으로 옮긴 지시문. 빠진 칸 목록도 준다."""
    gaps = []
    if not account:
        gaps.append("내 계정(영상: 여러분 계정으로 넣는다)")
    if not post_url:
        gaps.append("대상 게시물 주소(영상: 페이지 소스에서 콘텐츠 주소를 복사해 넣는다)")
    if not keyword:
        gaps.append("트리거 단어(영상은 'CODE')")
    lines = [
        "너는 내 인스타그램 계정 %s 의 댓글 관리 직원이다." % (account or "(계정)"),
        "대상 게시물: %s" % (post_url or "(게시물 주소)"),
        "할 일: 이 게시물에 달린 댓글 중 '%s' 라고 쓴 사람에게만 아래 2가지를 한다." % (keyword or "CODE"),
        "  1) 댓글에 답글: \"%s\"" % (reply or "요청 감사합니다! 메시지로 보내 드릴게요."),
        "  2) 그 사람에게 DM 전송: \"%s\"" % (dm or "(보낼 프롬프트/자료 링크)"),
        "규칙: 다른 게시물·다른 댓글은 건드리지 않는다(영상: '다른 거 건들지 말고 이 콘텐츠 댓글에만').",
        "처음 5명까지만 처리하고 결과(누구에게 무엇을 보냈는지)를 표로 보고한 뒤 멈춘다.",
        "로그인 확인·보안 경고·이상 접속 화면이 나오면 즉시 멈추고 나에게 알린다.",
    ]
    return "\n".join(lines), gaps


def handoff_rules(agents_list, path):
    """영상 23:29 '가운데 텍스트 파일로 소통': 서로 분리된 에이전트가 파일 하나로 맥락을 공유하는 규칙."""
    agents = [x for x in agents_list if x] or ["Claude", "ChatGPT", "안티그래비티"]
    head = ["# 공유 대화 기록 (모든 에이전트가 같은 파일을 읽고 쓴다)", "# 위치: %s" % path, ""]
    rules = [
        "규칙(각 에이전트에게 똑같이 붙여 넣기):",
        "1. 일을 시작하기 전에 %s 를 처음부터 끝까지 읽는다." % path,
        "2. 답을 하기 전에 앞사람 의견을 한 줄로 인용하고 동의·반대를 밝힌다(안 읽고 답하면 영상 속 '기구멍으로 들은' 답이 된다).",
        "3. 답한 뒤 파일 맨 아래에 아래 형식으로 한 항목을 덧붙인다. 기존 내용은 지우거나 고치지 않는다.",
        "4. 사람(나)의 결정은 '## 결정' 항목으로 적고, 결정이 나기 전에는 다음 단계로 가지 않는다.",
        "",
        "항목 형식:",
        "## [순번] 에이전트이름 / HH:MM",
        "- 한 일/의견:",
        "- 앞사람 의견에 대한 반응:",
        "- 다음 사람에게 넘길 것:",
        "",
        "참여 에이전트: " + ", ".join(agents),
    ]
    return "\n".join(head + rules)


def routine_table(text):
    """한 줄에 'HH:MM|할 일'. 시각순 표와 같은 시각 겹침을 돌려준다."""
    rows, bad, seen = [], [], {}
    for ln in str(text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = re.fullmatch(r"(\d{1,2}):(\d{2})\s*\|\s*(.+)", ln)
        if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
            bad.append(ln)
            continue
        t = "%02d:%s" % (int(m.group(1)), m.group(2))
        rows.append((t, m.group(3).strip()))
        seen.setdefault(t, []).append(m.group(3).strip())
    rows.sort()
    clash = {t: v for t, v in seen.items() if len(v) > 1}
    return rows, clash, bad


def breakeven(machine_won, monthly_cost_won, saved_per_month_won):
    """장비값을 월 절감액에서 월 운영비를 뺀 값으로 나눈 손익분기 개월(가정값)."""
    net = saved_per_month_won - monthly_cost_won
    if net <= 0:
        return None, net
    return machine_won / net, net


def api(params):
    p = params or {}
    need_app = _yn(p.get("need_app"))
    phone_only = _yn(p.get("phone_only"))
    login_sensitive = _yn(p.get("login_sensitive"))
    multi_model = _yn(p.get("multi_model"))
    is_dev = _yn(p.get("is_dev"))
    pc = str(p.get("pc_spec", "보통")).strip()
    budget = str(p.get("budget", "무료")).strip()
    speed_first = _yn(p.get("speed_first"))
    if pc not in ("낮음", "보통", "높음"):
        return {"ok": False, "text": "PC 사양은 낮음/보통/높음 중 하나로 적어 주세요."}
    if budget not in ("무료", "상관없음"):
        return {"ok": False, "text": "예산은 무료/상관없음 중 하나로 적어 주세요."}
    res = score_agents(need_app, phone_only, login_sensitive, multi_model, is_dev, pc != "낮음", budget, speed_first)
    ok_list = sorted([(s, k) for k, (b, s, r) in res.items() if b is None], reverse=True)
    out = ["■ 1. 누구를 고용할까 (점수는 영상 발언을 옮긴 경험칙, 100점 만점)"]
    if not ok_list:
        out.append("조건에 맞는 에이전트가 없다. 조건을 완화해 보자.")
    for i, (s, k) in enumerate(ok_list, 1):
        a = AGENTS[k]
        out.append("%d위 %s — %d점 (일하는 곳: %s, 속도: %s, 영상 %s)" % (i, a["name"], s, a["where"], a["speed"], a["src"]))
        out.append("   장점: " + a["pros"])
        out.append("   단점: " + a["cons"])
        if res[k][2]:
            out.append("   점수 이유: " + ", ".join(res[k][2]))
    blocked = [(k, b) for k, (b, s, r) in res.items() if b]
    if blocked:
        out.append("불가: " + " / ".join("%s: %s" % (AGENTS[k]["name"], b) for k, b in blocked))
    if len(ok_list) >= 2:
        out.append("영상의 조언: 하나만 고용해도 되고 여러 명을 고용해도 된다. 상위 1~2개만 직접 실험해 보자.")

    pr, gaps = ig_prompt(str(p.get("account", "")).strip(), str(p.get("post_url", "")).strip(),
                         str(p.get("keyword", "CODE")).strip(), str(p.get("reply", "")).strip(), str(p.get("dm", "")).strip())
    out.append("\n■ 2. 인스타그램 댓글 자동화 지시문 (영상 실습: 'CODE' 댓글 → 답글 + DM)")
    out.append(pr)
    if gaps:
        out.append("빠진 칸: " + "; ".join(gaps))
    out.append("주의: 자동 댓글·DM은 서비스 이용정책과 스팸 기준에 걸릴 수 있다(영상 설명란 취지, 숫자는 없음). 처음엔 소수 계정으로 시험하자.")

    out.append("\n■ 3. 에이전트를 여럿 쓸 때 공유 파일 규칙 (영상 23:29)")
    out.append(handoff_rules([x.strip() for x in str(p.get("team", "Claude,ChatGPT,안티그래비티")).split(",")],
                             str(p.get("shared_path", "바탕화면/공유대화.txt")).strip() or "바탕화면/공유대화.txt"))

    rows, clash, bad = routine_table(p.get("routines", ""))
    out.append("\n■ 4. 내 하루 루틴표 (영상 후반: 일상 적용부터 연습)")
    for t, w in rows:
        out.append("  %s  %s" % (t, w))
    if not rows:
        out.append("  (입력한 루틴이 없다)")
    for t, v in clash.items():
        out.append("  경고: %s 에 %d개가 겹친다: %s" % (t, len(v), " / ".join(v)))
    for b in bad:
        out.append("  형식 오류(HH:MM|할 일): " + b)

    machine = _num(p.get("machine_won", 10000000), 10000000)
    run = _num(p.get("monthly_cost_won", 300000), 300000)
    saved = _num(p.get("saved_won", 2500000), 2500000)
    months, net = breakeven(machine, run, saved)
    out.append("\n■ 5. 전용 컴퓨터(영상: 맥 스튜디오 약 1천만 원) 손익분기 — 모두 가정값")
    out.append("  장비 %s원, 월 운영비 %s원, 월 절감 인건비 %s원 → 월 순이익 %s원" % (
        format(int(machine), ","), format(int(run), ","), format(int(saved), ","), format(int(net), ",")))
    out.append("  손익분기: " + ("약 %.1f개월" % months if months else "월 절감이 운영비보다 작아 회수되지 않는다"))
    out.append("  (영상은 '인건비를 대체한다'고 말하지만 절감액 숫자는 주지 않았다. 내 값으로 바꿔 보자.)")
    return {"ok": True, "text": "\n".join(out), "ranking": [AGENTS[k]["name"] for s, k in ok_list],
            "scores": {AGENTS[k]["name"]: s for s, k in ok_list}}


if __name__ == "__main__":
    r = api({"login_sensitive": "Y", "multi_model": "Y", "is_dev": "Y", "pc_spec": "높음", "budget": "무료",
             "account": "@my_account", "post_url": "https://www.instagram.com/p/EXAMPLE/", "keyword": "CODE",
             "dm": "프롬프트 파일 링크: (여기에)", "routines": "10:00|운동 영상 찾아서 보내기\n12:00|명상 음악 보내기\n12:00|점심 식당 찾기\n25:00|오류"})
    assert r["ok"], r
    assert r["ranking"][0].startswith("에고라이트"), r["ranking"]
    assert "CODE" in r["text"] and "12:00 에 2개" in r["text"] and "형식 오류" in r["text"]
    r2 = api({"need_app": "Y"})
    assert r2["ranking"] == ["컴퓨터 유즈"], r2["ranking"]
    r3 = api({"phone_only": "Y"})
    assert set(r3["ranking"]) == {"뮤즈(Muse, 메타)", "피클(Pickle)"}, r3["ranking"]
    print(r["text"])
    print("성공")
