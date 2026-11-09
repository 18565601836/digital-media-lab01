# -*- coding: utf-8 -*-
"""步骤 7 的可复现实验素材：生成两张测试图，实测不同编码下的文件体积。

对应实验指南第 7 步「用手机截图核对分辨率与实际文件大小，解释压缩带来的差异」：
没有把压缩后的体积当成未压缩估算结果，而是用同一张图分别存成 BMP / PNG / JPEG，
直接量出「位深 × 分辨率」的理论值与实际落盘体积之间的差距。

运行：
    python tools/make_test_images.py
输出：
    assets/test_ui_1080x2400.png      界面类截图（大面积纯色、文字边缘锐利）
    assets/test_photo_1920x1080.jpg   照片类图像（连续色调、细节丰富）
    results/压缩对比.csv              实测数据
"""

from __future__ import annotations

import csv
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
RESULTS = os.path.join(ROOT, "results")
FONT = r"C:\Windows\Fonts\msyh.ttc"


def font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def make_ui(width: int = 1080, height: int = 2400) -> Image.Image:
    """模拟手机界面截图：大面积纯色 + 文字，是 PNG 的强项、JPEG 的弱项。"""
    img = Image.new("RGB", (width, height), "#F2F3F5")
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, width, 88], fill="#111318")          # 状态栏
    d.text((36, 26), "9:41", font=font(34), fill="#FFFFFF")
    d.text((width - 170, 26), "5G  100%", font=font(30), fill="#FFFFFF")

    d.rectangle([0, 88, width, 420], fill="#1E6FFF")         # 顶部渐变区
    for i in range(140):                                     # 用横向色带模拟渐变
        c = tuple(int(v) for v in np.array([30, 111, 255]) * (1 - i / 300))
        d.rectangle([0, 300 + i * 2, width, 302 + i * 2], fill=c)
    d.text((48, 140), "第 01 讲 · 数制与容量", font=font(58), fill="#FFFFFF")
    d.text((48, 226), "数字媒体程序设计  2026 秋", font=font(34), fill="#D8E4FF")

    for i, (title, sub) in enumerate([
        ("数制转换", "二 / 十 / 十六进制互转"),
        ("容量估算", "照片 · 音频 · 视频"),
        ("压缩对比", "BMP / PNG / JPEG"),
    ]):                                                      # 三张卡片
        top = 470 + i * 300
        d.rounded_rectangle([48, top, width - 48, top + 250], radius=28, fill="#FFFFFF")
        d.rounded_rectangle([80, top + 40, 240, top + 200], radius=24, fill="#E8F0FF")
        d.text((118, top + 92), f"{i + 1}", font=font(84), fill="#1E6FFF")
        d.text((280, top + 60), title, font=font(52), fill="#1A1A1A")
        d.text((280, top + 140), sub, font=font(32), fill="#8A8F99")
        d.line([48, top + 250, width - 48, top + 250], fill="#EDEFF3", width=2)

    for i in range(6):                                       # 列表项
        top = 1450 + i * 120
        d.ellipse([48, top + 16, 128, top + 96], fill="#EEF3FF")
        d.text((68, top + 38), "→", font=font(40), fill="#1E6FFF")
        d.rectangle([150, top + 34, 150 + 520 - i * 30, top + 54], fill="#DDE1E8")
        d.rectangle([150, top + 66, 150 + 380, top + 80], fill="#EDEFF3")

    d.rectangle([0, height - 180, width, height], fill="#FFFFFF")   # 底部导航
    for i in range(4):
        cx = 135 + i * 270
        d.ellipse([cx - 22, height - 120, cx + 22, height - 76], fill="#C9CED8" if i else "#1E6FFF")
        d.rectangle([cx - 40, height - 56, cx + 40, height - 44], fill="#C9CED8" if i else "#1E6FFF")
    return img


def make_photo(width: int = 1920, height: int = 1080, seed: int = 42) -> Image.Image:
    """模拟照片：连续色调、细节多，是 JPEG 的强项。"""
    rng = np.random.default_rng(seed)
    horizon = int(height * 0.62)

    top = np.array([22, 48, 96], dtype=float)
    bottom = np.array([248, 168, 120], dtype=float)          # 黄昏
    ramp = np.linspace(0, 1, horizon)[:, None] ** 0.85
    sky = top * (1 - ramp) + bottom * ramp

    yy, xx = np.mgrid[0:horizon, 0:width]
    sx, sy, r = width * 0.72, horizon * 0.5, 78
    dist = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    glow = np.exp(-((dist / (width * 0.30)) ** 1.5))[..., None] * np.array([255, 168, 92]) * 0.62
    disc = np.clip((r - dist) / 5.0, 0, 1)[..., None]

    canvas = np.zeros((height, width, 3), dtype=float)
    sky_block = sky[:, None, :] + glow
    sky_block = sky_block * (1 - disc) + disc * np.array([255, 240, 206])
    canvas[:horizon] = sky_block
    canvas[horizon:] = np.array([18, 24, 40], dtype=float)

    img = Image.fromarray(canvas.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")

    for layer, color in enumerate([(58, 66, 92), (40, 46, 68), (24, 28, 44)]):  # 远山
        pts = [(0, horizon + 20)]
        x = 0
        base = horizon - 130 + layer * 45
        while x < width:
            step = rng.integers(120, 260)
            pts.append((x, base + rng.integers(-70, 70)))
            pts.append((x + step // 2, base - rng.integers(30, 110)))
            x += step
        pts += [(width, horizon + 20)]
        d.polygon(pts, fill=color)

    water = np.array(img.crop((0, horizon, width, height)), dtype=float)    # 水面
    water = water[::-1, :, :] * 0.55 + np.array([18, 24, 40]) * 0.45
    water = np.array(Image.fromarray(water.clip(0, 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(3)), dtype=float)
    ripple = 1 + 0.06 * np.sin(np.linspace(0, 40 * np.pi, height - horizon))[:, None, None]
    img.paste(Image.fromarray((water * ripple).clip(0, 255).astype(np.uint8)), (0, horizon))

    grain = rng.normal(0, 5.0, (height, width, 3))
    arr = np.array(img, dtype=float) + grain
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def save_and_measure(img: Image.Image, name: str, rows: list) -> None:
    """把同一张图存成不同格式，记录落盘字节数。"""
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    w, h = img.size
    raw = w * h * 3

    variants = {
        "BMP（未压缩）": ("bmp", os.path.join(RESULTS, f"{name}.bmp"), {}),
        "PNG（无损）": ("png", os.path.join(ASSETS, f"{name}.png"), {"optimize": True}),
        "JPEG q95": ("jpeg", os.path.join(ASSETS, f"{name}_q95.jpg"), {"quality": 95, "subsampling": 0}),
        "JPEG q75": ("jpeg", os.path.join(ASSETS, f"{name}_q75.jpg"), {"quality": 75}),
    }
    sizes = {}
    for label, (fmt, path, kwargs) in variants.items():
        img.save(path, format=fmt.upper(), **kwargs)
        sizes[label] = os.path.getsize(path)
        if fmt == "bmp":                    # BMP 只是中间产物，量完即删
            os.remove(path)

    rows.append({
        "图像": name, "分辨率": f"{w}×{h}", "像素数": w * h,
        "理论未压缩(B)": raw, **{f"{k}(B)": v for k, v in sizes.items()},
        "最小体积(B)": min(sizes.values()),
    })
    print(f"{name:24s} {w}x{h}  理论 {raw:>10,d} B")
    for k, v in sizes.items():
        print(f"    {k:14s} {v:>10,d} B   压缩比 {raw / v:6.2f} : 1")


def main() -> int:
    rows: list = []
    save_and_measure(make_ui(), "test_ui_1080x2400", rows)
    save_and_measure(make_photo(), "test_photo_1920x1080", rows)

    csv_path = os.path.join(RESULTS, "压缩对比.csv")
    fields = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n已写出 {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
