"""Upscale catalogue photos with Real-ESRGAN, then give them the usual stone treatment.

Why: the ring fills a small part of each catalogue photo, so its crop is often ~600 px and was
being stretched to 1200 px. Here the crop is enlarged with Real-ESRGAN first.

Deterministic: fixed model weights (checked by SHA-256), fixed scale rule, deterministic torch ops,
fixed thread count. Same PDFs and weights in, same JPEGs out.

  python3 tools/upscale.py            all live designs
  python3 tools/upscale.py TG-1006    only these codes

Codes in tools/data/upscale_revert.txt get the older photo back from archive/designs-v1/.
Run this after tools/import_catalogue.py (the import writes the non-upscaled photos).
"""
import csv, hashlib, json, os, shutil, sys, tempfile, urllib.request

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(__file__))
import import_catalogue as ic

MODELS = {  # scale -> (file, url, sha256)
    2: ("RealESRGAN_x2plus.pth", "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
        "49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266abb"),
    4: ("RealESRGAN_x4plus.pth", "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1"),
}
MODEL_DIR = "models"
ARCHIVE = "archive/designs-v1"
REVERT = "tools/data/upscale_revert.txt"
LOG = "tools/data/upscale_log.csv"
TILE = 384  # crop is processed in tiles so memory stays small; overlap hides the seams
PAD = 16


def scale_for(side: int) -> int:
    """No upscale when the crop already covers 1200 px; x2 when it reaches 600; x4 below."""
    return 1 if side >= ic.WEB_SIDE else 2 if side * 2 >= ic.WEB_SIDE else 4


def weights(scale: int) -> str:
    name, url, sha = MODELS[scale]
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        os.makedirs(MODEL_DIR, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    if hashlib.sha256(open(path, "rb").read()).hexdigest() != sha:
        raise SystemExit(f"{path}: weights do not match the expected SHA-256")
    return path


class Upscaler:
    def __init__(self):
        import torch, spandrel
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        self.torch = torch
        self.models = {s: spandrel.ModelLoader().load_from_file(weights(s)).model.eval() for s in MODELS}

    def __call__(self, img: Image.Image, scale: int) -> Image.Image:
        torch = self.torch
        a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
        H, W, _ = a.shape
        out = np.zeros((H * scale, W * scale, 3), np.float32)
        model = self.models[scale]
        with torch.inference_mode():
            for y in range(0, H, TILE):
                for x in range(0, W, TILE):
                    y0, x0 = max(y - PAD, 0), max(x - PAD, 0)
                    y1, x1 = min(y + TILE + PAD, H), min(x + TILE + PAD, W)
                    t = torch.from_numpy(a[y0:y1, x0:x1].transpose(2, 0, 1).copy())[None]
                    r = model(t)[0].clamp(0, 1).numpy().transpose(1, 2, 0)
                    ty, tx = (y - y0) * scale, (x - x0) * scale
                    hh, ww = (min(y + TILE, H) - y) * scale, (min(x + TILE, W) - x) * scale
                    out[y * scale:y * scale + hh, x * scale:x * scale + ww] = r[ty:ty + hh, tx:tx + ww]
        return Image.fromarray((out * 255.0).round().astype(np.uint8))


def live_sources() -> dict[str, tuple[str, str]]:
    """code -> (extracted source photo, label style), for every design on the site."""
    codes = ic.load_json(ic.CODES, {})
    live = {d["id"] for d in json.load(open("src/data/designs.json", encoding="utf-8"))}
    out, tmp = {}, tempfile.mkdtemp()
    for s in ic.load_json(ic.SOURCES, []):
        d = os.path.join(tmp, s["source"]); os.makedirs(d)
        for page, path in ic.page_images(s["file"], d).items():
            c = codes.get(f"{s['source']}:{page}")
            if c in live: out[c] = (path, s["label"])
    return dict(sorted(out.items()))


def main() -> None:
    only = set(sys.argv[1:])
    revert = {l.strip() for l in open(REVERT, encoding="utf-8") if l.strip() and not l.startswith("#")} if os.path.exists(REVERT) else set()
    # The log remembers what is done, so a second run only does new pieces. Name codes to redo them.
    done = {}
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            done = {r["code"]: r for r in csv.DictReader(f)}
    srcs = live_sources()
    up = None
    rows = []
    for code, (path, label) in srcs.items():
        if only and code not in only: continue
        if not only and code in done and code not in revert: continue
        dst = os.path.join(ic.IMG_DIR, f"{code}.jpg")
        if code in revert:
            shutil.copy2(os.path.join(ARCHIVE, f"{code}.jpg"), dst)
            rows.append([code, "", 1, "reverted"]); print(code, "reverted"); continue
        if ic.override_for(code):
            rows.append([code, "", 1, "override"]); print(code, "override photo, left as is"); continue
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        box = None if label == "pill" else ic.crop_box(im)
        side = (box[2] - box[0]) if box else 0
        scale = scale_for(side) if box else 1
        if scale == 1:
            rows.append([code, side, 1, "kept, already large"]); print(code, side, "kept"); continue
        if up is None: up = Upscaler()
        out = ic.present(path, enlarge=lambda c, s=scale: up(c, s))
        out.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
        rows.append([code, side, scale, "upscaled"]); print(code, side, f"x{scale}", flush=True)
    merged = {c: [r["code"], r["crop_px"], r["scale"], r["result"]] for c, r in done.items()}
    merged.update({r[0]: r for r in rows})
    with open(LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["code", "crop_px", "scale", "result"]); w.writerows(merged[c] for c in sorted(merged))


if __name__ == "__main__":
    main()
