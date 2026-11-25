from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from post_renderer import CAM_X, CAM_Y, TOP, crop_aspect, valid_webcam, write_art, write_words
from studio import local_original, read_profile, save_profile


class SetupTest(unittest.TestCase):
    def test_preview_keeps_gameplay_full_height_with_or_without_webcam(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            avatar = folder / "avatar.png"
            Image.new("RGB", (100, 100), "yellow").save(avatar)
            still = Image.new("RGB", (1920, 1080), "blue")
            ImageDraw.Draw(still).rectangle((0, 124, 461, 423), fill="red")
            profile = dict(avatar=str(avatar), name="Creator", handle="@creator")
            args = SimpleNamespace(title="A surpresa no jogo", streamer="@streamer", badge="GTA 6",
                                   cover_title="QUE SURPRESA")
            font = ImageFont.load_default(size=24)
            for cam in (None, (0, 124, 462, 300)):
                with self.subTest(webcam=bool(cam)), patch("post_renderer.ImageFont.truetype", return_value=font):
                    write_art(folder, profile, args, still, cam, (650, 0, 720, 1080), 220 if cam else 0, folder)
                    with Image.open(folder / "preview.png") as preview:
                        self.assertEqual(preview.size, (1080, 1920))
                        for xy in ((500, TOP), (500, 1919), (0, 1200), (1079, 1200)):
                            self.assertEqual(preview.getpixel(xy), (0, 0, 255, 255))
                        expected = (255, 0, 0, 255) if cam else (0, 0, 255, 255)
                        self.assertEqual(preview.getpixel((CAM_X + 30, CAM_Y + 30)), expected)

    def test_profile_and_import_use_isolated_unicode_media_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            photo = root / "foto.png"
            Image.new("RGB", (90, 130), "purple").save(photo)
            media = root / "Vídeos de ação"
            state = root / "local"
            cfg = save_profile(state, name="Testé", handle="@teste", avatar=photo,
                               media_dir=media, engine=root / "engine")
            self.assertEqual(read_profile(state), cfg)
            self.assertEqual(cfg["handle"], "@teste")
            self.assertTrue(Path(cfg["avatar"]).is_file())
            src = root / "Vídeo original.mp4"
            src.write_bytes(b"synthetic")
            dst = local_original(src, cfg)
            self.assertEqual(dst.read_bytes(), src.read_bytes())
            self.assertEqual(dst.parent, media)
            with self.assertRaises(FileExistsError):
                local_original(src, cfg)

    def test_languages_and_bounds(self):
        self.assertEqual(crop_aspect((0, 0, 1920, 1080), 1), (420, 0, 1080, 1080))
        self.assertIsNone(valid_webcam(None, 1920, 1080))
        with self.assertRaises(ValueError):
            valid_webcam("1900,0,90,90", 1920, 1080)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "words.json"
            output = folder / "captions.ass"
            source.write_text(
                '[{"text":"Olá","start":0.1,"end":0.4,"language":"pt"},'
                '{"text":"Hello","start":0.6,"end":0.9,"language":"en"}]', encoding="utf-8"
            )
            write_words(output, source, 1)
            captions = output.read_text(encoding="utf-8")
            self.assertIn("OLÁ", captions)
            self.assertNotIn("HELLO", captions)
