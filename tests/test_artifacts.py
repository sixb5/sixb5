"""Verify displayed data, XML safety, static mode and portrait brightness."""
import unittest
from datetime import date, timedelta
from xml.etree import ElementTree as ET

from PIL import Image

from scripts.fetch_contributions import build_payload
from scripts.make_ascii_svg import image_to_rows, render_ascii
from scripts.make_info_card import render_info
from scripts.render_heatmap_svg import render_heatmap

NS = {'s': 'http://www.w3.org/2000/svg'}


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'username': 'sixb5', 'name': 'A & B <C>',
                        'subtitle': 'Code & craft',
                        'rows': [{'label': 'Now', 'value': 'R&D <tools>'}],
                        'footer': 'Hello & goodbye'}
        end = date(2024, 3, 2)  # Saturday: maximal Sunday-aligned 53-week window.
        start = end - timedelta(days=364)
        days = [{'date': (start + timedelta(days=i)).isoformat(),
                 'count': 2 if i == 364 else 0, 'level': 2 if i == 364 else 0}
                for i in range(365)]
        self.payload = build_payload('sixb5', days, end)

    def test_grid_displays_real_days_without_counting_padding(self):
        root = ET.fromstring(render_heatmap(self.payload, static=True))
        tiles = root.findall('.//s:rect[@data-date]', NS)
        self.assertEqual(len(tiles), 365)
        self.assertEqual(sum(int(tile.attrib['data-count']) for tile in tiles), 2)
        self.assertEqual(len({tile.attrib['x'] for tile in tiles}), 53)
        self.assertEqual(len({tile.attrib['y'] for tile in tiles}), 7)
        text = ' '.join(root.itertext())
        self.assertIn('2 contributions in the last year', text)
        self.assertIn('2024-03-02', text)

    def test_static_outputs_have_no_animations_and_escape_user_text(self):
        outputs = [render_heatmap(self.payload, static=True),
                   render_info(self.profile, static=True),
                   render_ascii([' @<& ', ' .:* '], 'sixb5', static=True)]
        for output in outputs:
            root = ET.fromstring(output)
            self.assertEqual(root.findall('.//s:animate', NS), [])
            self.assertNotIn('@keyframes', output)
        self.assertIn('A & B <C>', ''.join(ET.fromstring(outputs[1]).itertext()))
        self.assertIn(' @<& ', ''.join(ET.fromstring(outputs[2]).itertext()))

    def test_white_is_empty_black_is_dense(self):
        # Match physical character-cell aspect; letterboxing is separately intentional.
        self.assertEqual(image_to_rows(Image.new('L', (12, 10), 255), 2, 1), ['  '])
        self.assertEqual(image_to_rows(Image.new('L', (12, 10), 0), 2, 1), ['@@'])

    def test_animations_play_once_with_a_visible_final_frame(self):
        avatar = ET.fromstring(render_ascii([' @@ ', ' @@ '], 'sixb5'))
        animations = avatar.findall('.//s:animate', NS)
        self.assertTrue(animations)
        self.assertTrue(all(a.attrib.get('repeatCount', '1') == '1' for a in animations))
        self.assertIn('@keyframes', render_heatmap(self.payload))
        self.assertIn('both', render_info(self.profile))

    def test_dense_portrait_resolution_does_not_overlap_rows(self):
        root = ET.fromstring(render_ascii(['@@'] * 100, 'sixb5', static=True))
        rows = root.findall('.//s:g/s:text', NS)
        baseline_gap = float(rows[1].attrib['y']) - float(rows[0].attrib['y'])
        self.assertLessEqual(float(rows[0].attrib['font-size']), baseline_gap + .001)


if __name__ == '__main__':
    unittest.main()
