#!/bin/bash
# Converts icon.png into icon.icns for the macOS .app bundle.
# Run this ON macOS, in the same folder as icon.png.

set -e

SRC="icon.png"
ICONSET="icon.iconset"

if [ ! -f "$SRC" ]; then
    echo "icon.png not found in the current folder."
    exit 1
fi

rm -rf "$ICONSET"
mkdir "$ICONSET"

sips -z 16 16     "$SRC" --out "$ICONSET/icon_16x16.png"
sips -z 32 32     "$SRC" --out "$ICONSET/icon_16x16@2x.png"
sips -z 32 32     "$SRC" --out "$ICONSET/icon_32x32.png"
sips -z 64 64     "$SRC" --out "$ICONSET/icon_32x32@2x.png"
sips -z 128 128   "$SRC" --out "$ICONSET/icon_128x128.png"
sips -z 256 256   "$SRC" --out "$ICONSET/icon_128x128@2x.png"
sips -z 256 256   "$SRC" --out "$ICONSET/icon_256x256.png"
sips -z 512 512   "$SRC" --out "$ICONSET/icon_256x256@2x.png"
sips -z 512 512   "$SRC" --out "$ICONSET/icon_512x512.png"
cp "$SRC" "$ICONSET/icon_512x512@2x.png"

iconutil -c icns "$ICONSET" -o icon.icns
rm -rf "$ICONSET"

echo "Done: icon.icns created."