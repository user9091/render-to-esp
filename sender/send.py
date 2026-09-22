#!/usr/bin/env python3
"""Convert a local image to 300x400 monochrome and send it to the ESP."""

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

WIDTH, HEIGHT = 300, 400
ROW_BYTES = (WIDTH + 7) // 8
HERE = Path(__file__).resolve().parent


def pack_image(path: Path) -> bytes:
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source).convert("RGBA")
        source.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
        canvas.paste(source, ((WIDTH - source.width) // 2, (HEIGHT - source.height) // 2), source)
        gray = canvas.convert("L")
        # Darken midtones while keeping true white white and true black black.
        darker = gray.point([round(255 * (level / 255) ** 1.5) for level in range(256)])
        mono = darker.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        pixels = mono.load()
        packed = bytearray(ROW_BYTES * HEIGHT)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if pixels[x, y] == 0:
                    packed[y * ROW_BYTES + x // 8] |= 0x80 >> (x % 8)
        return bytes(packed)


def notify(title: str, message: str) -> None:
    try:
        subprocess.run(["notify-send", title, message], check=False)
    except FileNotFoundError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Image file to show")
    parser.add_argument("--notify", action="store_true", help="Show a desktop notification")
    args = parser.parse_args()
    try:
        config = json.loads((HERE / "config.json").read_text())
        url = config["url"]
        token = config["token"]
        if not url.startswith("http://") or not token or token == "choose-a-long-random-token":
            raise ValueError("Set URL and token in sender/config.json")
        bitmap = pack_image(args.image)
        boundary = "render-to-esp-" + uuid.uuid4().hex
        payload = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="image"; filename="image.bin"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("ascii") + bitmap + f"\r\n--{boundary}--\r\n".encode("ascii")
        request = Request(url, data=payload, method="POST", headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Image-Token": token,
        })
        with urlopen(request, timeout=45) as response:
            response.read()
        message = f"Sent {args.image.name} to ESP"
        print(message)
        if args.notify:
            notify("Render to ESP", message)
        return 0
    except (OSError, ValueError, KeyError, HTTPError, URLError) as exc:
        message = f"Could not send {args.image.name}: {exc}"
        print(message, file=sys.stderr)
        if args.notify:
            notify("Render to ESP failed", message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
