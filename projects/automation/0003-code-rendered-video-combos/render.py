"""영상 바이브코딩 흉내: 장면(3D 점 모델)을 한 번 만들고, 카메라만 돌려 프레임을 렌더해 GIF로 저장.
매일 다른 조합(모자x캐릭터x신발)을 날짜로 고르는 부분도 포함. 블렌더/유료 API 없이 numpy+Pillow만 사용."""
import datetime as dt
import itertools
import math
import numpy as np
from PIL import Image, ImageDraw

W = H = 200
HATS = ["빨강", "파랑", "초록"]
CHARS = ["토끼", "고양이", "강아지"]
SHOES = ["운동화", "장화"]

def daily_combo(day: dt.date):
    combos = list(itertools.product(HATS, CHARS, SHOES))   # 3*3*2 = 18가지
    return combos[day.toordinal() % len(combos)]

def scene(hat):
    """장면: 바닥 격자 + 공(구 표면 점). 한 번 만들어 두고 계속 재사용한다."""
    pts, cols = [], []
    for x in range(-5, 6):
        for z in range(-5, 6):
            pts.append((x * 0.4, 0.0, z * 0.4)); cols.append((90, 90, 100))
    ball = {"빨강": (230, 40, 40), "파랑": (40, 80, 230), "초록": (40, 180, 70)}[hat]
    for a in np.linspace(0, math.pi, 14):
        for b in np.linspace(0, 2 * math.pi, 24):
            pts.append((0.5 * math.sin(a) * math.cos(b), 0.5 + 0.5 * math.cos(a), 0.5 * math.sin(a) * math.sin(b)))
            cols.append(ball)
    return np.array(pts), cols

def render_frame(pts, cols, angle):
    cam = np.array([3.2 * math.cos(angle), 1.6, 3.2 * math.sin(angle)])
    fwd = np.array([0, 0.5, 0]) - cam; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    rel = pts - cam
    x, y, z = rel @ right, rel @ up, rel @ fwd
    img = Image.new("RGB", (W, H), (20, 24, 40)); d = ImageDraw.Draw(img)
    order = np.argsort(-z)                          # 먼 점부터 그린다
    for i in order:
        if z[i] <= 0.1: continue
        sx, sy = W / 2 + x[i] / z[i] * 170, H / 2 - y[i] / z[i] * 170
        r = max(1, int(5 / z[i]))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=cols[i])
    return img

def render_gif(path, hat, frames=24):
    pts, cols = scene(hat)
    imgs = [render_frame(pts, cols, 2 * math.pi * k / frames) for k in range(frames)]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=80, loop=0)
    return imgs


def api(params=None):
    """params: {"date": "2026-11-12"} -> 그날의 조합과 GIF(base64)를 돌려준다."""
    import base64, io
    day = dt.date.fromisoformat((params or {}).get("date", "2026-11-12"))
    hat, char, shoes = daily_combo(day)
    pts, cols = scene(hat)
    imgs = [render_frame(pts, cols, 2 * math.pi * k / 12) for k in range(12)]
    buf = io.BytesIO()
    imgs[0].save(buf, format="GIF", save_all=True, append_images=imgs[1:], duration=80, loop=0)
    diff = int(np.abs(np.array(imgs[0]).astype(int) - np.array(imgs[3]).astype(int)).sum())
    return {"ok": diff > 1000, "date": day.isoformat(), "combo": {"hat": hat, "character": char, "shoes": shoes},
            "frames": len(imgs), "frame_diff": diff, "gif_base64": base64.b64encode(buf.getvalue()).decode()}

if __name__ == "__main__":
    today = dt.date(2026, 11, 12)
    hat, char, shoes = daily_combo(today)
    print("오늘의 조합:", hat, "모자 /", char, "/", shoes)
    imgs = render_gif("orbit.gif", hat)
    # 확인: 프레임 수, 카메라가 돌면서 프레임이 실제로 달라지는지
    a, b = np.array(imgs[0]).astype(int), np.array(imgs[6]).astype(int)
    diff = int(np.abs(a - b).sum())
    print("프레임 수:", len(imgs), "/ 0번과 6번 프레임 차이:", diff)
    days = {daily_combo(today + dt.timedelta(days=i)) for i in range(18)}
    print("18일 동안 서로 다른 조합 수:", len(days))
    assert len(imgs) == 24 and diff > 1000 and len(days) == 18
    print("성공")
