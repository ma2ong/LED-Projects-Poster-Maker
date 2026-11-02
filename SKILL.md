---
name: led-projects-poster-maker
description: Create polished English promotional posters from LED display installation case photos, especially Korean project cases. Use when the user wants to combine many LED screen project photos into one or two sales images, label each case with pixel pitch/model and screen size, produce WhatsApp/email-ready portrait and landscape 4K JPGs, or reuse the Korea LED case poster workflow.
metadata:
  short-description: Make 4K LED project case promo posters
---

# LED Projects Poster Maker

## Purpose

Turn a folder of LED display installation photos into sales-ready English promotional images:

- Portrait poster for WhatsApp, WeChat, and direct customer messages.
- Landscape banner for email, presentations, LinkedIn, or attachments.
- Real case-photo collage with clear model labels such as `P1.86`, `P2.5`, `P3.91`, `P10`.
- CTA copy that uses the installation cases to lead into quotation requests.

Use real project photos. Do not use image generation to redraw installation scenes unless the user explicitly asks for generated visuals.

## Default Output

Always generate two variants (four files) unless the user asks otherwise. Allen sends the Korea version to Korean customers and the neutral version to every other country:

- `korea-projects-*`: title `RECENT KOREA\nPROJECTS`, subtitle ends with `in Korea`.
- `recent-projects-*`: title `RECENT\nPROJECTS`, subtitle without any country.

Each variant has:

- `<prefix>-poster-4k.jpg`: portrait `2160` wide, height cropped to content (about `3400-3700`).
- `<prefix>-banner-4k.jpg`: landscape 4K, default `3840x2160`.
- `<prefix>-poster-web.jpg` / `<prefix>-banner-web.jpg`: lightweight copies (75% size, JPEG q85, about 0.7 MB vs 3 MB) for WhatsApp and email. The 4K files stay full quality.

Both variants use the same `cases.json`, the same pill `LED DISPLAY INSTALLATIONS` and the same layout; only title and subtitle differ.

Keep the output in the user's current project/photo folder. Avoid overwriting source photos.

## Workflow

1. Inspect the image folder.
   - Use filenames and thumbnails to identify model, scene, and screen dimensions.
   - Prefer real installation variety: indoor wall, outdoor billboard, modern house/showroom, creative column, immersive/corner display.
   - If the user provides screenshots with markup, inspect them and fix the marked layout issues.

2. Normalize labels in English.
   - Keep labels concise and sales-facing.
   - Always show the model/pixel pitch on each case card.
   - Include screen size where available from the filename.

3. Write `cases.json` in the photo folder (one entry per case, first entry = hero).
   - Fields: `file`, `model`, `title`, `size`, optional `focus` `[x, y]` crop anchor (0-1), optional `crop` `[left, top, right, bottom]` fractional pre-crop for tall phone photos where the screen is a small part of the frame, optional `fit: "contain"` to show the whole (cropped) photo over a blurred fill when the screen would otherwise be cut off.
   - If a case only has video, grab a frame: `ffmpeg -ss 8 -i video.mp4 -frames:v 1 -q:v 2 "<case> (video frame).jpg"`, then list that file.
   - Pick one best photo per project; up to 12 cases after the hero. Prefer photos showing content on the screen over bare structure.
   - Example entry: `{"file": "P1.86 indoor 6400x1120 (1).jpeg", "model": "P1.86", "title": "Restaurant Menu LED Wall", "size": "6400 x 1120 mm"}`

4. Layout (handled by the script from the case count).
   - Portrait: hero image at top, spec strip, rows of 2 / 3 / 3 / 4 cards, CTA near the bottom, canvas cropped to content.
   - Landscape: left-side headline/spec/CTA, right-side hero image, 2 rows of 3 (<= 7 cases) or 3 rows of 4 (<= 13 cases), footer line above the bottom edge.
   - Avoid excessive empty bottom space; crop portrait height tighter if needed.
   - Keep all text fully inside cards. Do not let CTA blocks overlap or hide card text.

5. Generate deterministic composites.
   - Prefer the bundled script: `python scripts/make_led_project_posters.py --input <photo-folder>`.
   - It reads `<photo-folder>/cases.json` when present; without it, it falls back to the legacy Korean filename patterns.
   - `--title`, `--pill` and `--subtitle` override the headline (`
` = line break), tag and subtitle copy (e.g. add "in Korea" for a Korean-market version).
   - The script uses Pillow and preserves the source images as real photos.
   - If Pillow is missing, install or ask the user before using another implementation path.

6. Validate visually.
   - Open both outputs with the image viewer.
   - Check that every case has a model label.
   - Check that labels are not cut off at the bottom.
   - Check that the portrait bottom has no large blank area.
   - Check that the user-facing CTA is readable.

## Recommended English Copy

Main title:

```text
LED Display
Installations
```

Subtitle:

```text
Indoor & outdoor LED screen references recently delivered in Korea
```

CTA:

```text
Planning an LED display project?
Send your size, location and installation needs for a fast quotation.
```

Landscape CTA:

```text
Need a quotation?
Share project size and location with us.
```

Footer:

```text
For new LED display projects, send drawings or target screen size to get a fast quotation.
```

## Labeling Rules

Use these preferred names when the source photos match:

- `P10` + `Outdoor Billboard Screen`
- `P3.91` + `Outdoor LED Screen`
- `P2.5` + `Indoor LED Wall`
- `P2.5` + `Indoor Immersive LED Wall`
- `P1.86` + `Modern House LED Wall`
- `P1.86` + `Creative LED Column`
- `P1.86` + `Front Desk LED Wall`
- `P1.86` + `Indoor Restaurant LED Display`

If a filename includes dimensions, convert them into readable text:

- `12480x6720` -> `12480 x 6720 mm`
- `(960+960)x3360` -> `(960+960) x 3360 mm`
- `8000x2880&(1280+960)x2880` -> `8000 x 2880 mm + side screens`

## Visual Style

- Use a dark professional background with cyan accent blocks.
- Use rounded image cards, subtle shadows, and white typography.
- Use English only inside the final poster unless the user requests another language.
- Keep CTA blocks cyan with dark text.
- Keep copy short. These are sales images, not brochures.
- Do not put decorative elements over product photos.

## Script Notes

The bundled script renders from `cases.json` (preferred). Without a manifest it uses the legacy Korean filename pattern matching, then falls back to available JPG/PNG images.

Run both commands every time (Korea + neutral):

```powershell
# Korea version
python scripts\make_led_project_posters.py --input "<photo-folder>" --output "<photo-folder>\out" --prefix korea-projects --title "RECENT KOREA\nPROJECTS" --pill "LED DISPLAY INSTALLATIONS" --subtitle "Indoor & outdoor LED screen references recently delivered in Korea"
# Neutral version for other countries
python scripts\make_led_project_posters.py --input "<photo-folder>" --output "<photo-folder>\out" --prefix recent-projects --title "RECENT\nPROJECTS" --pill "LED DISPLAY INSTALLATIONS" --subtitle "Indoor & outdoor LED screen references recently delivered"
```

Optional output directory:

```powershell
python scripts\make_led_project_posters.py --input ".\photos" --output ".\out"
```

