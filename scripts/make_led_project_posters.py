#!/usr/bin/env python3
"""Create portrait and landscape LED project promotional posters from case photos."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ACCENT = (0, 206, 201, 255)
BG_TOP = (7, 13, 24)
BG_BOTTOM = (18, 40, 55)
SPEC_ROWS = [("P1.25 – P1.86", "Fine-pitch indoor LED"), ("P2.5 – P3.91", "Commercial indoor LED"), ("P4 – P10", "Outdoor LED displays")]


@dataclass
class CaseImage:
    key: str
    path: Path
    model: str
    title: str
    size: str
    focus: tuple[float, float] = (0.5, 0.5)
    crop: tuple[float, float, float, float] | None = None  # fractional (left, top, right, bottom) pre-crop
    fit: str = "cover"  # "contain" keeps the whole (cropped) photo visible over a blurred fill


def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def image_files(folder: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts)


def first_match(files: Iterable[Path], *patterns: str) -> Path | None:
    for pattern in patterns:
        rx = re.compile(pattern, re.I)
        for path in files:
            if rx.search(path.name):
                return path
    return None


def detect_cases(folder: Path) -> dict[str, CaseImage]:
    files = image_files(folder)
    if not files:
        raise SystemExit(f"No image files found in {folder}")

    used: set[Path] = set()

    def pick(key: str, patterns: list[str], model: str, title: str, size: str, focus=(0.5, 0.5)) -> CaseImage:
        path = first_match([p for p in files if p not in used], *patterns)
        if path is None:
            path = next(p for p in files if p not in used)
        used.add(path)
        return CaseImage(key, path, model, title, size, focus)

    cases = {
        "hero": pick("hero", [r"P1\.86.*8640x960.*\(1\)", r"P1\.86.*7360x960"], "P1.86", "Indoor Restaurant LED Display", "8640 x 960 mm"),
        "p10": pick("p10", [r"P10.*12480x6720.*\(1\)", r"P10"], "P10", "Outdoor Billboard Screen", "12480 x 6720 mm"),
        "p25_install": pick("p25_install", [r"P2\.5\s+indoor\s+5760x2880", r"P2\.5.*5760"], "P2.5", "Indoor LED Wall", "5760 x 2880 mm"),
        "p186_modern": pick("p186_modern", [r"P1\.86.*12800x2880"], "P1.86", "Modern House LED Wall", "12800 x 2880 mm"),
        "p25_8000": pick("p25_8000", [r"P2\.5.*8000x2880"], "P2.5", "Indoor Immersive LED Wall", "8000 x 2880 mm + side screens"),
        "p186_column": pick("p186_column", [r"P1\.86.*3360"], "P1.86", "Creative LED Column", "(960+960) x 3360 mm"),
        "p391": pick("p391", [r"P3\.91", r"4000x3000"], "P3.91", "Outdoor LED Screen", "4000 x 3000 mm"),
        "p186_front": pick("p186_front", [r"P1\.86.*3840x1920(?!.*\(2\))", r"P1\.86.*3840x1920"], "P1.86", "Front Desk LED Wall", "3840 x 1920 mm"),
    }
    return cases


def load_manifest(folder: Path, manifest: Path) -> list[CaseImage]:
    """Ordered case list from cases.json; the first entry is the hero image."""
    items = json.loads(manifest.read_text(encoding="utf-8"))
    cases = []
    for i, it in enumerate(items):
        path = folder / it["file"]
        if not path.exists():
            raise SystemExit(f"Manifest file not found: {path}")
        cases.append(CaseImage(f"case{i}", path, it["model"], it["title"], it["size"], tuple(it.get("focus", (0.5, 0.5))), tuple(it["crop"]) if "crop" in it else None, it.get("fit", "cover")))
    if len(cases) < 2:
        raise SystemExit("Manifest needs at least a hero and one case")
    return cases


def gradient(size: tuple[int, int], top=BG_TOP, bottom=BG_BOTTOM) -> Image.Image:
    w, h = size
    out = Image.new("RGBA", size)
    d = ImageDraw.Draw(out)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,)
        d.line((0, y, w, y), fill=col)
    return out


def cover(path: Path, size: tuple[int, int], focus=(0.5, 0.5), crop=None, fit="cover", reserve_bottom=0) -> Image.Image:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if crop:
        iw, ih = im.size
        im = im.crop((int(crop[0] * iw), int(crop[1] * ih), int(crop[2] * iw), int(crop[3] * ih)))
    iw, ih = im.size
    w, h = size
    if fit == "contain":
        bg = cover_resize(im, size, focus).filter(ImageFilter.GaussianBlur(40))
        bg = Image.eval(bg, lambda v: int(v * 0.45))
        ah = h - reserve_bottom  # keep the photo clear of the label overlay
        scale = min(w / iw, ah / ih)
        fg = im.resize((int(iw * scale), int(ih * scale)), Image.Resampling.LANCZOS)
        bg.paste(fg, ((w - fg.width) // 2, (ah - fg.height) // 2))
        return bg
    return cover_resize(im, size, focus)


def cover_resize(im: Image.Image, size: tuple[int, int], focus=(0.5, 0.5)) -> Image.Image:
    iw, ih = im.size
    w, h = size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = max(0, min(nw - w, int((nw - w) * focus[0])))
    y = max(0, min(nh - h, int((nh - h) * focus[1])))
    return im.crop((x, y, x + w, y + h))


def rounded_paste(base: Image.Image, im: Image.Image, box: tuple[int, int, int, int], radius=36, shadow=True) -> None:
    x, y, w, h = box
    if shadow:
        sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle((40, 40, w + 40, h + 40), radius=radius, fill=(0, 0, 0, 115))
        sh = sh.filter(ImageFilter.GaussianBlur(24))
        base.alpha_composite(sh, (x - 40, y - 26))
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    base.paste(im.convert("RGBA"), (x, y), mask)
    ImageDraw.Draw(base).rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=(255, 255, 255, 88), width=4)


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, start_size: int, bold=True):
    name = "arialbd.ttf" if bold else "arial.ttf"
    size = start_size
    while size > 18:
        f = font(name, size)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        size -= 2
    return font(name, size)


def pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, size=42) -> None:
    f = font("arialbd.ttf", size)
    bb = draw.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle((x, y, x + w + 56, y + h + 30), radius=22, fill=ACCENT)
    draw.text((x + 28, y + 14), text, font=f, fill=(5, 22, 32, 255))


def tile_label(base: Image.Image, box: tuple[int, int, int, int], case: CaseImage, scale=1.0, pad: int | None = None) -> None:
    x, y, w, h = box
    d = ImageDraw.Draw(base)
    pad = int(28 * scale) if pad is None else pad
    overlay_h = int(170 * scale)
    grad = Image.new("RGBA", (w, overlay_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for yy in range(overlay_h):
        gd.line((0, yy, w, yy), fill=(0, 0, 0, int(215 * yy / overlay_h)))
    base.alpha_composite(grad, (x, y + h - overlay_h))

    mf = font("arial.ttf", int(34 * scale))
    mbb = d.textbbox((0, 0), case.model, font=mf)
    mw, mh = mbb[2] - mbb[0], mbb[3] - mbb[1]
    d.rounded_rectangle(
        (x + pad, y + h - overlay_h + int(22 * scale), x + pad + mw + int(34 * scale), y + h - overlay_h + mh + int(48 * scale)),
        radius=int(14 * scale),
        fill=(0, 206, 201, 245),
    )
    d.text((x + pad + int(17 * scale), y + h - overlay_h + int(33 * scale)), case.model, font=mf, fill=(5, 22, 32, 255))

    tf = fit_text(d, case.title, w - pad * 2, int(44 * scale), True)
    sf = fit_text(d, case.size, w - pad * 2, int(32 * scale), False)
    d.text((x + pad, y + h - int(88 * scale)), case.title, font=tf, fill=(255, 255, 255, 255))
    d.text((x + pad, y + h - int(42 * scale)), case.size, font=sf, fill=(225, 238, 244, 245))


def cta_two_line(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], line1: str, line2: str, scale=1.0) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=int(36 * scale), fill=ACCENT)
    f1 = fit_text(draw, line1, w - int(96 * scale), int(48 * scale), True)
    f2 = fit_text(draw, line2, w - int(96 * scale), int(38 * scale), False)
    draw.text((x + int(48 * scale), y + int(26 * scale)), line1, font=f1, fill=(5, 22, 32, 255))
    draw.text((x + int(48 * scale), y + int(78 * scale)), line2, font=f2, fill=(5, 22, 32, 245))


def place_rows(base: Image.Image, tiles: list[CaseImage], x0: int, y0: int, total_w: int, rows: list[tuple[int, int]], gap=40) -> int:
    """Lay tiles into rows of (count, height); returns the y after the last row."""
    i, y = 0, y0
    for count, h in rows:
        if i >= len(tiles):
            break
        w = (total_w - gap * (count - 1)) // count
        scale = min(1.0, w / 620)
        for c in range(count):
            if i >= len(tiles):
                break
            box = (x0 + c * (w + gap), y, w, h)
            rounded_paste(base, cover(tiles[i].path, (w, h), tiles[i].focus, tiles[i].crop, tiles[i].fit, int(110 * scale)), box, 34, True)
            tile_label(base, box, tiles[i], scale)
            i += 1
        y += h + 65
    return y


def save_jpg(im: Image.Image, out: Path) -> None:
    """Write to a temp file then swap in, so an open image viewer never sees a half-written JPG."""
    tmp = out.with_suffix(".tmp.jpg")
    im = im.convert("RGB")
    im.save(tmp, "JPEG", quality=96, subsampling=0)
    os.replace(tmp, out)
    # Lightweight copy (~0.7 MB vs ~3 MB) for WhatsApp / email; 75% keeps the smallest text crisp.
    web = out.with_name(out.name.replace("-4k.jpg", "-web.jpg"))
    small = im.resize((round(im.width * 0.75), round(im.height * 0.75)), Image.LANCZOS)
    small.save(tmp, "JPEG", quality=85, optimize=True, progressive=True)
    os.replace(tmp, web)


def make_portrait(cases: list[CaseImage], out: Path, subtitle: str, pill_text: str, title: str) -> None:
    pw, ph = 2160, 4200  # cropped to content height at the end
    poster = gradient((pw, ph))
    d = ImageDraw.Draw(poster)

    hero = cover(cases[0].path, (pw, 1040), cases[0].focus, cases[0].crop).convert("RGBA")
    ov = Image.new("RGBA", (pw, 1040), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for yy in range(1040):
        od.line((0, yy, pw, yy), fill=(0, 0, 0, int(130 * (1 - yy / 1040))))
    for xx in range(pw):
        od.line((xx, 0, xx, 1040), fill=(0, 0, 0, int(150 * (1 - xx / pw))))
    hero.alpha_composite(ov)
    poster.alpha_composite(hero, (0, 0))
    tile_label(poster, (0, 0, pw, 1040), cases[0], 1.25, pad=116)

    pill(d, 116, 96, pill_text)
    d.multiline_text((116, 228), title, font=font("arialbd.ttf", 132), fill=(255, 255, 255, 255), spacing=0)
    d.text((122, 558), subtitle, font=fit_text(d, subtitle, 1928, 50, False), fill=(226, 238, 245, 245))

    d.rounded_rectangle((116, 1115, 2044, 1290), radius=36, fill=(255, 255, 255, 240))
    for i, (a, b) in enumerate(SPEC_ROWS):
        x = 178 + i * 610
        d.text((x, 1150), a, font=font("arialbd.ttf", 58), fill=(6, 23, 35, 255))
        d.text((x, 1218), b, font=font("arial.ttf", 39), fill=(68, 84, 98, 255))
        if i < 2:
            d.line((x + 520, 1150, x + 520, 1254), fill=(180, 195, 207), width=4)

    y = place_rows(poster, cases[1:], 116, 1370, 1928, [(2, 520), (3, 400), (3, 400), (4, 340)])
    cta_two_line(
        d,
        (116, y + 15, 1928, 160),
        "Planning an LED display project?",
        "Send your size, location and installation needs for a fast quotation.",
    )
    support = "Fine-pitch indoor LED walls, creative columns and outdoor billboard displays for commercial projects."
    d.text((116, y + 250), support, font=fit_text(d, support, 1928, 38, False), fill=(208, 226, 236, 235))
    poster = poster.crop((0, 0, pw, y + 380))
    save_jpg(poster, out)


def make_landscape(cases: list[CaseImage], out: Path, subtitle: str, pill_text: str, title: str) -> None:
    lw, lh = 3840, 2160
    land = gradient((lw, lh), (6, 12, 22), (16, 38, 54))
    d = ImageDraw.Draw(land)

    pill(d, 150, 120, pill_text, 40)
    d.multiline_text((150, 270), title, font=font("arialbd.ttf", 150), fill=(255, 255, 255, 255), spacing=0)
    d.multiline_text((156, 640), subtitle, font=font("arial.ttf", 54), fill=(226, 238, 245, 245), spacing=18)

    for i, (a, b) in enumerate(SPEC_ROWS):
        y = 900 + i * 135
        d.rounded_rectangle((150, y, 1160, y + 102), radius=28, fill=(22, 45, 62, 255), outline=(75, 110, 128, 255), width=3)
        af = font("arialbd.ttf", 52)
        d.text((205, y + 23), a, font=af, fill=(255, 255, 255, 255))
        ax = 205 + d.textbbox((0, 0), a, font=af)[2] + 40
        d.text((ax, y + 34), b, font=fit_text(d, b, 1160 - 40 - ax, 38, False), fill=(202, 220, 230, 255))

    cta_two_line(d, (150, 1345, 1130, 210), "Need a quotation?", "Share project size and location with us.", 1.35)
    hero_h = 900 if len(cases) <= 7 else 700
    rounded_paste(land, cover(cases[0].path, (2280, hero_h), cases[0].focus, cases[0].crop), (1390, 115, 2280, hero_h), 50, True)
    tile_label(land, (1390, 115, 2280, hero_h), cases[0], 1.15)

    rows = [(3, 315), (3, 315)] if len(cases) <= 7 else [(4, 330), (4, 330), (4, 330)]
    y = place_rows(land, cases[1:], 1390, 115 + hero_h + 75, 2280, rows)
    note = "For new LED display projects, send drawings or target screen size to get a fast quotation."
    d.text((1390, y - 5), note, font=fit_text(d, note, 2280, 44, False), fill=(211, 229, 238, 235))
    save_jpg(land, out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=Path, default=Path.cwd(), help="Folder containing LED project images")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output folder, defaults to input folder")
    parser.add_argument("--prefix", default="led-projects", help="Output filename prefix")
    parser.add_argument("--manifest", "-m", type=Path, default=None, help="cases.json (defaults to <input>/cases.json if present)")
    parser.add_argument("--pill", default="RECENT LED PROJECTS", help="Small tag text above the title")
    parser.add_argument("--title", default="LED Display\\nInstallations", help="Big headline; use \\n for a line break")
    parser.add_argument("--subtitle", default="Indoor & outdoor LED screen references recently delivered", help="Subtitle under the title")
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_dir = (args.output or input_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = args.manifest or (input_dir / "cases.json")
    if manifest.exists():
        cases = load_manifest(input_dir, manifest)
    else:
        legacy = detect_cases(input_dir)
        cases = [legacy["hero"]] + [c for k, c in legacy.items() if k != "hero"]
    portrait = output_dir / f"{args.prefix}-poster-4k.jpg"
    landscape = output_dir / f"{args.prefix}-banner-4k.jpg"
    subtitle = args.subtitle
    title = args.title.replace("\\n", "\n")
    make_portrait(cases, portrait, subtitle, args.pill, title)
    make_landscape(cases, landscape, subtitle.replace(" recently", "\nrecently"), args.pill, title)
    print(portrait)
    print(landscape)


if __name__ == "__main__":
    main()
