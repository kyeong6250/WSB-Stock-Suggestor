"""Generates assets/icon.ico from scratch with Pillow (no external image needed)."""

from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).parent.parent / "assets"
OUT_DIR.mkdir(exist_ok=True)

SIZE = 256
SURFACE = (255, 255, 255, 255)  # matches --surface in style.css
BORDER = (230, 229, 224, 255)  # neutral, close to --border over white
ACCENT = (47, 111, 237, 255)  # matches --accent / --bull


def build_icon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 8
    draw.rounded_rectangle([margin, margin, SIZE - margin, SIZE - margin], radius=52, fill=SURFACE, outline=BORDER, width=4)

    # Uptrend line with an arrowhead, echoing the in-app sidebar brand mark.
    line_width = 18
    points = [(64, 176), (108, 132), (140, 164), (196, 96)]
    draw.line(points, fill=ACCENT, width=line_width, joint="curve")
    for p in points:
        draw.ellipse([p[0] - line_width / 2, p[1] - line_width / 2, p[0] + line_width / 2, p[1] + line_width / 2], fill=ACCENT)

    # Arrowhead flag at the top-right end of the line.
    draw.line([(160, 96), (196, 96)], fill=ACCENT, width=line_width, joint="curve")
    draw.line([(196, 96), (196, 132)], fill=ACCENT, width=line_width, joint="curve")
    for p in [(160, 96), (196, 96), (196, 132)]:
        draw.ellipse([p[0] - line_width / 2, p[1] - line_width / 2, p[0] + line_width / 2, p[1] + line_width / 2], fill=ACCENT)

    return img


def main() -> None:
    img = build_icon()
    ico_path = OUT_DIR / "icon.ico"
    img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
