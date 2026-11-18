"""Link-preview pictures (1200 x 630) for WhatsApp, Instagram, Google and the like.

public/designs/og/<code>.jpg for every live design: the piece on warm cream, large, with the code and the brand in small
type. public/og-home.jpg for the home page (a row of the newest pieces). The source is working/cutouts/<code>.png when there is
one, otherwise the photo. Rebuilt only when the source is newer. Only the home card is made unless you add --designs (the design pages use the square share cards). Run from the site root:  python3 tools/previews.py
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H, BG, INK, GOLD = 1200, 630, (250, 246, 238), (43, 33, 22), (160, 120, 48)
OUT = "public/designs/og"
FONTS = ["tools/assets/fonts/EBGaramond-400.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/System/Library/Fonts/Supplemental/Georgia.ttf",
         "/System/Library/Fonts/Times.ttc"]


def font(size):
    for f in FONTS:
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def piece(code, box):
    cut = f"working/cutouts/{code}.png"
    src = cut if os.path.exists(cut) else f"public/designs/{code}.jpg"
    if not os.path.exists(src): return None, src
    im = Image.open(src)
    if src != cut:  # a photo with its own background: shrink so its edge blends into the cream
        im = im.convert("RGB")
    else:
        im = im.convert("RGBA")
        im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox())
    s = min(box[0] / im.width, box[1] / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS), src


def card(code, name, weight):
    img = Image.new("RGB", (W, H), BG)
    p, src = piece(code, (760, 560))
    if p is None: return None, src
    x, y = 60 + (760 - p.width) // 2, (H - p.height) // 2
    img.paste(p, (x, y), p if p.mode == "RGBA" else None)
    d = ImageDraw.Draw(img)
    d.text((880, 230), code, font=font(54), fill=INK)
    d.text((880, 300), weight, font=font(30), fill=GOLD)
    d.text((880, 500), "Tejasvi Gold", font=font(28), fill=INK)
    d.text((880, 540), "22K wholesale", font=font(22), fill=GOLD)
    return img, src


def grams(lo, hi):
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    return f"{f(lo)} g" if lo == hi else f"{f(lo)} to {f(hi)} g"


def home():
    """og-home.jpg: five pieces in a row on cream, with the name. Uses the first live designs that have a photo."""
    img = Image.new("RGB", (W, H), BG)
    codes = [d["id"] for d in json.load(open("src/data/designs.json"))]
    codes = [c for c in codes if os.path.exists(f"public/designs/{c}.jpg")][:5]
    for i, c in enumerate(codes):
        p, _ = piece(c, (210, 210))
        if p: img.paste(p, (60 + i * 222 + (210 - p.width) // 2, 90 + (210 - p.height) // 2), p if p.mode == "RGBA" else None)
    d = ImageDraw.Draw(img)
    d.text((60, 380), "Tejasvi Gold", font=font(84), fill=INK)
    d.text((60, 490), "22K hallmarked gold jewellery, wholesale", font=font(34), fill=GOLD)
    d.text((60, 545), "Zaveri Bazaar, Mumbai", font=font(28), fill=INK)
    img.save("public/og-home.jpg", quality=86, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    designs = json.load(open("src/data/designs.json"))
    made = 0
    for dd in (designs if "--designs" in sys.argv else []):  # the design pages now use the square share card, so these are off by default
        dst = f"{OUT}/{dd['id']}.jpg"
        cut = f"working/cutouts/{dd['id']}.png"
        src = cut if os.path.exists(cut) else f"public/designs/{dd['id']}.jpg"
        if not os.path.exists(src): continue
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): continue
        img, _ = card(dd["id"], "", grams(dd["weight_min_g"], dd["weight_max_g"]))
        if img: img.save(dst, quality=84, optimize=True); made += 1
    home()
    print("preview cards written:", made, "+ og-home.jpg")


if __name__ == "__main__":
    main()
