#!/usr/bin/env python3
"""Create portrait and landscape LED project promotional posters from case photos."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ACCENT = (0, 206, 201, 255)
BG_TOP = (7, 13, 24)
BG_BOTTOM = (18, 40, 55)


@dataclass
class CaseImage:
    key: str
    path: Path
    model: str
    title: str
    size: str
    focus: tuple[float, float] = (0.5, 0.5)


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


def gradient(size: tuple[int, int], top=BG_TOP, bottom=BG_BOTTOM) -> Image.Image:
    w, h = size
    out = Image.new("RGBA", size)
    d = ImageDraw.Draw(out)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,)
        d.line((0, y, w, y), fill=col)
    return out


def cover(path: Path, size: tuple[int, int], focus=(0.5, 0.5)) -> Image.Image:
    im = Image.open(path).convert("RGB")
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


def tile_label(base: Image.Image, box: tuple[int, int, int, int], case: CaseImage, scale=1.0) -> None:
    x, y, w, h = box
    d = ImageDraw.Draw(base)
    pad = int(28 * scale)
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


def make_portrait(cases: dict[str, CaseImage], out: Path) -> None:
    pw, ph = 2160, 3400
    poster = gradient((pw, ph))
    d = ImageDraw.Draw(poster)

    hero = cover(cases["hero"].path, (pw, 1040), cases["hero"].focus).convert("RGBA")
    ov = Image.new("RGBA", (pw, 1040), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for yy in range(1040):
        od.line((0, yy, pw, yy), fill=(0, 0, 0, int(130 * (1 - yy / 1040))))
    for xx in range(pw):
        od.line((xx, 0, xx, 1040), fill=(0, 0, 0, int(150 * (1 - xx / pw))))
    hero.alpha_composite(ov)
    poster.alpha_composite(hero, (0, 0))

    pill(d, 116, 96, "RECENT KOREA PROJECTS")
    d.multiline_text((116, 228), "LED Display\nInstallations", font=font("arialbd.ttf", 132), fill=(255, 255, 255, 255), spacing=0)
    d.text((122, 558), "Indoor & outdoor LED screen references recently delivered in Korea", font=font("arial.ttf", 50), fill=(226, 238, 245, 245))

    d.rounded_rectangle((116, 1115, 2044, 1290), radius=36, fill=(255, 255, 255, 240))
    for i, (a, b) in enumerate([("P1.86", "Modern House Indoor"), ("P2.5", "Commercial Indoor"), ("P3.91 / P10", "Outdoor LED")]):
        x = 178 + i * 610
        d.text((x, 1150), a, font=font("arialbd.ttf", 58), fill=(6, 23, 35, 255))
        d.text((x, 1218), b, font=font("arial.ttf", 39), fill=(68, 84, 98, 255))
        if i < 2:
            d.line((x + 520, 1150, x + 520, 1254), fill=(180, 195, 207), width=4)

    placements = [
        ("p10", (116, 1370, 928, 475)),
        ("p25_install", (1116, 1370, 928, 475)),
        ("p186_modern", (116, 1910, 928, 420)),
        ("p25_8000", (1116, 1910, 928, 420)),
        ("p186_column", (116, 2395, 590, 400)),
        ("p391", (785, 2395, 590, 400)),
        ("p186_front", (1454, 2395, 590, 400)),
    ]
    for key, box in placements:
        case = cases[key]
        rounded_paste(poster, cover(case.path, (box[2], box[3]), case.focus), box, 34, True)
        tile_label(poster, box, case)

    cta_two_line(
        d,
        (116, 3025, 1928, 160),
        "Planning an LED display project?",
        "Send your size, location and installation needs for a fast quotation.",
    )
    support = "Fine-pitch indoor LED walls, creative columns and outdoor billboard displays for commercial projects."
    d.text((116, 3260), support, font=fit_text(d, support, 1928, 38, False), fill=(208, 226, 236, 235))
    poster.convert("RGB").save(out, quality=96, subsampling=0)


def make_landscape(cases: dict[str, CaseImage], out: Path) -> None:
    lw, lh = 3840, 2160
    land = gradient((lw, lh), (6, 12, 22), (16, 38, 54))
    d = ImageDraw.Draw(land)

    pill(d, 150, 120, "KOREA LED DISPLAY CASES", 40)
    d.multiline_text((150, 270), "Recent LED\nDisplay Projects", font=font("arialbd.ttf", 150), fill=(255, 255, 255, 255), spacing=0)
    d.multiline_text((156, 640), "Real indoor and outdoor installations\nrecently delivered in Korea.", font=font("arial.ttf", 54), fill=(226, 238, 245, 245), spacing=18)

    for i, (a, b) in enumerate([("P1.86", "Modern house LED walls"), ("P2.5", "Commercial indoor LED screens"), ("P3.91 / P10", "Outdoor billboard displays")]):
        y = 900 + i * 135
        d.rounded_rectangle((150, y, 1160, y + 102), radius=28, fill=(22, 45, 62, 255), outline=(75, 110, 128, 255), width=3)
        d.text((205, y + 23), a, font=font("arialbd.ttf", 52), fill=(255, 255, 255, 255))
        d.text((530, y + 34), b, font=font("arial.ttf", 38), fill=(202, 220, 230, 255))

    cta_two_line(d, (150, 1345, 1130, 210), "Need a quotation?", "Share project size and location with us.", 1.35)
    rounded_paste(land, cover(cases["hero"].path, (2280, 900), cases["hero"].focus), (1390, 115, 2280, 900), 50, True)
    tile_label(land, (1390, 115, 2280, 900), cases["hero"], 1.15)

    placements = [
        ("p10", (1390, 1090, 700, 315)),
        ("p25_install", (2180, 1090, 700, 315)),
        ("p25_8000", (2970, 1090, 700, 315)),
        ("p186_modern", (1390, 1480, 700, 315)),
        ("p186_column", (2180, 1480, 700, 315)),
        ("p391", (2970, 1480, 700, 315)),
    ]
    for key, box in placements:
        case = cases[key]
        rounded_paste(land, cover(case.path, (box[2], box[3]), case.focus), box, 34, True)
        tile_label(land, box, case, 0.9)

    note = "For new LED display projects, send drawings or target screen size to get a fast quotation."
    d.text((1390, 1888), note, font=fit_text(d, note, 2280, 44, False), fill=(211, 229, 238, 235))
    land.convert("RGB").save(out, quality=96, subsampling=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=Path, default=Path.cwd(), help="Folder containing LED project images")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output folder, defaults to input folder")
    parser.add_argument("--prefix", default="korea-led-projects", help="Output filename prefix")
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_dir = (args.output or input_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = detect_cases(input_dir)
    portrait = output_dir / f"{args.prefix}-poster-4k.jpg"
    landscape = output_dir / f"{args.prefix}-banner-4k.jpg"
    make_portrait(cases, portrait)
    make_landscape(cases, landscape)
    print(portrait)
    print(landscape)


if __name__ == "__main__":
    main()
