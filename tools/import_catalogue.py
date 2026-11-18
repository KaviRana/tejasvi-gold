"""Import makers' PDF catalogues into the website, deterministically.

For each PDF listed in tools/data/catalogue_sources.json:
  1. pull the original photo out of every page (pdfimages, no re-rendering)
  2. read the weight printed on the photo with OCR, using the label style set for that PDF
  3. give each page a permanent design code (kept in src/data/catalogue_codes.json)
  4. save a web-size JPEG to public/designs/<code>.jpg
  5. write tools/data/catalogue_review.csv and src/data/designs.json

Nothing is guessed silently. A weight is used only when OCR finds exactly one plausible
value; otherwise the row is marked "review". Fix a row by typing the weight in weight_g and
setting status to "checked", then run the script again. Only "auto" and "checked" rows go live.

Needs: poppler (pdfimages), tesseract, python3 with Pillow and numpy.
Run from the repo root:  python3 tools/import_catalogue.py
"""
from __future__ import annotations
import csv, hashlib, io, json, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "tools", "data", "catalogue_sources.json")
CODES = os.path.join(ROOT, "src", "data", "catalogue_codes.json")
REVIEW = os.path.join(ROOT, "tools", "data", "catalogue_review.csv")
DESIGNS = os.path.join(ROOT, "src", "data", "designs.json")
IMG_DIR = os.path.join(ROOT, "public", "designs")
OVERRIDES = os.path.join(ROOT, "tools", "data", "photo_overrides")  # <code>.png or .jpg: a hand-picked photo used instead
FIRST_CODE = 1001
WEB_SIDE = 1200
POOR_PHOTO = 40  # border_mismatch above this keeps a photo off the site
RANGES = {"ladies-ring": (0.8, 15), "gents-ring": (2, 40), "engagement-set": (2, 40), "necklace": (3, 150),
          "mangalsutra": (2, 80), "earring": (0.5, 40), "bracelet": (2, 80), "pendant": (0.5, 30), "bangle": (3, 150)}
WEIGHT_WITH_PREFIX = re.compile(r"[Ww][Tt]?\s*[-:.]?\s*(\d{1,3}\s?[.,]\s?\d{1,3})(?![\d])")
WEIGHT_ANY = re.compile(r"(?<![\d.,])(\d{1,3}[.,]\d{2,3})(?![\d.,])")
REVIEW_COLS = ["code", "source", "page", "category", "ocr_text", "weight_g", "status", "note"]


def run(cmd: list[str], data: bytes | None = None) -> str:
    return subprocess.run(cmd, input=data, capture_output=True, check=True).stdout.decode(errors="replace")


def tesseract(img: Image.Image, psm: int) -> str:
    buf = io.BytesIO(); img.save(buf, "PNG")
    return run(["tesseract", "stdin", "stdout", "--psm", str(psm)], buf.getvalue())


def page_images(pdf: str, tmp: str) -> dict[int, str]:
    """Largest image on each page -> its extracted file. pdfimages -j keeps JPEGs byte-for-byte."""
    listing = run(["pdfimages", "-list", pdf]).splitlines()[2:]
    run(["pdfimages", "-j", pdf, os.path.join(tmp, "img")])
    files = sorted(f for f in os.listdir(tmp) if f.startswith("img-"))
    best: dict[int, tuple[int, str]] = {}
    for row, fname in zip(listing, files):
        parts = row.split()
        page, w, h = int(parts[0]), int(parts[3]), int(parts[4])
        if page not in best or w * h > best[page][0]:
            best[page] = (w * h, os.path.join(tmp, fname))
    return {p: f for p, (_, f) in sorted(best.items())}


def candidates(text: str) -> list[float]:
    found = WEIGHT_WITH_PREFIX.findall(text) or WEIGHT_ANY.findall(text)
    return sorted({round(float(re.sub(r"\s", "", x).replace(",", ".")), 3) for x in found})


def ocr_burned(gray: Image.Image) -> str:
    s = 1600 / max(gray.size)
    return tesseract(gray.resize((round(gray.width * s), round(gray.height * s))), 11)


def ocr_pill(gray: Image.Image) -> str:
    """White rounded label near the bottom on a dark background."""
    w, h = gray.size
    band = gray.crop((0, int(h * 0.7), w, h))
    a = np.asarray(band) >= 235
    rows = np.where(a.mean(axis=1) > 0.04)[0]
    cols = np.where(a.mean(axis=0) > 0.15)[0]
    if len(rows) == 0 or len(cols) == 0:
        return ""
    box = (int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1)
    return tesseract(band.crop(box), 7)


def ocr_weight(path: str, style: str) -> tuple[str, list[float]]:
    gray = ImageOps.exif_transpose(Image.open(path)).convert("L")
    if style == "burned":
        text = ocr_burned(gray)
    elif style == "pill":
        text = ocr_pill(gray)
    else:  # "tag": maker's small rotated paper tag; OCR is not reliable, so always review
        return "", []
    return " ".join(text.split())[:80], candidates(text)


# ---- photo treatment -------------------------------------------------------
# Rings: find the gold by colour, crop a square around it, even out the background to
# one stone tone (the site's page colour), and paint out the printed weight label.
# Necklaces with a white weight label at the bottom: square crop above the label.
STONE = np.array([250, 249, 247], dtype=float)  # near white, so the gold is what you see

def hsv(im): return np.asarray(im.convert("HSV")).astype(int)
def dilate(mask, r):
    """Square binary dilation in O(N) with an integral image (numpy only)."""
    m=np.pad(mask.astype(np.int32),r+1)
    c=m.cumsum(0).cumsum(1)
    k=2*r+1; H,W=mask.shape
    s=c[k:k+H,k:k+W]-c[0:H,k:k+W]-c[k:k+H,0:W]+c[0:H,0:W]
    return s>0
def crop_box(im):
    """Square around the gold piece, 1.8x its size. None when no gold is found."""
    W,H=im.size
    small=im.resize((W//4,H//4)); x=hsv(small)
    m=(x[...,0]>=12)&(x[...,0]<=40)&(x[...,1]>=80)&(x[...,2]>=60)
    if m.sum()<0.001*m.size: return None
    ys,xs=np.nonzero(m); y0,y1=np.percentile(ys,[1,99]); x0,x1=np.percentile(xs,[1,99])
    cx,cy=(x0+x1)/2*4,(y0+y1)/2*4; side=max(x1-x0,y1-y0)*4*1.8
    side=min(max(side,0.25*min(W,H)),min(W,H))
    l=int(min(max(cx-side/2,0),W-side)); t=int(min(max(cy-side/2,0),H-side))
    return (l,t,l+int(side),t+int(side))


def present(src, size=WEB_SIDE, enlarge=None):
    """enlarge: optional function applied to the raw crop before resizing (see tools/upscale.py)."""
    im=ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    box=crop_box(im)
    if box is None: return None
    crop=im.crop(box)
    if enlarge is not None: crop=enlarge(crop)
    return treat(crop.resize((size,size),Image.LANCZOS))


def treat(crop):
    """Stone background, label text painted out. Same input, same output."""
    a=np.asarray(crop).astype(float); y=hsv(crop)
    border=np.concatenate([a[:40].reshape(-1,3),a[-40:].reshape(-1,3),a[:,:40].reshape(-1,3),a[:,-40:].reshape(-1,3)])
    a=np.clip(a*(STONE/np.maximum(np.median(border,axis=0),1)),0,255)
    gold=(y[...,0]>=10)&(y[...,0]<=42)&(y[...,1]>=60)&(y[...,2]>=90)
    protect=dilate(gold, 60)
    # Printed weights (dark text) and white label boxes away from the piece are painted out.
    label=(y[...,2]>=242)&(y[...,1]<=22)
    text=((y[...,2]<70)|label)&~protect
    text=dilate(text,7)
    if text.any():
        ring=dilate(text,16)&~text&~protect
        fill=np.median(a[ring],axis=0) if ring.any() else STONE
        a[text]=fill
    out=Image.fromarray(a.astype(np.uint8))
    soft=out.filter(ImageFilter.GaussianBlur(3))
    mask=Image.fromarray((dilate(text,4)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))
    return Image.composite(soft,out,mask)


def square_top(src, size=WEB_SIDE):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB"); W, H = im.size
    side = min(W, int(H * 0.86)); left = (W - side) // 2
    return im.crop((left, 0, left + side, side)).resize((size, size), Image.LANCZOS)


def override_for(code: str) -> str | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(OVERRIDES, code + ext)
        if os.path.exists(p): return p
    return None


def override_jpeg(src: str, dst: str) -> None:
    """A hand-picked photo: centre square, 1200 px. Always rewritten, so a new override takes effect."""
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB"); W, H = im.size; s = min(W, H)
    im = im.crop(((W - s) // 2, (H - s) // 2, (W - s) // 2 + s, (H - s) // 2 + s)).resize((WEB_SIDE, WEB_SIDE), Image.LANCZOS)
    im.save(dst, "JPEG", quality=86, optimize=True, progressive=True)


def web_jpeg(src: str, dst: str, style: str) -> float:
    out = square_top(src) if style == "pill" else present(src)
    if out is None:  # no gold found: keep the photo, just resized
        out = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        s = min(1.0, WEB_SIDE / max(out.size))
        if s < 1:
            out = out.resize((round(out.width * s), round(out.height * s)), Image.LANCZOS)
    # A photo already on disk is kept, so upscaled photos survive a re-import. Delete it to redo it.
    if not os.path.exists(dst):
        out.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
    return border_mismatch(out) if style != "pill" else 0.0


def border_mismatch(img) -> float:
    """Median distance of the frame's edge pixels from the stone tone. Clean product shots
    score under 25; photos with a hand, tag or busy background score 60+."""
    a = np.asarray(img.convert("RGB")).astype(float)
    dist = np.abs(a - STONE).sum(-1)
    edge = np.concatenate([dist[:60].ravel(), dist[-60:].ravel(), dist[:, :60].ravel(), dist[:, -60:].ravel()])
    return float(np.median(edge))


def load_json(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def main() -> None:
    sources = load_json(SOURCES, [])
    codes: dict[str, str] = load_json(CODES, {})
    old_review = {}
    if os.path.exists(REVIEW):
        with open(REVIEW, encoding="utf-8") as f:
            old_review = {r["code"]: r for r in csv.DictReader(f)}
    os.makedirs(IMG_DIR, exist_ok=True)
    next_no = max([int(c[3:]) for c in codes.values()] + [FIRST_CODE - 1]) + 1
    seen_hash: dict[str, str] = {}
    review_rows, live = [], []

    for src in sources:
        pdf = os.path.join(ROOT, src["file"])
        if not os.path.exists(pdf):
            sys.exit(f"missing catalogue: {src['file']}")
        lo, hi = RANGES.get(src["category"], (0.5, 200))
        with tempfile.TemporaryDirectory() as tmp:
            for page, path in page_images(pdf, tmp).items():
                key = f"{src['source']}:{page}"
                if key not in codes:
                    codes[key] = f"TG-{next_no}"; next_no += 1
                code = codes[key]
                digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
                if digest in seen_hash:
                    review_rows.append(dict(code=code, source=src["source"], page=page, category=src["category"], ocr_text="",
                                            weight_g="", status="duplicate", note=f"same photo as {seen_hash[digest]}"))
                    continue
                seen_hash[digest] = code
                ov = override_for(code)
                if ov:
                    override_jpeg(ov, os.path.join(IMG_DIR, f"{code}.jpg")); mismatch = 0.0
                else:
                    mismatch = web_jpeg(path, os.path.join(IMG_DIR, f"{code}.jpg"), src["label"])
                prev = old_review.get(code)
                # A weight once read or typed is kept: OCR versions differ between machines, so it is not re-read.
                if prev and prev.get("status") in ("checked", "auto") and prev.get("weight_g"):
                    row = dict(prev); row.update(page=page, source=src["source"], category=src["category"])
                else:
                    text, cands = ocr_weight(path, src["label"])
                    ok = [c for c in cands if lo <= c <= hi]
                    if len(ok) == 1:
                        row = dict(code=code, source=src["source"], page=page, category=src["category"], ocr_text=text,
                                   weight_g=f"{ok[0]:g}", status="auto", note="")
                    else:
                        note = "label is a maker's tag; type the weight" if src["label"] == "tag" else \
                               ("no weight found" if not ok else f"several readings: {ok}")
                        row = dict(code=code, source=src["source"], page=page, category=src["category"], ocr_text=text,
                                   weight_g="", status="review", note=note)
                if mismatch > POOR_PHOTO and row["status"] != "checked":
                    row.update(status="poor-photo", note="hand, tag or busy background in the photo; ask the maker for a better one")
                review_rows.append(row)
                if row["status"] in ("auto", "checked") and row["weight_g"]:
                    wgt = float(row["weight_g"])
                    entry = dict(id=code, category=src["category"], weight_min_g=wgt, weight_max_g=wgt,
                                 status="made-to-order", added=src["added"])
                    if src.get("purity", "22K") != "22K": entry["purity"] = src["purity"]  # 22K and /designs/<code>.jpg are defaults
                    live.append(entry)

    json.dump(dict(sorted(codes.items(), key=lambda kv: int(kv[1][3:]))), open(CODES, "w", encoding="utf-8"), indent=2)
    review_rows.sort(key=lambda r: int(r["code"][3:]))
    with open(REVIEW, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_COLS, extrasaction="ignore"); w.writeheader(); w.writerows(review_rows)
    # Keep hand-added designs that are not samples and not from catalogues; replace everything imported.
    imported = set(codes.values())
    keep = [d for d in load_json(DESIGNS, []) if not d.get("sample") and d["id"] not in imported]
    live.sort(key=lambda d: int(d["id"][3:]))
    json.dump(keep + live, open(DESIGNS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    n = {s: sum(1 for r in review_rows if r["status"] == s) for s in ("auto", "checked", "review", "duplicate", "poor-photo")}
    print(f"pages: {len(review_rows)} | live: {len(live)} | auto: {n['auto']} | checked: {n['checked']} | "
          f"to review: {n['review']} | poor photos: {n['poor-photo']} | duplicates: {n['duplicate']}")
    print(f"review sheet: {os.path.relpath(REVIEW, ROOT)}")


if __name__ == "__main__":
    main()
