#!/usr/bin/env python3
"""Remove the background from a product photo (optional helper; needs `rembg`).

Usage:
    python cutout.py assets/images/product.png [--out assets/images/product_cutout.png]

Writes a transparent PNG next to the original (never overwrites it) plus two check images
(<name>_check_dark.png, <name>_check_light.png) so the edges can be inspected on both backgrounds.
`rembg` downloads a ~170 MB model on first run. Ask the user before installing it:
    python -m pip install rembg
Alternative: the HyperFrames /media-use skill also offers cut-outs.
"""
import argparse
import importlib.util
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--out")
    a = ap.parse_args()
    if importlib.util.find_spec("rembg") is None:
        sys.exit("rembg is not installed. Ask the user, then: python -m pip install rembg")
    from PIL import Image  # rembg depends on Pillow
    from rembg import remove

    stem, _ = os.path.splitext(a.image)
    out = a.out or f"{stem}_cutout.png"
    if os.path.exists(out):
        sys.exit(f"Refusing to overwrite {out}")
    src = Image.open(a.image).convert("RGBA")
    cut = remove(src)
    cut.save(out)
    for name, colour in (("dark", (18, 18, 22, 255)), ("light", (245, 245, 245, 255))):
        bg = Image.new("RGBA", cut.size, colour)
        bg.alpha_composite(cut)
        bg.convert("RGB").save(f"{stem}_check_{name}.png")
    print(f"wrote {out} (+ check images). Inspect edges before use; record the original's licence in credits.json.")


if __name__ == "__main__":
    main()
