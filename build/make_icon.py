"""Generate the app + installer icon (dark-green logo).

Run:  python build/make_icon.py
Outputs: assets/logo.png  and  assets/logo.ico
"""

from __future__ import annotations

from PIL import Image, ImageDraw

SIZE = 256
GREEN_TOP = (16, 185, 129)      # #10b981
GREEN_BOT = (6, 95, 70)         # #065f46
WHITE = (255, 255, 255)


def rounded_mask(size: int, radius: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def build_logo(size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # vertical gradient
    for y in range(size):
        t = y / size
        r = int(GREEN_TOP[0] * (1 - t) + GREEN_BOT[0] * t)
        g = int(GREEN_TOP[1] * (1 - t) + GREEN_BOT[1] * t)
        b = int(GREEN_TOP[2] * (1 - t) + GREEN_BOT[2] * t)
        ImageDraw.Draw(img).line([(0, y), (size, y)], fill=(r, g, b, 255))
    img.putalpha(rounded_mask(size, radius=size // 4))

    d = ImageDraw.Draw(img)
    cx = size // 2
    # down arrow
    d.line([(cx, size * 0.28), (cx, size * 0.62)], fill=WHITE, width=size // 14)
    d.polygon(
        [(cx, size * 0.68),
         (cx - size * 0.14, size * 0.50),
         (cx + size * 0.14, size * 0.50)],
        fill=WHITE,
    )
    # base bar
    d.rounded_rectangle(
        [size * 0.28, size * 0.76, size * 0.72, size * 0.82],
        radius=size // 18, fill=WHITE,
    )
    return img


if __name__ == "__main__":
    logo = build_logo()
    logo.save("assets/logo.png")
    # multi-resolution ICO
    logo.save("assets/logo.ico", sizes=[(16, 16), (32, 32), (48, 48),
                                        (64, 64), (128, 128), (256, 256)])
    print("wrote assets/logo.png and assets/logo.ico")
