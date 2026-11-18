"""Cut the first pieces of the catalogue out of their stone background, for the hero's spill.

Each cutout keeps the exact framing of its photo in public/designs, so when it lands on its
tile the swap is invisible. Same photos in, same files out. Run from the site root:
    python3 tools/hero_cutouts.py            # the rings listed in HELD
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

N = 12
SIDE = 480
SRC = "public/designs"
OUT = "public/hero/pieces"


def dilate(mask, r):
    m = np.pad(mask.astype(np.int32), r + 1)
    c = m.cumsum(0).cumsum(1)
    k = 2 * r + 1; H, W = mask.shape
    return (c[k:k+H, k:k+W] - c[0:H, k:k+W] - c[k:k+H, 0:W] + c[0:H, 0:W]) > 0


def cutout(path):
    """Gold only: gold-coloured pixels are solid, bright highlights count only right next to gold,
    and the grey background, its shadow and the light inside the ring are dropped."""
    im = Image.open(path).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS)
    hsv = np.asarray(im.convert("HSV")).astype(float)
    h, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    goldish = (h >= 8) & (h <= 45)
    core = goldish & (sat >= 70) & (val >= 60)
    a = goldish * np.clip((sat - 38) / 40, 0, 1) * np.clip((val - 40) / 40, 0, 1)
    shine = dilate(core, 2) & (val >= 205) & (sat >= 22) & (h >= 5) & (h <= 50)   # pale gold highlights, never the white backdrop
    a = np.maximum(a, shine * 0.95)
    a = np.where(dilate(core, 4), a, 0)             # nothing far from the metal survives
    alpha = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    out = im.convert("RGBA"); out.putalpha(alpha)
    return out


def band_point(im):
    """Where fingers would hold the ring: the thinnest part of its upper edge, which is the plain band.
    For every column, measure how thick the gold is going down from its top edge; among columns in the
    middle 70% of the ring whose top edge is in the upper third, take the thinnest (ties: nearest the middle).
    Returned as fractions of the image (x, y)."""
    a = np.asarray(im)[..., 3] > 128
    ys, xs = np.nonzero(a)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    mid = (x0 + x1) / 2
    best = None
    for x in range(int(x0 + 0.15 * (x1 - x0)), int(x1 - 0.15 * (x1 - x0)) + 1):
        col = np.nonzero(a[:, x])[0]
        if not len(col): continue
        top = col[0]
        if top > y0 + (y1 - y0) / 3: continue
        run = 1
        while top + run < a.shape[0] and a[top + run, x]: run += 1
        key = (run, abs(x - mid))
        if best is None or key < best[0]: best = (key, x, top)
    _, x, top = best
    return [round(x / im.width, 4), round((top + 2) / im.height, 4)]


# The rings Kavita chose for her painting, shown in this order.
HELD = ["TG-1001", "TG-1002", "TG-1008", "TG-1023", "TG-1046", "TG-1055"]


def hang_angle(im, band):
    """Degrees to turn the ring (clockwise) so it hangs straight down from its band: after turning,
    the ring's centre of gold lies directly below the band point."""
    a = np.asarray(im)[..., 3].astype(float) / 255
    ys, xs = np.nonzero(a > 0.5)
    cx, cy = xs.mean() / im.width, ys.mean() / im.height
    return round(float(np.degrees(np.arctan2(cx - band[0], cy - band[1]))), 1)


def main():
    os.makedirs(OUT, exist_ok=True)
    done = []
    for code in HELD:
        p = os.path.join(SRC, f"{code}.jpg")
        if not os.path.exists(p): sys.exit(f"missing photo for {code}")
        im = cutout(p)
        im.save(os.path.join(OUT, f"{code}.webp"), "WEBP", quality=82, method=6)
        band = band_point(im)
        done.append({"id": code, "band": band, "hang": hang_angle(im, band)})
    with open("src/data/hero.json", "w") as f:
        json.dump({"pieces": done}, f, indent=2); f.write("\n")
    print("cut", len(done), ", ".join(f"{d['id']} ({d['hang']}°)" for d in done))


if __name__ == "__main__":
    main()
