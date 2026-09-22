import tempfile
import unittest
from pathlib import Path

from PIL import Image

from sender.send import HEIGHT, ROW_BYTES, WIDTH, pack_image


class BitmapTests(unittest.TestCase):
    def test_black_and_white_pixels_use_msb_first(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.png"
            image = Image.new("RGB", (WIDTH, HEIGHT), "white")
            image.putpixel((0, 0), (0, 0, 0))
            image.putpixel((7, 0), (0, 0, 0))
            image.putpixel((8, 0), (0, 0, 0))
            image.putpixel((0, 1), (0, 0, 0))
            image.putpixel((WIDTH - 1, HEIGHT - 1), (0, 0, 0))
            image.save(path)
            bitmap = pack_image(path)
        self.assertEqual(len(bitmap), ROW_BYTES * HEIGHT)
        self.assertEqual(bitmap[:2], bytes((0x81, 0x80)))
        self.assertEqual(bitmap[ROW_BYTES], 0x80)
        self.assertEqual(bitmap[-1], 0x10)

    def test_midtones_print_darker(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gray.png"
            Image.new("RGB", (WIDTH, HEIGHT), (180, 180, 180)).save(path)
            bitmap = pack_image(path)
        black_fraction = sum(byte.bit_count() for byte in bitmap) / (WIDTH * HEIGHT)
        self.assertGreater(black_fraction, 0.38)


if __name__ == "__main__":
    unittest.main()
