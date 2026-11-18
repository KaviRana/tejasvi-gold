"""Bring every catalogue photo's background to near white (the site's tone), without touching its framing.

Each photo's background colour is measured on its border; every pixel is then scaled per channel so that
background becomes the target. Photos already at the target are left alone, so running it again changes
nothing. Hand-picked photos in tools/data/photo_overrides are skipped. Run from the site root:
    python3 tools/whiten.py
"""
import glob, os
import numpy as np
from PIL import Image

TARGET = np.array([250, 249, 247], dtype=float)


def main():
    overrides = {os.path.splitext(f)[0] for f in os.listdir("tools/data/photo_overrides")}
    changed = 0
    for path in sorted(glob.glob("public/designs/TG-*.jpg")):
        code = os.path.basename(path)[:-4]
        if code in overrides: continue
        a = np.asarray(Image.open(path).convert("RGB")).astype(float)
        border = np.concatenate([a[:30].reshape(-1, 3), a[-30:].reshape(-1, 3), a[:, :30].reshape(-1, 3), a[:, -30:].reshape(-1, 3)])
        bg = np.median(border, axis=0)
        if np.abs(bg - TARGET).max() <= 3: continue
        out = np.clip(a * (TARGET / np.maximum(bg, 1)), 0, 255).astype(np.uint8)
        Image.fromarray(out).save(path, "JPEG", quality=86, optimize=True, progressive=True)
        changed += 1
    print("whitened", changed, "photos")


if __name__ == "__main__":
    main()
