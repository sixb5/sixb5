"""Prepare a high-contrast grayscale image on white for ASCII conversion."""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

try:
    from .common import ROOT
except ImportError:
    from common import ROOT


def prepare_photo(source, remove_background=False, clip_limit=2.0):
    image = ImageOps.exif_transpose(Image.open(source)).convert('RGBA')
    if remove_background:
        try:
            from rembg import remove
        except ImportError as error:
            raise ValueError('Install scripts/requirements-background.txt for --remove-background.') from error
        image = remove(image).convert('RGBA')
    alpha = image.getchannel('A')
    bounds = alpha.getbbox()
    if bounds and alpha.getextrema()[0] == 0:
        image = image.crop(bounds)
        alpha = image.getchannel('A')
    gray = np.asarray(ImageOps.grayscale(image))
    enhanced = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8)).apply(gray)
    # Composite AFTER contrast enhancement so transparent background stays pure white.
    subject = Image.fromarray(enhanced).convert('RGBA')
    subject.putalpha(alpha)
    white = Image.new('RGBA', image.size, 'white')
    white.alpha_composite(subject)
    # Near-white backgrounds otherwise become dotted ASCII noise. Stretch the
    # grayscale range after compositing so its light endpoint is exactly white.
    contrasted = ImageOps.autocontrast(white.convert('L'), cutoff=(1, 1))
    return ImageOps.expand(contrasted, border=max(1, image.width // 32), fill=255)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'source-prepped.png')
    parser.add_argument('--remove-background', action='store_true', help='Use optional rembg; first run downloads its model')
    parser.add_argument('--clip-limit', type=float, default=2.0)
    args = parser.parse_args()
    if not 0 < args.clip_limit <= 10:
        parser.error('--clip-limit must be between 0 and 10')
    try:
        image = prepare_photo(args.source, args.remove_background, args.clip_limit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Photo preparation failed: {error}\n')
    print(f'Prepared {args.output} ({image.width} x {image.height}, grayscale).')


if __name__ == '__main__':
    main()
