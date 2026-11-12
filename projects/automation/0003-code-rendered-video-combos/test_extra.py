"""0003 추가 시험: 블렌더(bpy) 실제 렌더. bpy 가 없으면 건너뛴다(pip install bpy)."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    import bpy  # noqa: F401
    HAS_BPY = True
except ImportError:
    HAS_BPY = False


class BlenderTest(unittest.TestCase):
    def test_pure_helpers(self):
        import blender_scene as b
        self.assertEqual(b.frames_for(10, 24), 240)
        self.assertEqual(b.resolution_for(True), (1080, 1920))
        self.assertEqual(b.resolution_for(False), (1920, 1080))

    @unittest.skipUnless(HAS_BPY, "bpy 없음: 블렌더 렌더 시험 건너뜀")
    def test_render_frames_and_cloth_falls(self):
        import blender_scene as b
        import bpy
        sc = b.build(seconds=1, fps=24, vertical=True, percent=5, samples=2)
        cloth = bpy.data.objects["Cloth"]
        for f in range(1, 25):
            sc.frame_set(f)
        lows = cloth.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        self.assertLess(min(v.co.z for v in lows.vertices), -1.0, "천이 떨어지지 않음")
        with tempfile.TemporaryDirectory() as d:
            files = b.render(os.path.join(d, "f_"))
            self.assertEqual(len(files), 24)
            mp4 = b.to_mp4(os.path.join(d, "f_"), 24, os.path.join(d, "o.mp4"))
            if mp4.endswith("o.mp4"):
                self.assertGreater(os.path.getsize(mp4), 1000)
            self.assertEqual(sc.render.resolution_x, 1080)
            self.assertEqual(sc.render.resolution_y, 1920)
