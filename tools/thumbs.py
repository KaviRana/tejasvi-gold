"""Small copies of every live catalogue photo for the grid, so a page of 24 pieces loads fast.

For each design in src/data/designs.json: public/designs/w/<code>-480.webp, -800.webp and -1200.webp (sharp
phones and the design page). The source is working/cutouts/<code>.png when there is one (tools/remove_bg.py), giving transparent
WebP, otherwise public/designs/<code>.jpg. Rebuilt only when the source is newer than its copy, so running it again is
quick and changes nothing. Run from the site root:  python3 tools/thumbs.py
"""
import json, os
from PIL import Image

SIZES = (480, 800, 1200)
OUT = "public/designs/w"


def main():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for d in json.load(open("src/data/designs.json")):
        cut = f"working/cutouts/{d['id']}.png"
        src = cut if os.path.exists(cut) else f"public/designs/{d['id']}.jpg"
        if not os.path.exists(src): continue
        dst = lambda w: f"{OUT}/{d['id']}-{w}.webp"
        todo = [w for w in SIZES if not (os.path.exists(dst(w)) and os.path.getmtime(dst(w)) >= os.path.getmtime(src))]
        if not todo: continue
        im = Image.open(src)  # opened once for all the sizes
        # A cutout is resized premultiplied, so its edge gets no dark or white fringe.
        im = im.convert("RGBa") if src == cut else im.convert("RGB")
        for w in todo:
            r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            if src == cut: r = r.convert("RGBA")
            r.save(dst(w), "WEBP", quality=82, method=4)
            made += 1
    print("thumbnails written:", made)


if __name__ == "__main__":
    main()
