"""커뮤니티 쇼츠 제작 설계기 (영상 zAA7lfTfq-I, money_touch).

영상의 제작 흐름: 사연 -> 대본 -> 장면 나누기(이미지 약 13개) -> 음성(배속·쉼 줄이기) -> 편집 -> 내보내기.
이 도구는 사연 원문(필요하면 각색 대본)을 넣으면
  1) 장면 나누기와 장면별 이미지 프롬프트
  2) 음성 길이 추정(배속·쉼 반영)과 쇼츠 길이 맞춤
  3) 제목 후보 10개(경험칙 틀)
  4) 개인정보·위험 표현 점검
  5) 원문과 각색 대본이 얼마나 비슷한지(그대로 베낌 경고)
  6) 업로드 수 x 조회수 x RPM 수익 시뮬레이션과 영상 속 수치 환산 RPM 비교
를 한 번에 낸다. 글자 수 -> 초 환산, RPM, 제목 틀은 모두 가정·경험칙이다.
표준 라이브러리만 사용(휴대폰 Pyodide 에서 동작), 외부 호출 없음."""
import difflib
import re
from collections import Counter

SAMPLE = ("이사하면서 당근에서 후기가 좋은 입주 청소 업체를 예약했다. 평점은 5.0이었고 가격도 보통보다 비쌌다. "
          "청소가 끝나고 보니 하얀 창틀에 때가 그대로 끼어 있었다. 손가락으로 쓸어 보니 검은 가루가 묻어나왔다. "
          "문틀에는 이사 전에 붙인 테이프도 남아 있었다. 업체에 연락하니 꼼꼼하게 보는 사람이 드물다며 웃었다. "
          "결국 당근에 솔직한 후기를 남겼다. 그러자 업체가 다시 연락해 다시 청소해 줄 테니 글을 지워 달라고 했다. "
          "나는 그 일을 겪고 그 업체를 다시 집에 부르고 싶지 않았다. 후기는 그대로 두었다.")

STOP = set("그리고 그런데 그래서 하지만 그러나 이사 때문에 정말 너무 진짜 그냥 나는 내가 우리 저는 제가 있었다 했다 하는 했던 있는 없는 그것 이것 저것 이번 다시 결국 그러자".split())
TITLES = ["{k} 때문에 벌어진 일, 끝까지 보세요", "{k}, 이래도 되나요?", "{k} 사연, 댓글 반응이 갈렸습니다",
          "{k} 겪고 나서 생긴 습관", "'{k}' 이 한 가지만 확인했어도", "{k}, 나만 이렇게 느낀 걸까요",
          "{k} 후기를 남겼더니 생긴 일", "{k} 사연의 반전", "{k}, 여러분이라면 어떻게 하시겠어요", "{k} 하기 전에 꼭 보세요"]

PII = [("전화번호", re.compile(r"01[016789][- .]?\d{3,4}[- .]?\d{4}")),
       ("이메일", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
       ("주민등록번호 형태", re.compile(r"\d{6}[- ]?[1-4]\d{6}")),
       ("주소 형태", re.compile(r"[가-힣]{2,}(?:시|도)\s?[가-힣]{1,}(?:구|군)\s?[가-힣0-9]+(?:로|길|동)")),
       ("링크", re.compile(r"https?://\S+"))]
RISK = ["욕설", "자살", "죽여", "성폭행", "마약", "불법촬영", "~~로 확인됨", "사실이다"]


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


def sentences(text):
    t = re.sub(r"\s+", " ", (text or "").strip())
    parts = re.split(r"(?<=[.!?…])\s+|\n+", t)
    return [s.strip() for s in parts if s.strip()]


def chars(s):
    return len(re.sub(r"\s", "", s))


def keyword(text):
    words = re.findall(r"[가-힣A-Za-z]{2,}", text or "")
    josa = ("으로", "에서", "에게", "한테", "까지", "부터", "을", "를", "은", "는", "이", "가", "에", "의", "도", "로", "과", "와")
    clean = []
    for w in words:
        for j in josa:
            if w.endswith(j) and len(w) - len(j) >= 2:
                w = w[:-len(j)]
                break
        if w not in STOP:
            clean.append(w)
    c = Counter(clean)
    return (c.most_common(1)[0][0] if c else "이 사연")


def split_scenes(sents, n):
    n = max(1, min(n, len(sents)))
    total = sum(chars(s) for s in sents) or 1
    target = total / n
    scenes, cur, cl = [], [], 0
    for i, s in enumerate(sents):
        cur.append(s)
        cl += chars(s)
        left_sents = len(sents) - i - 1
        left_scenes = n - len(scenes) - 1
        if (cl >= target and left_scenes > 0 and left_sents >= left_scenes) or (left_sents == left_scenes and left_scenes > 0):
            scenes.append(cur)
            cur, cl = [], 0
    if cur:
        scenes.append(cur)
    return scenes


def similarity(story, script):
    a, b = sentences(story), sentences(script)
    if not a or not b:
        return None
    same = 0
    for s in b:
        best = max(difflib.SequenceMatcher(None, s, x).ratio() for x in a)
        if best >= 0.8:
            same += 1
    ratio = same / len(b)
    sh = lambda t: {t[i:i + 5] for i in range(max(1, len(t) - 4))}
    ta, tb = sh(re.sub(r"\s", "", story)), sh(re.sub(r"\s", "", script))
    jac = len(ta & tb) / max(1, len(ta | tb))
    return ratio, jac


def api(params):
    p = params or {}
    story = (p.get("story") or "").strip() or SAMPLE
    script = (p.get("script") or "").strip()
    speed = _num(p.get("speed"), 1.2, 0.5)
    pause = _num(p.get("pause_sec"), 0.2, 0)
    cps = _num(p.get("chars_per_sec"), 6.0, 1)
    n_img = int(_num(p.get("target_images"), 13, 1))
    max_sec = _num(p.get("max_sec"), 60, 5)
    per_day = _num(p.get("uploads_per_day"), 10, 0)
    views = _num(p.get("avg_views"), 20000, 0)
    rpm = _num(p.get("rpm_won"), 160, 0)
    extra = _num(p.get("extra_month"), 0, 0)
    body = script or story
    ss = sentences(body)
    if not ss:
        return {"ok": False, "text": "사연 내용이 비어 있습니다."}
    L = []
    nchar = sum(chars(s) for s in ss)
    sec = nchar / (cps * speed) + pause * len(ss)
    L.append("[음성 길이 추정] 글자 %d자, 문장 %d개, 배속 %.1f배, 문장 사이 쉼 %.1f초" % (nchar, len(ss), speed, pause))
    L.append("  추정 %.0f초 (1배속 %.0f자/초 가정, 실제 음성 엔진에 따라 +-20%% 차이)" % (sec, cps))
    fit = sec <= max_sec
    if fit:
        L.append("  쇼츠 길이 %.0f초 이내: 통과" % max_sec)
    else:
        need = nchar / ((max_sec - pause * len(ss)) * cps) if max_sec > pause * len(ss) else 99
        cut = int(nchar - (max_sec - pause * len(ss)) * cps * speed)
        L.append("  %.0f초 초과 -> 배속 약 %.1f배로 올리거나 약 %d자(문장 %d개 안팎) 줄일 것" % (max_sec, need, max(cut, 0), max(1, round(cut / (nchar / len(ss))))))
    scenes = split_scenes(ss, n_img)
    L.append("")
    L.append("[장면 나누기] 목표 이미지 %d개 -> 실제 %d장면" % (n_img, len(scenes)))
    tot_sec = 0
    for i, sc in enumerate(scenes, 1):
        txt = " ".join(sc)
        c = chars(txt)
        t = c / (cps * speed) + pause * len(sc)
        tot_sec += t
        L.append("  장면%d (%.1f초, %d자): %s" % (i, t, c, txt if len(txt) <= 60 else txt[:58] + "…"))
        L.append("    이미지 프롬프트: 세로 9:16, 사실적 일상 사진 느낌, 얼굴 특정 안 됨 / 장면: %s" % re.sub(r"[.!?…]+$", "", sc[0])[:30])
    L.append("  장면 길이 합계 %.1f초" % tot_sec)
    k = keyword(body)
    L.append("")
    L.append("[제목 후보] 핵심어 '%s' (경험칙 틀 10종, 영상의 16개 공식은 공개되지 않아 대체한 것)" % k)
    L += ["  %d) %s" % (i + 1, t.format(k=k)) for i, t in enumerate(TITLES)]
    flags = []
    for name, rx in PII:
        for m in rx.findall(body):
            flags.append("%s: %s" % (name, m if isinstance(m, str) else m[0]))
    for w in RISK:
        if w in body:
            flags.append("민감 표현: %s" % w)
    L.append("")
    L.append("[개인정보·위험 점검]")
    if flags:
        L += ["  - 발견 " + f for f in flags]
        L.append("  -> 지우거나 바꾼 뒤 올릴 것")
    else:
        L.append("  발견 없음(정규식 점검일 뿐이라 상호명·실명은 사람이 확인)")
    L.append("  원문 출처 표기 / 확인되지 않은 글이면 '확인되지 않음' 문구 / 특정 업체 비방 여부는 사람이 판단 (영상 속 뉴스 사례도 '지급 대상인지 확인되지 않았다'고 밝힘)")
    sim = similarity(story, script) if script else None
    L.append("")
    L.append("[원문과 각색본 비교]")
    if sim is None:
        L.append("  각색 대본이 없어 비교하지 않음. 원문을 그대로 읽으면 저작권 문제가 될 수 있으니 문장을 바꾼 각색 대본을 넣어 보세요.")
        same_ratio = None
    else:
        same_ratio, jac = sim
        warn = "그대로 옮긴 문장이 많음 -> 더 바꿀 것" if same_ratio > 0.3 or jac > 0.4 else "원문과 충분히 다름(저작권 판단이 아니라 문장 유사도 기준)"
        L.append("  원문과 80%% 이상 같은 문장 비율 %.0f%%, 글자 5연속 겹침 %.0f%% -> %s" % (same_ratio * 100, jac * 100, warn))
    month_views = per_day * 30 * views
    rev = month_views / 1000.0 * rpm
    low = month_views / 1000.0 * rpm * 0.5
    L.append("")
    L.append("[수익 시뮬레이션] (가정값, 보장 아님)")
    L.append("  하루 %d편 x 30일 x 편당 평균 %s회 = 월 %s회" % (per_day, "{:,}".format(int(views)), "{:,}".format(int(month_views))))
    L.append("  RPM(천 회당 수익) %s 가정 -> 월 조회수 수익 약 %s (RPM 절반이면 %s)%s" % (won(rpm), won(rev), won(low), (" + 기타 수익 " + won(extra)) if extra else ""))
    ref = 34000000 / 210000000 * 1000
    L.append("  영상 화면 환산: 28일 약 2.1억 회 / 예상 수익 3,400만원 -> RPM 약 %s (자막이 거칠어 숫자 오인 가능)" % won(ref))
    if rpm > ref * 1.5:
        L.append("  입력 RPM이 영상 환산보다 훨씬 높다. 낙관적인 가정이다.")
    claim = 1e7 * 30
    L.append("  '하루 천만 조회 x 월 5천만원' 주장: 월 3억 회라면 RPM %s이어야 한다(조회수 수익만 4천만원이면 %s)." % (won(5e7 / claim * 1000), won(4e7 / claim * 1000)))
    need_d = 4e7 / 30 / (views / 1000.0 * rpm) if views and rpm else 0
    if need_d:
        L.append("  내 가정(편당 %s회, RPM %s)으로 월 4천만원이면 하루 약 %.0f편이 필요하다." % ("{:,}".format(int(views)), won(rpm), need_d))
    L.append("  업로드 수가 늘어도 편당 조회수는 크게 갈린다. 영상 속 3개월 111편 사례도 조회 1백만 이상은 일부였다고 말한다. 2026년 2월 수익화 기준 변경은 영상 발언이며 구체 기준은 직접 확인하라.")
    return {"ok": True, "text": "\n".join(L), "seconds": sec, "fits": fit, "scenes": len(scenes),
            "flags": flags, "same_ratio": same_ratio, "month_revenue": rev, "ref_rpm": ref,
            "note": "가정값 기반 계산이며 수익을 보장하지 않는다. 투자·사업 권유가 아니다."}


if __name__ == "__main__":
    r = api({})
    assert r["ok"] and r["scenes"] >= 5 and r["fits"]
    assert abs(r["ref_rpm"] - 161.9) < 0.5
    print(r["text"])
    print("성공")
