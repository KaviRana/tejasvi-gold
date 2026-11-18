"""Put a real catalogue bangle on the painted tray, in place of the painted one. Same files in, same picture out.

Run from the site root:  python3 tools/hero_tray.py TG-1383
Reads   without centre with background.png  (Kavita's painting, in the site root)
        public/designs/<code>.jpg           (the catalogue photo)
Writes  public/hero/painting-1920.webp, painting-1280.webp and src/data/tray.json (where the bangle sits, for the link)
"""
import json, sys
import cv2
import numpy as np
from PIL import Image, ImageFilter

PAINTING = "without centre with background.png"
BANGLE = (980, 977, 104, 50)        # painted bangle: centre x, centre y, half-width, half-height (1920 x 1080)
TARGET_W = 216                      # a little wider than the painted one (208 px), so it covers its place


def gold_alpha(rgb):
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV")).astype(float)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    g = (h >= 6) & (h <= 45)
    core = g & (s >= 60) & (v >= 60)
    a = g * np.clip((s - 35) / 40, 0, 1) * np.clip((v - 40) / 40, 0, 1)
    near = cv2.dilate(core.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    a = np.maximum(a, (near & (v >= 200)) * 0.95)        # polished highlights and white-gold accents next to gold
    a = a * (cv2.dilate(core.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
    return cv2.GaussianBlur(a.astype(np.float32), (3, 3), 0)


def flat_bangle(code):
    """Cut the bangle out, turn its long axis level, and lay it down to the tray's angle."""
    rgb = np.asarray(Image.open(f"public/designs/{code}.jpg").convert("RGB"))
    a = gold_alpha(rgb)
    ys, xs = np.nonzero(a > 0.5)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0); cov = np.cov((pts - c).T)
    w, v = np.linalg.eigh(cov); major = v[:, np.argmax(w)]
    ang = np.degrees(np.arctan2(major[1], major[0]))
    rgba = np.dstack([rgb, (a * 255).astype(np.uint8)])
    M = cv2.getRotationMatrix2D((float(c[0]), float(c[1])), ang, 1.0)
    rot = cv2.warpAffine(rgba, M, (rgba.shape[1], rgba.shape[0]), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    ys, xs = np.nonzero(rot[..., 3] > 20)
    rot = rot[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hgt = int(round(TARGET_W * BANGLE[3] / BANGLE[2] * 1.05))
    return cv2.resize(rot, (TARGET_W, hgt), interpolation=cv2.INTER_AREA)


def main():
    code = sys.argv[1] if len(sys.argv) > 1 else "TG-1383"
    base = np.asarray(Image.open(PAINTING).convert("RGB").resize((1920, 1080), Image.LANCZOS)).copy()
    cx, cy, rx, ry = BANGLE
    # 1. Paint the old bangle out of the tray.
    mask = np.zeros(base.shape[:2], np.uint8)
    cv2.ellipse(mask, (cx, cy), (rx + 8, ry + 8), 0, 0, 360, 255, -1)
    clean = cv2.inpaint(base, mask, 9, cv2.INPAINT_TELEA)
    # 2. A soft contact shadow, then the real bangle, warmed slightly to sit in the painting's light.
    b = cv2.GaussianBlur(flat_bangle(code), (0, 0), 0.6).astype(np.float32)   # as soft as the painting
    bh, bw = b.shape[:2]
    x0, y0 = cx - bw // 2, cy - bh // 2
    shadow = np.zeros(base.shape[:2], np.float32)
    cv2.ellipse(shadow, (cx + 6, cy + bh // 2 - 6), (bw // 2, max(8, bh // 5)), 0, 0, 360, 1.0, -1)
    shadow = cv2.GaussianBlur(shadow, (0, 0), 9) * 0.45
    out = clean.astype(np.float32) * (1 - shadow[..., None])
    rgb = b[..., :3] * np.array([1.0, 0.94, 0.82]) * 0.95       # warmer, a touch darker
    al = b[..., 3:] / 255.0
    region = out[y0:y0 + bh, x0:x0 + bw]
    out[y0:y0 + bh, x0:x0 + bw] = rgb * al + region * (1 - al)
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    im.save("public/hero/painting-1920.webp", "WEBP", quality=82, method=6)
    im.resize((1280, 720), Image.LANCZOS).save("public/hero/painting-1280.webp", "WEBP", quality=80, method=6)
    box = {"code": code, "left": round(x0 / 19.2, 2), "top": round(y0 / 10.8, 2), "width": round(bw / 19.2, 2), "height": round(bh / 10.8, 2)}
    json.dump(box, open("src/data/tray.json", "w"), indent=2)
    print(box)


if __name__ == "__main__":
    main()
