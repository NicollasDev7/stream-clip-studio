"""Run with python -m unittest discover -s tests -p test_render_clip.py."""
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'render_clip', Path(__file__).resolve().parents[1] / 'scripts/render_clip.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class RenderClipTest(unittest.TestCase):
    def test_rejects_out_of_bounds_crop(self):
        with self.assertRaises(ValueError):
            renderer.rect([1200, 0, 200, 200], 1280, 720)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_split_and_full_frame_outputs_preserve_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=size=1280x720:rate=30', '-f', 'lavfi', '-i',
                            'sine=frequency=440:sample_rate=44100', '-t', '2',
                            '-c:v', 'libx264', '-c:a', 'aac', str(source)], check=True)
            for camera in ([0, 0, 320, 240], None):
                job = dict(source=str(source), output=str(root / f'clip-{bool(camera)}.mp4'),
                           duration=1, game=[320, 80, 640, 640], camera=camera)
                result = renderer.render(job)
                self.assertEqual(result['technical_validation'], 'passed')
                self.assertEqual(result['visual_review'], 'pending')
                with self.assertRaises(ValueError):
                    renderer.render(job)


if __name__ == '__main__':
    unittest.main()
