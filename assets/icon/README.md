# App icon — constellation mark

Three connected four-point stars of three sizes, wired into a triangle, on a
deep near-black squircle. Drawn in the Constellation UI's own idiom: the actual
`starPath(r, 4, innerRatio)` geometry, the evidence-level blue, self-coloured
glow, and faint background starlight.

## Files

- `icon-master.svg` — **source of truth.** 1024×1024, artwork clipped to an
  n=5 superellipse squircle (Apple-style continuous curvature: 824px body,
  100px margin). Also copied to `ui/logo.svg` for the web UI favicon + header.
- `AppIcon.icns` — built macOS icon, all 10 slots (16→512 @1x/@2x).
- `gen.py` — regenerates `icon-master.svg` from the locked design settings.

## Locked design settings

From the interactive tuner:

```
hue #6aa5ff · sharpness 0.31 · glow 0.9 · spread 1.00 · dust 9
lead 4-point · lines blue · core on · layout dynamic
```

Change these at the top of `gen.py` to re-cut the mark.

## Regenerate the .icns

No SVG rasterizer is a project dependency; this uses headless Chrome (already
on the machine) plus the native `iconutil`/`sips`.

```sh
cd assets/icon
python3 gen.py                      # writes icon-master.svg + render.html

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --default-background-color=00000000 \
  --window-size=1024,1024 --screenshot="$PWD/png_1024.png" \
  "file://$PWD/render.html"

# downsample the 1024 master to every size (crisper than rendering small)
mkdir -p AppIcon.iconset
for pair in "16 icon_16x16" "32 icon_16x16@2x" "32 icon_32x32" \
            "64 icon_32x32@2x" "128 icon_128x128" "256 icon_128x128@2x" \
            "256 icon_256x256" "512 icon_256x256@2x" "512 icon_512x512" \
            "1024 icon_512x512@2x"; do
  set -- $pair
  cp png_1024.png "AppIcon.iconset/$2.png"
  sips -z "$1" "$1" "AppIcon.iconset/$2.png" >/dev/null
done
iconutil -c icns AppIcon.iconset -o AppIcon.icns
```

Rendering at 1024 and downsampling (rather than rendering each size directly)
avoids a headless-Chrome first-paint race at small window sizes and yields
smoother small icons.
