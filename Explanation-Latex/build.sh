#!/bin/bash
# Build main.pdf into the build/ subfolder.
# Usage:
#   ./build.sh          — compile
#   ./build.sh --clean  — delete the build/ folder entirely

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
TEX="$SCRIPT_DIR/main.tex"

if [[ "$1" == "--clean" ]]; then
    echo "Removing $BUILD_DIR ..."
    rm -rf "$BUILD_DIR"
    echo "Done."
    exit 0
fi

mkdir -p "$BUILD_DIR"

echo "Building main.tex -> build/main.pdf ..."

# Run twice so TOC and cross-references are resolved.
pdflatex -interaction=nonstopmode -output-directory="$BUILD_DIR" "$TEX"
pdflatex -interaction=nonstopmode -output-directory="$BUILD_DIR" "$TEX"

echo ""
echo "Done.  PDF: $BUILD_DIR/main.pdf"
