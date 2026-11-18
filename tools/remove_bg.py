"""Cut photos out of their background with an open-source model, so each piece sits on the page with no tinted box.

Model: ISNet (isnet-general-use) through rembg. The code is MIT and the model Apache-2.0, so it is fine on a business
site. It keeps the holes in bangles and wires see-through, which U2-Net filled in (tested on TG-1379 and TG-1395).
Do not swap in BRIA RMBG: its weights are not licensed for commercial use.

Source for each design code, first one found:
  tools/data/photo_overrides/<code>.png|jpg|webp   your enhanced photo, with its background
  public/designs/<code>.jpg                   the catalogue photo
Writes working/cutouts/<code>.png (not committed): transparent, the piece fitted into a 1200 x 1200 square with the same margin
on every photo, so pieces look the same size in the grid. An enhanced photo also replaces public/designs/<code>.jpg with
the piece on white (search engines and old links use that file).

  python3 tools/remove_bg.py              only the photos in tools/data/photo_overrides
  python3 tools/remove_bg.py --all        every live design
  python3 tools/remove_bg.py TG-1379      only these codes
A code is skipped when its cutout is newer than its source, so running it again is quick.
Then run:  python3 tools/thumbs.py,  python3 tools/share_cards.py  and  python3 tools/previews.py
Needs:  pip3 install rembg onnxruntime pillow   (the model, 170 MB, downloads once)
"""
import json, os, sys
from PIL import Image

CANVAS, FILL = 1200, 0.84  # the piece's longer side takes 84% of the square
OVERRIDES, PUBLIC, OUT = "tools/data/photo_overrides", "public/designs", "working/cutouts"
MODEL = "isnet-general-use"


def override(code):
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = f"{OVERRIDES}/{code}.{ext}"
        if os.path.exists(p): return p


def fit(cut):
    """Crop to the piece and centre it in the square. Resized premultiplied, so edges get no dark or white fringe."""
    box = cut.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box: return None
    cut = cut.crop(box).convert("RGBa")
    scale = CANVAS * FILL / max(cut.size)
    cut = cut.resize((max(1, round(cut.width * scale)), max(1, round(cut.height * scale))), Image.LANCZOS).convert("RGBA")
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    out.paste(cut, ((CANVAS - cut.width) // 2, (CANVAS - cut.height) // 2))
    return out


def main(argv):
    live = [d["id"] for d in json.load(open("src/data/designs.json"))]
    if "--all" in argv: codes = live
    elif [a for a in argv if a.startswith("TG-")]: codes = [a for a in argv if a.startswith("TG-")]
    else: codes = [c for c in live if override(c)]
    if not codes:
        print("nothing to do: put enhanced photos in tools/data/photo_overrides, or use --all"); return
    from rembg import new_session, remove  # imported late so --help style errors stay quick
    os.makedirs(OUT, exist_ok=True)
    session, made = None, 0
    for code in codes:
        src = override(code) or f"{PUBLIC}/{code}.jpg"
        dst = f"{OUT}/{code}.png"
        if not os.path.exists(src): print(f"{code}: no photo"); continue
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): continue
        session = session or new_session(MODEL)
        cut = fit(remove(Image.open(src).convert("RGB"), session=session))
        if cut is None: print(f"{code}: nothing found in the photo, check it by hand"); continue
        cut.save(dst, optimize=True)
        if override(code):
            white = Image.new("RGB", cut.size, (255, 255, 255)); white.paste(cut, mask=cut.getchannel("A"))
            white.save(f"{PUBLIC}/{code}.jpg", quality=90, optimize=True)
        made += 1; print(f"{code}: cut out")
    # Which designs have a cutout, so the site drops the soft edge fade for exactly those. Committed; the PNGs are not.
    done = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".png") and f.startswith("TG-"))
    json.dump(done, open("src/data/cutouts.json", "w"), indent=0)
    print("cutouts written:", made, "| designs with a cutout:", len(done))


if __name__ == "__main__":
    main(sys.argv[1:])
