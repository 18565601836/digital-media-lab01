# -*- coding: utf-8 -*-
"""把 results/压缩对比.csv 画成对比图（assets/fig4_compression.png）。

设计说明：BMP 未压缩体积（7.8 MB / 6.2 MB）比其余编码大一个数量级，
若同轴绘制会把 PNG / JPEG 压成看不见的细线，因此图中只画三种压缩后的编码，
BMP 作为「理论未压缩」参照写在每个子图标题里。

运行：
    python tools/plot_compression.py
"""

from __future__ import annotations

import csv
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = r"C:\Windows\Fonts\msyh.ttc"
BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

INK = (26, 26, 26)
MUTED = (110, 116, 128)
GRID = (228, 231, 236)
COLORS = {"PNG（无损）": (46, 107, 255), "JPEG q95": (255, 138, 61), "JPEG q75": (34, 160, 107)}


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(BOLD if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def human(n: float) -> str:
    for unit, factor in (("MB", 10**6), ("KB", 10**3)):
        if n >= factor:
            return f"{n / factor:.2f} {unit}" if unit == "MB" else f"{n / factor:.1f} {unit}"
    return f"{n:.0f} B"


def panel(d: ImageDraw.ImageDraw, box, row: dict, title: str) -> None:
    x0, y0, x1, y1 = box
    d.text((x0, y0), title, font=font(30, True), fill=INK)
    d.text((x0, y0 + 44), f"理论未压缩（BMP）：{human(int(row['BMP（未压缩）(B)']))}，图中按压缩后体积绘制",
           font=font(22), fill=MUTED)

    raw = int(row["理论未压缩(B)"])
    keys = ["PNG（无损）", "JPEG q95", "JPEG q75"]
    values = [int(row[f"{k}(B)"]) for k in keys]
    top = max(values) * 1.06
    label_w = 250
    bar_x0 = x0 + 170
    bar_max = (x1 - label_w) - bar_x0
    y = y0 + 100
    bar_h, gap = 52, 34

    for key, value in zip(keys, values):
        d.text((x0, y + 12), key, font=font(24), fill=INK)
        w = max(4, int(bar_max * value / top))
        d.rounded_rectangle([bar_x0, y, bar_x0 + w, y + bar_h], radius=6, fill=COLORS[key] + (255,))
        ratio = raw / value
        d.text((bar_x0 + w + 14, y + 10), f"{human(value)}  （{ratio:.1f}×）",
               font=font(23), fill=MUTED)
        y += bar_h + gap

    d.line([bar_x0, y + 6, x1 - label_w + 40, y + 6], fill=GRID, width=2)
    d.text((x0, y + 20), "括号内为相对未压缩体积的压缩比", font=font(20), fill=MUTED)


def main() -> int:
    csv_path = os.path.join(ROOT, "results", "压缩对比.csv")
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = {r["图像"]: r for r in csv.DictReader(f)}

    w, h = 1680, 700
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img, "RGBA")

    d.text((60, 44), "同一内容、不同编码：文件体积对比", font=font(40, True), fill=INK)
    d.text((60, 100), "1080×2400 界面截图与 1920×1080 照片，实测落盘字节数（Pillow 编码）",
           font=font(24), fill=MUTED)

    panel(d, (60, 180, 800, 620), rows["test_ui_1080x2400"], "界面截图 1080×2400")
    d.line([840, 200, 840, 600], fill=GRID, width=2)
    panel(d, (880, 180, 1620, 620), rows["test_photo_1920x1080"], "照片 1920×1080")

    d.text((60, 640), "数据来源：results/压缩对比.csv；复现：python tools/make_test_images.py",
           font=font(20), fill=MUTED)

    out = os.path.join(ROOT, "assets", "fig4_compression.png")
    img.save(out, optimize=True)
    print(f"{out}  {img.size[0]}x{img.size[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

