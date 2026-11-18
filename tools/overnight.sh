#!/bin/bash
# Import every PDF in tools/data/catalogue_sources.json, upscale every live photo, cut each piece out of its
# background, make the web sizes, share cards and link previews, and cut out the first-screen pieces. Same files in, same pictures out. Keeps the Mac awake until it finishes.
# Run from the website folder:  bash tools/overnight.sh
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || { echo "Run  bash tools/setup_mac.sh  first."; exit 1; }
exec > >(tee tools/overnight.log) 2>&1
echo "Started $(date)"
caffeinate -i -w $$ &
$PY tools/import_catalogue.py
$PY tools/upscale.py
$PY tools/whiten.py
$PY tools/remove_bg.py --all
$PY tools/thumbs.py
$PY tools/share_cards.py
$PY tools/previews.py
$PY tools/hero_cutouts.py
node scripts/apply-tags.mjs
echo "Finished $(date). Pieces to check by hand: tools/data/catalogue_review.csv (rows marked review)."
