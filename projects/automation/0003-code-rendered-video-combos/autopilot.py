"""영상 바이브코딩 '오토파일럿' 키트 (영상 Yz3124ulHKE).

영상이 알려 준 방식: 영상을 '생성'하지 않고 3D 장면을 한 번 만들어 두고 매일 카메라·조합만 바꿔 렌더한다.
이 파일이 해 주는 일
  1) 매일 아침 AI(Claude Code·Codex·Antigravity)에게 붙여 넣을 '오토파일럿 프롬프트'를 만든다.
     (장면 파일, 시각, 길이, 화면 크기, 바꿀 것, 절대 바꾸면 안 되는 것, 오늘의 조합)
  2) 모자·캐릭터·장갑·신발처럼 칸별 후보를 곱해 만든 '조합표'에서 날짜별로 다른 조합을 고른다.
  3) 프레임 수(=길이 x fps)와 해상도를 계산한다. 영상은 정지 화면이 이어진 것이기 때문이다.
실제 장면·렌더는 blender_scene.py 가 한다(블렌더 또는 bpy 필요). 이 파일은 표준 라이브러리만 쓴다."""
import datetime
import sys

DEFAULT_POOLS = (
    "모자: 비니, 야구모자, 밀짚모자, 왕관, 마법사모자, 헬멧, 베레모, 두건, 털모자, 모자없음\n"
    "캐릭터: 토끼, 사자, 하마, 강아지, 고양이, 펭귄, 여우, 곰, 판다, 너구리\n"
    "장갑: 털장갑, 권투장갑, 가죽장갑, 야구장갑, 고무장갑, 레이스장갑, 오븐장갑, 면장갑, 방한장갑, 장갑없음\n"
    "신발: 운동화, 장화, 슬리퍼, 부츠, 구두, 샌들, 스케이트, 발레슈즈, 등산화, 맨발"
)
DEFAULT_CHANGES = "조명 방향과 세기\n날씨(맑음·비·노을)\n카메라 경로(회전·전진·크레인)\n오늘 등장하는 캐릭터와 소품"
DEFAULT_KEEPS = "브랜드 로고\n워터마크\n캐릭터 얼굴 모양\n장면 파일의 기본 배치"


def _lines(text):
    return [x.strip() for x in (text or "").splitlines() if x.strip()]


def parse_pools(text):
    pools = []
    for ln in _lines(text):
        name, _, rest = ln.partition(":")
        items = [x.strip() for x in rest.replace("，", ",").split(",") if x.strip()]
        if name.strip() and items:
            pools.append((name.strip(), items))
    return pools


def total_combos(pools):
    n = 1
    for _, items in pools:
        n *= len(items)
    return n


def pick(pools, day_number):
    """날짜 번호 -> 칸별 후보 하나씩. 혼합 진법이라 전체 조합을 다 쓸 때까지 같은 조합이 나오지 않는다."""
    n = day_number % total_combos(pools)
    out = {}
    for name, items in pools:
        out[name] = items[n % len(items)]
        n //= len(items)
    return out


def resolution(orientation, fps=24):
    vertical = str(orientation).strip() in ("세로", "vertical", "v")
    return (1080, 1920) if vertical else (1920, 1080)


def frames(seconds, fps):
    return max(1, int(round(float(seconds) * int(fps))))


def build_prompt(scene, hhmm, seconds, orientation, fps, changes, keeps, today, w, h):
    ch = "\n".join("- " + c for c in changes) or "- (없음)"
    kp = "\n".join("- " + k for k in keeps) or "- (없음)"
    combo = ", ".join(f"{k}: {v}" for k, v in today.items()) or "(조합표 없음)"
    return (
        f"블렌더(MCP 연결 상태)를 사용해 매일 {hhmm}에 새 영상을 만들어 줘.\n"
        f"장면 파일: {scene} (이 파일을 열어서 시작하고, 끝나면 새 이름으로 저장해 원본은 보존)\n"
        f"길이: {seconds}초, {fps}fps (총 {frames(seconds, fps)}프레임), 화면 크기: {w}x{h} ({'세로' if h > w else '가로'})\n"
        "렌더링은 오래 걸리니 밤새 돌려 두고, 아침에 결과 영상 파일 경로를 알려 줘.\n\n"
        f"오늘의 조합: {combo}\n\n"
        f"매일 바꿀 것:\n{ch}\n\n"
        f"절대 바꾸지 말 것:\n{kp}\n\n"
        "작업 순서: 장면 열기 -> 오늘의 조합 적용 -> 카메라 키프레임 설정 -> 미리보기 1장 확인 -> 전체 렌더 -> 저장.\n"
        "막히면 멈추고 이유를 적어 줘. 컴퓨터와 블렌더는 켜져 있어야 해."
    )


def api(params=None):
    """params: {"date","scene","time","seconds","orientation","fps","changes","keeps","pools"} (모두 선택)"""
    p = params or {}
    try:
        d = datetime.date.fromisoformat(str(p.get("date") or "2026-11-12"))
    except ValueError:
        return {"ok": False, "error": "날짜는 2026-11-12 형식으로 입력하세요."}
    try:
        seconds = float(p.get("seconds") or 10)
        fps = int(float(p.get("fps") or 24))
    except ValueError:
        return {"ok": False, "error": "길이(초)와 fps 는 숫자로 입력하세요."}
    if not (0 < seconds <= 600) or not (1 <= fps <= 120):
        return {"ok": False, "error": "길이는 1~600초, fps 는 1~120 사이로 입력하세요."}
    pools = parse_pools(p.get("pools") or DEFAULT_POOLS)
    if not pools:
        return {"ok": False, "error": "조합표는 한 줄에 '칸이름: 후보1, 후보2' 형식으로 입력하세요."}
    day_no = d.toordinal()
    today = pick(pools, day_no)
    total = total_combos(pools)
    w, h = resolution(p.get("orientation") or "세로")
    scene = (p.get("scene") or "my_scene.blend").strip()
    hhmm = (p.get("time") or "08:00").strip()
    prompt = build_prompt(scene, hhmm, seconds, "", fps,
                          _lines(p.get("changes")) or _lines(DEFAULT_CHANGES),
                          _lines(p.get("keeps")) or _lines(DEFAULT_KEEPS), today, w, h)
    tomorrow = pick(pools, day_no + 1)
    summary = (f"[오늘의 조합] {', '.join(f'{k}: {v}' for k, v in today.items())}\n"
               f"[내일] {', '.join(f'{k}: {v}' for k, v in tomorrow.items())}\n"
               f"조합 {total:,}가지(겹치지 않고 {total:,}일). 프레임 {frames(seconds, fps)}장, 크기 {w}x{h}.\n"
               f"렌더 명령: blender -b {scene} -P blender_scene.py -- --out out/frame_ --seconds {seconds:g} --fps {fps}\n\n"
               f"[붙여 넣을 프롬프트]\n{prompt}")
    return {
        "ok": True,
        "text": summary,
        "prompt": prompt,
        "today": today,
        "tomorrow": tomorrow,
        "combos_total": total,
        "days_before_repeat": total,
        "frames": frames(seconds, fps),
        "resolution": [w, h],
        "render_command": f"blender -b {scene} -P blender_scene.py -- --out out/frame_ --seconds {seconds:g} --fps {fps}" + ("" if h > w else " --horizontal"),
        "cost_note": "영상 생성 API 비용 0원: 처음 장면을 만들 때만 토큰이 들고, 이후엔 재사용(영상 설명). 매일은 조합 변경 요청 토큰만 든다.",
    }


if __name__ == "__main__":
    r = api({"date": "2026-11-12"})
    print(r["prompt"])
    print("\n오늘:", r["today"], "| 내일:", r["tomorrow"])
    print("조합 수:", r["combos_total"], "| 프레임:", r["frames"], "| 크기:", r["resolution"])
    pools = parse_pools(DEFAULT_POOLS)
    seen = {tuple(pick(pools, n).items()) for n in range(1000)}
    assert r["ok"] and r["combos_total"] == 10000 and len(seen) == 1000, "1000일 동안 조합이 겹치면 안 됨"
    assert r["today"] != r["tomorrow"] and r["frames"] == 240 and r["resolution"] == [1080, 1920]
    assert api({"date": "내일"})["ok"] is False and api({"seconds": "0"})["ok"] is False
    assert api({"orientation": "가로"})["resolution"] == [1920, 1080]
    print("성공")
    sys.exit(0)
