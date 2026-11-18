"""A PDF catalogue of chosen designs, to send on WhatsApp or print. Made from the site's own data, so it matches the site.

Six pieces to an A4 page: photo, name, code and weight. Logo and phone number on every page. Sorted by piece type, then code.
Choose what goes in with any of these (they combine):
  --added 2026-11-06            designs added on that date or later
  --category necklace           one type (ladies-ring, gents-ring, necklace, bangle, ...)
  --min-g 10 --max-g 20         weight range in grams
  --codes TG-1379 TG-1428       exactly these
  --title "New necklaces"       the heading on the cover (default is built from the choices)
  --out working/pdfs/name.pdf default working/pdfs/<title>.pdf
Examples:
  python3 tools/catalogue_pdf.py --added 2026-11-06 --title "New designs, 6 November"
  python3 tools/catalogue_pdf.py --category bangle --min-g 8 --max-g 12
Needs: pip3 install reportlab pillow, and node (names come from the site's own code). Run from the site root.
"""
import json, os, re, subprocess, sys
from io import BytesIO
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

W, H, M = 595.28, 841.89, 40
INK, GOLD, LINE = (0.17, 0.13, 0.09), (0.59, 0.44, 0.17), (0.88, 0.86, 0.82)
COLS, ROWS = 2, 3
for w in ("400", "500"): pdfmetrics.registerFont(TTFont(f"EBG{w}", f"tools/assets/fonts/EBGaramond-{w}.ttf"))


def phone_text(n): return f"+{n[:2]} {n[2:7]} {n[7:]}"


def photo(code):
    """The piece on white, 640 px, as JPEG bytes. A cutout is laid on white; a photo is used as it is."""
    cut = f"working/cutouts/{code}.png"
    src = cut if os.path.exists(cut) else f"public/designs/{code}.jpg"
    im = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    im = bg.convert("RGB"); im.thumbnail((640, 640), Image.LANCZOS)
    buf = BytesIO(); im.save(buf, "JPEG", quality=84); buf.seek(0)
    return ImageReader(buf), im.size


def choose(data, a):
    arg = lambda k: a[a.index(k) + 1] if k in a else None
    ds = data["designs"]
    if "--codes" in a:
        i = a.index("--codes") + 1; codes = []
        while i < len(a) and a[i].startswith("TG-"): codes.append(a[i]); i += 1
        ds = [d for d in ds if d["id"] in codes]
    if arg("--added"): ds = [d for d in ds if d["added"] >= arg("--added")]
    if arg("--category"): ds = [d for d in ds if d["category"] == arg("--category")]
    if arg("--min-g"): ds = [d for d in ds if d["max_g"] >= float(arg("--min-g"))]
    if arg("--max-g"): ds = [d for d in ds if d["min_g"] <= float(arg("--max-g"))]
    order = {c["id"]: c["order"] for c in data["categories"]}
    return sorted(ds, key=lambda d: (order.get(d["category"], 99), d["id"]))


def main(a):
    data = json.loads(subprocess.run(["node", "scripts/card-data.mjs"], capture_output=True, check=True).stdout)
    ds = choose(data, a)
    if not ds: sys.exit("no designs match those choices")
    arg = lambda k: a[a.index(k) + 1] if k in a else None
    title = arg("--title") or "Catalogue"
    out = arg("--out") or f"working/pdfs/{re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_')}.pdf"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    logo = ImageReader("tools/assets/logo.png"); lw = 120; lh = lw * 0.4  # logo.png keeps its own ratio, set below
    iw, ih = Image.open("tools/assets/logo.png").size; lh = lw * ih / iw
    c = canvas.Canvas(out, pagesize=(W, H)); c.setTitle(f"Tejasvi Gold, {title}"); c.setAuthor("Tejasvi Gold")
    phone = phone_text(data["phone"])

    def furniture(n, total):
        c.drawImage(logo, M, H - M - lh, lw, lh, mask="auto")
        c.setFillColorRGB(*GOLD); c.setFont("EBG500", 8); c.drawString(M, H - M - lh - 13, "22K WHOLESALE JEWELLERY")
        c.setFillColorRGB(*INK); c.setFont("EBG500", 15); c.drawRightString(W - M, H - M - 12, phone)
        c.setFillColorRGB(*GOLD); c.setFont("EBG400", 10); c.drawRightString(W - M, H - M - 28, title)
        c.setStrokeColorRGB(*LINE); c.setLineWidth(.6); c.line(M, 52, W - M, 52)
        c.setFillColorRGB(*INK); c.setFont("EBG400", 8.5)
        c.drawString(M, 38, data["address"]); c.drawRightString(W - M, 38, f"{n} of {total}")

    # Cover
    c.drawImage(logo, (W - 300) / 2, H - 260, 300, 300 * ih / iw, mask="auto")
    c.setFillColorRGB(*GOLD); c.setFont("EBG500", 12); c.drawCentredString(W / 2, H - 290, "22K WHOLESALE JEWELLERY")
    c.setFillColorRGB(*INK); c.setFont("EBG400", 34); c.drawCentredString(W / 2, H / 2, title)
    c.setFont("EBG400", 15); c.drawCentredString(W / 2, H / 2 - 30, f"{len(ds)} designs, every piece 22K and hallmarked")
    c.setFont("EBG500", 22); c.drawCentredString(W / 2, 150, phone)
    c.setFont("EBG400", 10.5); c.drawCentredString(W / 2, 128, data["address"])
    c.showPage()

    per = COLS * ROWS
    pages = (len(ds) + per - 1) // per
    gx, top, bottom = 20, H - 118, 66
    cw, rh = (W - 2 * M - gx * (COLS - 1)) / COLS, (top - bottom) / ROWS
    for pg in range(pages):
        furniture(pg + 1, pages)
        for k, d in enumerate(ds[pg * per:(pg + 1) * per]):
            col, row = k % COLS, k // COLS
            x, y = M + col * (cw + gx), top - (row + 1) * rh
            box = rh - 44
            img, (pw, ph) = photo(d["id"])
            s = min(cw / pw, box / ph); dw, dh = pw * s, ph * s
            c.drawImage(img, x + (cw - dw) / 2, y + 40 + (box - dh) / 2, dw, dh)
            c.setFillColorRGB(*INK); c.setFont("EBG400", 13); c.drawCentredString(x + cw / 2, y + 24, d["name"])
            c.setFillColorRGB(*GOLD); c.setFont("EBG500", 10.5); c.drawCentredString(x + cw / 2, y + 9, f"{d['id']}   {d['weight']}")
        c.showPage()
    c.save()
    print(f"{out}: {len(ds)} designs, {pages + 1} pages")


if __name__ == "__main__":
    main(sys.argv[1:])
