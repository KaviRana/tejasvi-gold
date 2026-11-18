"""Square share cards (1080 x 1080) for WhatsApp, Instagram and editing: public/share/<code>.jpg.

Layout: logo and "22K wholesale jewellery" top left, code and weight top right, the piece in the middle, its name
below it, the phone number bottom right. The piece is working/cutouts/<code>.png when there is one, otherwise
public/designs/<code>.jpg. The name comes from the site's own code (scripts/card-data.mjs).

Built for thousands of designs: a card is redrawn only when its inputs change (name, weight, photo, or the layout
version below), recorded in tools/data/share_manifest.json. Run from the site root:
  python3 tools/share_cards.py              new and changed cards only
  python3 tools/share_cards.py TG-1379      only these codes, always redrawn
Needs: node (for the names), pip3 install pillow. Run  node tools/make_logo.mjs  once for the logo.
"""
import hashlib, json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

VERSION = "2"  # change when the layout changes, so every card is redrawn
S, M = 1080, 64
BG, INK, GOLD = (255, 255, 255), (43, 33, 22), (150, 112, 44)
OUT, MANIFEST = "public/share", "tools/data/share_manifest.json"
TAGLINE = "22K WHOLESALE JEWELLERY"


def font(weight, size): return ImageFont.truetype(f"tools/assets/fonts/EBGaramond-{weight}.ttf", size)


def phone_text(n):  # 919876543210 -> +91 98765 43210
    return f"+{n[:2]} {n[2:7]} {n[7:]}"


def spaced(d, xy, text, f, fill, track=3, anchor="l"):
    """Letter-spaced text; Pillow has no tracking, so draw it letter by letter."""
    widths = [d.textlength(c, font=f) + track for c in text]
    x, y = xy
    if anchor == "r": x -= sum(widths) - track
    for c, w in zip(text, widths): d.text((x, y), c, font=f, fill=fill); x += w


def source_for(code):
    cut = f"working/cutouts/{code}.png"
    return cut if os.path.exists(cut) else f"public/designs/{code}.jpg"


def card(code, name, weight, phone):
    img = Image.new("RGB", (S, S), BG)
    src = source_for(code)
    p = Image.open(src).convert("RGBA")
    box = 640
    k = min(box / p.width, box / p.height)
    p = p.resize((round(p.width * k), round(p.height * k)), Image.LANCZOS)
    img.paste(p, ((S - p.width) // 2, 222 + (box - p.height) // 2), p)
    d = ImageDraw.Draw(img)
    logo = Image.open("tools/assets/logo.png").convert("RGBA")
    lw = 250; logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    img.paste(logo, (M, M), logo)
    spaced(d, (M + 2, M + logo.height + 18), TAGLINE, font("500", 17), GOLD, track=2.4)
    d.text((S - M, M - 6), code, font=font("500", 46), fill=INK, anchor="ra")
    d.text((S - M, M + 52), weight, font=font("400", 36), fill=GOLD, anchor="ra")
    fs = 58
    while d.textlength(name, font=font("400", fs)) > S - 2 * M and fs > 30: fs -= 2
    d.text((S // 2, 902), name, font=font("400", fs), fill=INK, anchor="mm")
    d.text((S - M, S - M + 6), phone_text(phone), font=font("500", 36), fill=INK, anchor="rs")
    return img


def main(argv):
    data = json.loads(subprocess.run(["node", "scripts/card-data.mjs"], capture_output=True, check=True).stdout)
    only = [a for a in argv if a.startswith("TG-")]
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for d in data["designs"]:
        code = d["id"]
        if only and code not in only: continue
        src = source_for(code)
        if not os.path.exists(src): continue
        key = hashlib.sha256(f"{VERSION}|{d['name']}|{d['weight']}|{data['phone']}|{os.path.getmtime(src):.0f}|{src}".encode()).hexdigest()[:16]
        dst = f"{OUT}/{code}.jpg"
        if not only and manifest.get(code) == key and os.path.exists(dst): continue
        card(code, d["name"], d["weight"], data["phone"]).save(dst, quality=86, optimize=True, progressive=True)
        manifest[code] = key; made += 1
    json.dump(dict(sorted(manifest.items())), open(MANIFEST, "w"), indent=0)
    print("share cards written:", made)


if __name__ == "__main__":
    main(sys.argv[1:])
