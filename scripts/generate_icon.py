"""Generates assets/icon.ico from scratch with Pillow (no external image needed)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent.parent / "assets"
OUT_DIR.mkdir(exist_ok=True)

SIZE = 256
BG = (3, 0, 20, 255)  # matches --bg in style.css
ACCENT = (204, 255, 0, 255)  # matches --accent
BULL = (57, 135, 229, 255)  # matches --bull


def build_icon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 8
    draw.rounded_rectangle([margin, margin, SIZE - margin, SIZE - margin], radius=48, fill=BG)

    draw.ellipse([margin, margin, SIZE - margin, SIZE - margin], outline=ACCENT, width=10)

    # Simple rocket silhouette: triangle nose + body + fins, in the accent lime.
    cx = SIZE // 2
    draw.polygon(
        [
            (cx, 46),
            (cx - 34, 150),
            (cx + 34, 150),
        ],
        fill=ACCENT,
    )
    draw.rounded_rectangle([cx - 34, 130, cx + 34, 200], radius=18, fill=ACCENT)
    draw.polygon([(cx - 34, 170), (cx - 62, 210), (cx - 34, 200)], fill=BULL)
    draw.polygon([(cx + 34, 170), (cx + 62, 210), (cx + 34, 200)], fill=BULL)
    draw.ellipse([cx - 14, 96, cx + 14, 124], fill=BG)

    return img


def main() -> None:
    img = build_icon()
    ico_path = OUT_DIR / "icon.ico"
    img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
