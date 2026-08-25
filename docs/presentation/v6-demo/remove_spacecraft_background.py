"""Create a real-alpha spacecraft cutout from the light-background source."""

from collections import deque
from pathlib import Path
from statistics import median

from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "assets" / "spacecraft-light.png"
OUTPUT = HERE / "assets" / "spacecraft-transparent.png"


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")
    width, height = source.size
    pixels = source.load()

    border = []
    for x in range(width):
        border.extend((pixels[x, 0], pixels[x, height - 1]))
    for y in range(height):
        border.extend((pixels[0, y], pixels[width - 1, y]))
    background = tuple(int(median(channel)) for channel in zip(*border, strict=True))

    visited = bytearray(width * height)
    queue: deque[int] = deque()

    def is_background(x: int, y: int) -> bool:
        red, green, blue = pixels[x, y]
        distance = (
            (red - background[0]) ** 2
            + (green - background[1]) ** 2
            + (blue - background[2]) ** 2
        )
        return min(red, green, blue) >= 195 and distance <= 48**2

    def enqueue(x: int, y: int) -> None:
        offset = y * width + x
        if not visited[offset] and is_background(x, y):
            visited[offset] = 1
            queue.append(offset)

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        offset = queue.popleft()
        x = offset % width
        y = offset // width
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    alpha = Image.new("L", source.size, 255)
    alpha_pixels = alpha.load()
    for offset, is_clear in enumerate(visited):
        if is_clear:
            alpha_pixels[offset % width, offset // width] = 0

    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))
    result = source.convert("RGBA")
    result.putalpha(alpha)
    result.save(OUTPUT, optimize=True)

    alpha_extrema = alpha.getextrema()
    clear_pixels = alpha.histogram()[0]
    print(f"output={OUTPUT}")
    print(f"background={background} alpha_extrema={alpha_extrema} clear_pixels={clear_pixels}")


if __name__ == "__main__":
    main()
