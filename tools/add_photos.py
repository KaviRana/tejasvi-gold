"""Add new pieces from photos that are already cut out (the working/new-photos folder), named by their weight.

A file named 10.500.png is a 10.50 g piece (the trailing zero is ignored). Each new file gets the next design code,
permanently (src/data/manual_photos.json remembers file name -> code, so running again adds nothing twice). For each one:
  - the photo is fitted into a white 1200 x 1200 square and saved as public/designs/<code>.jpg
  - a design is added to src/data/designs.json (category from --category, default necklace; made to order)
  - a row is added to tools/data/tags_review.csv with the name and tags in tools/data/new_piece_tags.json when present
    (status "checked"), otherwise status "suggested" so it is not shown until someone fills it in.
Then run:  python3 tools/thumbs.py   and   python3 tools/previews.py
Run from the site root:  python3 tools/add_photos.py [--category bangle] [--added 2026-11-06]
"""
import csv, datetime, json, os, re, sys
from PIL import Image, ImageOps

SRC, DESIGNS, MANUAL = "working/new-photos", "src/data/designs.json", "src/data/manual_photos.json"
TAGS_IN, REVIEW = "tools/data/new_piece_tags.json", "tools/data/tags_review.csv"
NAME = re.compile(r"^(\d{1,3}\.\d{1,3})\.(png|jpg|jpeg|webp)$", re.I)
SIDE, FILL = 1200, 0.92


def load(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def square(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert("RGB")
    s = SIDE * FILL / max(im.size)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    out = Image.new("RGB", (SIDE, SIDE), (255, 255, 255))
    out.paste(im, ((SIDE - im.width) // 2, (SIDE - im.height) // 2))
    return out


def main(argv):
    arg = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    category, added = arg("--category", "necklace"), arg("--added", datetime.date.today().isoformat())
    designs, manual, tags = load(DESIGNS, []), load(MANUAL, {}), load(TAGS_IN, {})
    nxt = max(int(d["id"][3:]) for d in designs) + 1
    rows = list(csv.DictReader(open(REVIEW, encoding="utf-8"))) if os.path.exists(REVIEW) else []
    cols = ["code", "category", "weight_g", "name", "motif", "finish", "work", "stones", "occasion", "status", "note"]
    new = 0
    for f in sorted(os.listdir(SRC)):
        m = NAME.match(f)
        if not m or f in manual: continue
        weight = round(float(m.group(1)), 2)
        code = f"TG-{nxt}"; nxt += 1
        square(f"{SRC}/{f}").save(f"public/designs/{code}.jpg", quality=88, optimize=True, progressive=True)
        designs.append(dict(id=code, category=category, weight_min_g=weight, weight_max_g=weight, status="made-to-order", added=added))
        t = tags.get(f, {})
        rows.append(dict(code=code, category=category, weight_g=f"{weight:g}", name=t.get("name", ""), motif=t.get("motif", ""),
                         finish=t.get("finish", ""), work=t.get("work", ""), stones=t.get("stones", "None"),
                         occasion=t.get("occasion", ""), status="checked" if t else "suggested", note=f"from {f}"))
        manual[f] = code; new += 1; print(f"{f} -> {code}  {weight:g} g")
    json.dump(designs, open(DESIGNS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(manual, open(MANUAL, "w", encoding="utf-8"), indent=2)
    with open(REVIEW, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print("added:", new)


if __name__ == "__main__":
    main(sys.argv[1:])
