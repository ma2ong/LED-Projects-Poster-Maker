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

Generate both files unless the user asks otherwise:

- `korea-led-projects-poster-4k.jpg`: tight portrait, default `2160x3400`.
- `korea-led-projects-banner-4k.jpg`: landscape 4K, default `3840x2160`.

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

3. Choose layout.
   - Portrait: hero image at top, spec strip, 2 large cards, 2 medium cards, 3 small cards, CTA near the bottom.
   - Landscape: left-side headline/spec/CTA, right-side hero image, 2 rows of case cards, footer line above the bottom edge.
   - Avoid excessive empty bottom space; crop portrait height tighter if needed.
   - Keep all text fully inside cards. Do not let CTA blocks overlap or hide card text.

4. Generate deterministic composites.
   - Prefer the bundled script: `python scripts/make_led_project_posters.py --input <photo-folder>`.
   - The script uses Pillow and preserves the source images as real photos.
   - If Pillow is missing, install or ask the user before using another implementation path.

5. Validate visually.
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

The bundled script is designed for folders similar to Korean LED project case photo collections. It uses filename pattern matching first, then falls back to available JPG/PNG images.

Typical command:

```powershell
python scripts\make_led_project_posters.py --input "C:\Users\Administrator\Desktop\韩国案例"
```

Optional output directory:

```powershell
python scripts\make_led_project_posters.py --input ".\photos" --output ".\out"
```

