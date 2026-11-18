"""Cut her pinching fingers out of the painting so the held ring can sit between them and the painting.

Kavita's two exports are the same picture with and without the background. Where the "without" image is
white, there is no figure; everywhere else is her hand. The patch takes the painting's own pixels (so the
colours match exactly) and that figure mask as transparency, around the fingertips only.

Run from the site root:  python3 tools/hero_fingers.py
Writes public/hero/fingers.webp and src/data/fingers.json (where the patch sits, as % of the painting).
"""
import json
import numpy as np
from PIL import Image, ImageFilter

WITH = "without centre with background.png"
WITHOUT = "without centre piece without background.png"
BOX = (740, 250, 1010, 500)            # fingertip area in 1920 x 1080 painting pixels


def main():
    paint = Image.open(WITH).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    figure = np.asarray(Image.open(WITHOUT).convert("RGB").resize((1920, 1080), Image.LANCZOS)).astype(float)
    whiteness = figure.min(-1)
    alpha = np.clip((250 - whiteness) / 22, 0, 1)                  # white → clear, hand → solid, soft edge
    a = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    patch = paint.crop(BOX).convert("RGBA"); patch.putalpha(a.crop(BOX))
    patch.save("public/hero/fingers.webp", "WEBP", quality=90, alpha_quality=100, method=6)
    x0, y0, x1, y1 = BOX
    pos = {"left": round(x0 / 19.2, 3), "top": round(y0 / 10.8, 3), "width": round((x1 - x0) / 19.2, 3), "height": round((y1 - y0) / 10.8, 3)}
    json.dump(pos, open("src/data/fingers.json", "w"), indent=2)
    print(pos)


if __name__ == "__main__":
    main()
