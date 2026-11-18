#!/bin/bash
# One-time setup on a Mac. Run from the website folder:  bash tools/setup_mac.sh
set -e
cd "$(dirname "$0")/.."
command -v brew >/dev/null || { echo "Homebrew is missing. Install it from https://brew.sh, then run this again."; exit 1; }
brew list poppler >/dev/null 2>&1 || brew install poppler
brew list tesseract >/dev/null 2>&1 || brew install tesseract
# The Mac's own python3 is too old for these versions, so use Homebrew's Python 3.13.
brew list python@3.13 >/dev/null 2>&1 || brew install python@3.13
PYBIN="$(brew --prefix python@3.13)/bin/python3.13"
if [ -d .venv ] && ! .venv/bin/python -c 'import sys; sys.exit(sys.version_info[:2] != (3, 13))' 2>/dev/null; then rm -rf .venv; fi
[ -d .venv ] || "$PYBIN" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r tools/requirements.txt
mkdir -p models
[ -f models/RealESRGAN_x2plus.pth ] || curl -fL --retry 3 -o models/RealESRGAN_x2plus.pth "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
[ -f models/RealESRGAN_x4plus.pth ] || curl -fL --retry 3 -o models/RealESRGAN_x4plus.pth "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
.venv/bin/python -c "import torch, spandrel, PIL, numpy; print('Ready. torch', torch.__version__)"
