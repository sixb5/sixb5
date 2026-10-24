"""A near-white photo background must disappear in the ASCII image."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from scripts.prep_photo import prepare_photo


class PhotoTests(unittest.TestCase):
    def test_near_white_background_maps_to_pure_white_after_contrast(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'photo.png'
            image = Image.new('L', (320, 320), 240)
            ImageDraw.Draw(image).rectangle((80, 80, 240, 240), fill=140)
            image.save(source)
            prepared = prepare_photo(source)
        self.assertEqual(prepared.mode, 'L')
        self.assertEqual(prepared.getpixel((25, 25)), 255)
        self.assertLessEqual(prepared.getpixel((160, 160)), 20)


if __name__ == '__main__':
    unittest.main()
