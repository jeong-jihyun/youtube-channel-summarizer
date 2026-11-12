"""블렌더(bpy) 장면 만들기 + 카메라 360도 렌더.
영상(Yz3124ulHKE)에서 말로 시킨 장면을 코드로 옮긴 것: 반짝이는 빨간 공, 그 위의 무지개,
공 위로 떨어지는 천(물리), 하늘 배경, 공 둘레를 한 바퀴 도는 카메라.

실행 방법
  1) 블렌더 앱: blender -b -P blender_scene.py -- --out out/frame_ --seconds 6 --fps 24
  2) 파이썬 모듈: pip install bpy 한 뒤 python blender_scene.py --out out/frame_
  3) 장면 파일만 저장: --save ball_cloth_rainbow.blend  (영상의 '파일이 곧 자산')

핵심 개념(영상 설명)
  - 영상은 정지 화면(프레임)이 이어진 것: 프레임 수 = 길이(초) x fps.
  - 모델링 -> 애니메이션(키프레임) -> 렌더링 3단계. 장면을 한 번 만들어 저장해 두면 영상 생성 비용 없이 재사용.
  - 재질에 따라 물리가 달라진다(천은 감기고, 쇠는 툭 얹힌다). 아래 CLOTH_STIFFNESS 로 바꿔 볼 수 있다.
"""
import argparse
import math
import os
import sys

RAINBOW = [(1, 0, 0), (1, 0.5, 0), (1, 1, 0), (0, 0.8, 0), (0, 0.3, 1), (0.3, 0, 0.7), (0.6, 0, 0.8)]
CLOTH_STIFFNESS = 5  # 값이 클수록 뻣뻣함(쇠에 가까움). 5=천, 80=두꺼운 판


def frames_for(seconds, fps):
    return max(1, int(round(seconds * fps)))


def resolution_for(vertical):
    return (1080, 1920) if vertical else (1920, 1080)


def _material(bpy, name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def build(seconds=6, fps=24, vertical=True, percent=100, samples=16, with_cloth=True):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    n = frames_for(seconds, fps)
    sc.frame_start, sc.frame_end, sc.render.fps = 1, n, fps

    # 하늘 배경
    w = bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.45, 0.7, 1.0, 1)
    bg.inputs[1].default_value = 1.0

    # 바닥
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    ground.data.materials.append(_material(bpy, "Grass", (0.2, 0.5, 0.2), 0.9))
    ground.modifiers.new("Collision", "COLLISION")

    # 반짝이는 빨간 공 (rough 낮음 = 유리처럼 반짝)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=48, ring_count=24)
    ball = bpy.context.object
    ball.name = "RedBall"
    bpy.ops.object.shade_smooth()
    ball.data.materials.append(_material(bpy, "RedGloss", (0.9, 0.05, 0.05), 0.05))
    ball.modifiers.new("Collision", "COLLISION")

    # 무지개: 색마다 서 있는 고리(아랫부분은 바닥 밑으로 묻혀서 호처럼 보임)
    for i, col in enumerate(RAINBOW):
        bpy.ops.mesh.primitive_torus_add(major_radius=3.0 + i * 0.22, minor_radius=0.11,
                                         location=(0, 3.2, 0), rotation=(math.radians(90), 0, 0))
        t = bpy.context.object
        t.name = "Rainbow%d" % i
        t.data.materials.append(_material(bpy, "R%d" % i, col, 0.4))

    # 천(물리 시뮬레이션): 공 위에서 떨어져 감긴다
    if with_cloth:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=3.2, location=(0, 0, 3.5))
        cloth = bpy.context.object
        cloth.name = "Cloth"
        cloth.data.materials.append(_material(bpy, "ClothMat", (0.95, 0.95, 0.9), 0.8))
        cm = cloth.modifiers.new("Cloth", "CLOTH")
        cm.settings.quality = 5
        cm.settings.tension_stiffness = CLOTH_STIFFNESS
        cm.settings.bending_stiffness = CLOTH_STIFFNESS
        cm.collision_settings.use_collision = True
        cm.collision_settings.distance_min = 0.02
        cm.point_cache.frame_start, cm.point_cache.frame_end = 1, max(n, 60)

    # 조명(해)
    bpy.ops.object.light_add(type="SUN", location=(4, -4, 8))
    bpy.context.object.data.energy = 4.0

    # 카메라: 공 위치의 빈 오브젝트를 축으로 360도 회전 (키프레임)
    bpy.ops.object.empty_add(location=(0, 0, 1.5))
    pivot = bpy.context.object
    pivot.name = "CameraPivot"
    bpy.ops.object.camera_add(location=(0, -9, 3.5))
    cam = bpy.context.object
    cam.parent = pivot
    tr = cam.constraints.new("TRACK_TO")
    tr.target = pivot
    tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    sc.camera = cam
    pivot.rotation_euler[2] = 0
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler[2] = math.radians(360 * (n - 1) / n)  # 마지막 프레임이 첫 프레임과 겹치지 않게
    pivot.keyframe_insert("rotation_euler", index=2, frame=n)
    for fc in pivot.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(
            pivot.animation_data.action, "layers") else pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    # 렌더 설정: 세로 1080x1920 (릴스·쇼츠) 또는 가로 1920x1080 (유튜브)
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = resolution_for(vertical)
    sc.render.resolution_percentage = percent
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"  # 색이 선명하게
    return sc


def render(out_prefix):
    import bpy
    os.makedirs(os.path.dirname(os.path.abspath(out_prefix)), exist_ok=True)
    sc = bpy.context.scene
    sc.render.filepath = out_prefix
    # 천 물리는 프레임을 1장씩 차례로 지나가야 계산된다(건너뛰면 멈춘 채로 렌더됨).
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
    sc.frame_set(sc.frame_start)
    bpy.ops.render.render(animation=True)
    d = os.path.dirname(os.path.abspath(out_prefix))
    base = os.path.basename(out_prefix)
    return sorted(f for f in os.listdir(d) if f.startswith(base) and f.endswith(".png"))


def to_mp4(out_prefix, fps, mp4):
    """프레임 PNG(out_prefix0001.png ...)를 mp4 로 묶는다. ffmpeg 가 없으면 안내만 하고 넘어간다."""
    import shutil
    import subprocess
    if not shutil.which("ffmpeg"):
        return "ffmpeg 가 없어 건너뜀 (설치 후: ffmpeg -framerate %d -i %s%%04d.png -c:v libx264 -pix_fmt yuv420p %s)" % (fps, out_prefix, mp4)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", out_prefix + "%04d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4], check=True)
    return mp4


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/frame_")
    ap.add_argument("--seconds", type=float, default=6)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--horizontal", action="store_true", help="가로 1920x1080 (기본은 세로 1080x1920)")
    ap.add_argument("--percent", type=int, default=100, help="해상도 비율(시험용 10~25)")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--no-cloth", action="store_true")
    ap.add_argument("--mp4", default="", help="렌더가 끝나면 ffmpeg 로 mp4 로 묶기(ffmpeg 필요)")
    ap.add_argument("--save", default="", help="장면을 .blend 파일로 저장(렌더는 건너뜀)")
    a = ap.parse_args(argv)
    import bpy
    build(a.seconds, a.fps, not a.horizontal, a.percent, a.samples, not a.no_cloth)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
        print("저장:", a.save)
        return [a.save]
    files = render(a.out)
    print("렌더 완료:", len(files), "프레임")
    if a.mp4:
        print("mp4:", to_mp4(a.out, a.fps, a.mp4))
    return files


if __name__ == "__main__":
    main()
