# Photo pipeline: from a maker's photo to a live design

Run everything from the website folder. Every step skips work already done, so running again is safe.
Status: [done] works and is in use, [written] code exists but is not tested on real photos, [todo] not built.

## Where things live

- Scripts: `tools/`. Hand-edited sheets: `tools/data/`. Logo and fonts: `tools/assets/`.
- Generated or in-progress files, never committed: `working/cutouts/` (transparent PNG per design), `working/new-photos/` (drop folder for new weight-named photos), `working/pdfs/` (catalogue PDFs).
- Catalogue PDFs from the makers: `catalogue-sources/`. Model weights: `models/`.

## The steps, in order

| # | Step | Script | What it does | Status |
|---|------|--------|--------------|--------|
| 1 | Register the catalogue | `tools/data/catalogue_sources.json` | Add the PDF: file, source name, category, label style (`burned`, `pill` or `tag`), added date | done |
| 2 | Import | `tools/import_catalogue.py` | Pulls the original photo from each PDF page. Reads the weight from the label with OCR. Gives each page a permanent design code (`src/data/catalogue_codes.json`). Writes `tools/data/catalogue_review.csv` and `src/data/designs.json` | done |
| 3 | Fix weights by hand | `tools/data/catalogue_review.csv` | Rows marked `review` or `poor-photo`: type the weight, set status `checked`, run step 2 again | manual |
| 4 | Upscale | `tools/upscale.py` | Real-ESRGAN enlarges the photo. Weights are SHA-checked | done |
| 5 | Whiten | `tools/whiten.py` | Pushes the photo's background to near white. Skips hand-picked photos | done |
| 6 | Cut out the background | `tools/remove_bg.py --all` | rembg with isnet-general-use. Writes `working/cutouts/<code>.png` (transparent, same margin on every piece) and `src/data/cutouts.json`, the list the site uses to drop the soft edge fade. Tested on bangles: holes and thin wires kept | done |
| 7 | Web sizes | `tools/thumbs.py` | 480, 800 and 1200 px WebP. Transparent when there is a cutout | done |
| 8 | Share cards | `tools/share_cards.py` | Square 1080 card per design in `public/share/`: logo and "22K wholesale jewellery", code and weight, piece, name below, phone number. The design page's Share button shares this image (phones) or saves it (laptops). Redrawn only when name, weight, photo or layout changes (`tools/data/share_manifest.json`) | done |
| 9 | Link-preview cards | `tools/previews.py` | `public/og-home.jpg` for the home page. Design pages use the share card as their link preview, so the per-design 1200 x 630 cards are off (`--designs` makes them) | done |
| 10 | Names and tags | `tools/data/tags_review.csv`, then `node scripts/apply-tags.mjs` | Motif, finish, work, stones, occasion and name. Only rows marked `checked` show. By hand | manual |
| 11 | Catalogue PDF | `tools/catalogue_pdf.py` | A PDF of chosen designs, six to a page, by date, type, weight or code. See the top of the file | done |
| 12 | Build and push | `npm run build`, `npm test` | Prune script drops unpublished photos from the deploy | done |

`bash tools/overnight.sh` runs steps 2 and 4 to 9, the hero cutouts and the tag step on the Mac. First run needs internet for the 170 MB background-removal model.

## Shortcuts

- **Photo already enhanced and cut out, named by weight** (`10.500.png` is 10.50 g): `python3 tools/add_photos.py`, then steps 7 and 8. It assigns the next code and adds the design. Names and tags go in `tools/data/new_piece_tags.json` first.
- **Hand-picked photo for one design**: put it in `tools/data/photo_overrides/<code>.png`. Upscale and whiten skip it.

## Rules that must hold

- A design code is permanent. Never reuse or renumber one.
- A weight is never guessed. If OCR finds anything other than exactly one plausible value, the row is `review`.
- Same files in, same pictures out. No step uses random settings.
- Model licences must allow business use. Use isnet-general-use (Apache-2.0). Do not use BRIA RMBG weights.

## Plan for 10,000 designs (not built yet; decide at about 2,000)

- **Repo size.** One design is about 400 KB across its files (photo, three WebP sizes, share card, link card), so 10,000 is about 4 GB. Git hosting and deploys will struggle well before that. Move the images to object storage (Cloudflare R2 or Vercel Blob) behind one `IMAGE_BASE` address, and keep only the data in git.
- **Catalogue page.** It puts every tile in the HTML and filters in the browser. Fine for 300, about 10 MB of HTML at 10,000. At that size: one static page per type with paging, and a small search file.
- **Deploy limits.** Check the host's file-count and size limits for the plan before passing about 5,000 designs (one design is about 6 files).
- **Pipeline.** Every step already skips finished work, so a new batch costs only its own photos. Background removal is the slow step: about 2.5 seconds a photo on a laptop.
- **Codes.** `TG-` plus four digits runs out at 9,999. Past that the code pattern in `src/lib/whatsapp.js` and the search need to accept five digits.

## Known problems

- Catalogue photos have uneven off-white and blue-tinted backgrounds. A photo without a cutout still gets the soft edge fade, which shows the tint as a grey-blue cloud. A design listed in `src/data/cutouts.json` gets no fade. Running step 6 on everything removes the cloud.
- u2net fills the holes inside bangles. isnet keeps them. BiRefNet-lite failed with no output (probably out of memory) and is untested.

## To test on one sample image

For each step, keep the image before and after and look at both:
1. Original from the PDF
2. After upscale
3. After whiten
4. After cutout (on a plain colour and on the site's tile white)
5. 480 px tile as it will show
6. Link-preview card
Note any step that makes it worse. Put the results here.

## Test log

(empty)
