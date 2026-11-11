"""Create public demonstration media using a procedural fictional avatar."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_subtitle
from subtitle_engine.core import puttext

WIDTH, HEIGHT, FPS = 284, 504, 30
FONT = ROOT / "assets/approved-subtitle-rework-v1/fonts/706b8c0de2de.otf"


def avatar(frame, transparent=False):
    """Geometric cartoon drawn from code, with no photograph or voice input."""
    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0) if transparent else "#dce9ef")
    draw = ImageDraw.Draw(image)
    if not transparent:
        draw.rounded_rectangle((22, 25, 262, 440), radius=20, fill="#c4d8df")
        draw.ellipse((192, 50, 231, 89), fill="#f4d78b")
    drift = round(math.sin(frame / 25) * 2)
    draw.ellipse((62, 365, 225, 414), fill="#8aa1ac" if not transparent else "#557e9a")
    draw.rounded_rectangle((65, 238 + drift, 220, 405), radius=39, fill="#3c7794")
    draw.rounded_rectangle((123, 202 + drift, 161, 253 + drift), radius=10, fill="#edb98c")
    draw.ellipse((89, 95 + drift, 195, 225 + drift), fill="#f1c69e")
    draw.pieslice((84, 72 + drift, 200, 171 + drift), 175, 355, fill="#39485c")
    draw.ellipse((114, 149 + drift, 122, 158 + drift), fill="#243344")
    draw.ellipse((161, 149 + drift, 169, 158 + drift), fill="#243344")
    draw.arc((124, 170 + drift, 160, 195 + drift), 10, 165, fill="#9d5f4d", width=3)
    draw.line((139, 159 + drift, 135, 176 + drift, 144, 176 + drift), fill="#c88c68", width=2)
    draw.ellipse((46, 275 + drift, 82, 346 + drift), fill="#f1c69e")
    draw.ellipse((204, 267 + drift, 239, 338 + drift), fill="#f1c69e")
    return image


def visual(gid, frame, count):
    image = avatar(frame)
    if gid == "cg01":
        yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
        radius = ((xx - 142) / 154) ** 2 + ((yy - 200) / 247) ** 2
        opacity = (np.clip((radius - .32) * 125, 0, 205)).astype("uint8")
        vignette = Image.new("RGBA", image.size, "#142332")
        vignette.putalpha(Image.fromarray(opacity))
        image.alpha_composite(vignette)
        stage = max(0, min(1, (frame - 8) / 18))
        card = Image.new("RGBA", (226, 95), "#edf2f5")
        pen = ImageDraw.Draw(card)
        for x, h in [(25, 29), (62, 45), (99, 62), (136, 74), (173, 56)]:
            pen.rounded_rectangle((x, 87 - h, x + 23, 87), radius=3, fill="#4a91a0")
        image.alpha_composite(card, (29, round(HEIGHT - 107 + (1 - stage) * 110)))
        puttext(image, "如何一步步", {"font": str(FONT), "size": 18}, 142, 292)
        if frame > 30:
            puttext(image, "学会新技能", {"font": str(FONT), "size": 24, "fill": "#f5cf5c"}, 142, 326,
                    op=min(1, (frame - 30) / 10))
    else:
        if frame > 22:
            puttext(image, "持续练习", {"font": str(FONT), "size": 47, "fill": "#3d648c"}, 142, 91,
                    op=min(1, (frame - 22) / 10))
            image.alpha_composite(avatar(frame, True))
        draw = ImageDraw.Draw(image)
        for i in range(12):
            x = 15 + ((i * 43 + frame * (i % 3 - 1)) % 250)
            y = (frame * (2 + i % 3) - i * 29) % 620 - 75
            angle = frame * .11 + i
            size = 10 + i % 4 * 3
            points = [(x + math.cos(angle + j * math.pi / 2) * size,
                       y + math.sin(angle + j * math.pi / 2) * size) for j in range(4)]
            draw.polygon(points, fill="#f0bd49" if i % 2 else "#b87949")
        puttext(image, "把想法变成行动", {"font": str(FONT), "size": 18}, 142, 335)
    return image


def encode(path, frames):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoder = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-s", "284x504",
         "-r", str(FPS), "-pix_fmt", "rgb24", "-i", "pipe:0", "-an",
         "-c:v", "libx264", "-threads", "2", "-crf", "18", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    try:
        for image in frames:
            encoder.stdin.write(image.convert("RGB").tobytes())
    finally:
        encoder.stdin.close()
    if encoder.wait():
        raise RuntimeError("Mock preview encoding failed")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"], check=True)


def main():
    examples = ROOT / "examples"
    catalog = json.loads((examples / "catalog.json").read_text("utf-8"))
    for row in catalog["examples"]:
        gid = row["id"]
        if row.get("input"):
            config = render_subtitle.resolve(json.loads((ROOT / row["input"]).read_text("utf-8")))
            count = config["frameCount"]

            def sequence():
                for frame in range(count):
                    image = avatar(frame)
                    image.alpha_composite(render_subtitle.combined(config, frame))
                    yield image
        else:
            count = 110
            sequence = lambda: (visual(gid, frame, count) for frame in range(count))
        destination = examples / "videos" / (gid + ".mp4")
        encode(destination, sequence())
        gif = ROOT / row["gif"]
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(destination), "-an", "-vf",
             "fps=10,scale=240:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];"
             "[s1][p]paletteuse=dither=bayer", "-loop", "0", str(gif)], check=True)
        row.pop("reference", None)
        row["result"] = destination.relative_to(ROOT).as_posix()
        row["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        row["status"] = "mock-demonstration"
        row["presenter"] = "procedural-fictional-cartoon"
        row["fullDecode"] = True
        print(gid, "encoded and decoded", flush=True)
    catalog["scope"] = "代码绘制虚构人物的 mock 示例；字幕使用既有机制，画面两组为合成示意"
    catalog["humanFootageIncluded"] = False
    (examples / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", "utf-8")
    avatar(0).save(examples / "mock-presenter.png")
    raw = ROOT / "assets/migration-demo/talking-head-raw.mp4"
    encode(raw, (avatar(n) for n in range(360)))
    manifest = {
        "file": raw.name, "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "role": "procedural-mock-migration-input", "durationSeconds": 12,
        "canvas": [WIDTH, HEIGHT], "fps": FPS, "audio": False,
        "usePolicy": "Synthetic cartoon for rendering smoke tests. Supply authorized talking-head footage for real speech migration.",
        "generator": "examples/build_mock_examples.py",
    }
    (raw.parent / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")


if __name__ == "__main__":
    main()
