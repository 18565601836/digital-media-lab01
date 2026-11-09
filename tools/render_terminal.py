# -*- coding: utf-8 -*-
"""把命令行输出渲染成「终端截图」PNG，用于实验报告插图。

逐字符按网格定位绘制：ASCII 用 Consolas（等宽，步进 = 一个字符格），
CJK 用微软雅黑（占两格并居中），因此中英混排的表格在图片里也能严格对齐。

用法：
    python tools/render_terminal.py --input build/demo.txt --command "python estimate.py demo" \
        --output assets/fig1.png --title "Windows PowerShell"
"""

from __future__ import annotations

import argparse
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

MONO = r"C:\Windows\Fonts\consola.ttf"
CJK = r"C:\Windows\Fonts\msyh.ttc"
CONSOLE_ICON = ">_"

BG = (12, 12, 12)
FG = (212, 212, 212)
DIM = (118, 118, 118)
GREEN = (22, 198, 12)
CYAN = (59, 120, 255)
YELLOW = (249, 241, 165)
WHITE = (244, 244, 244)


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def is_wide(ch: str) -> bool:
    return unicodedata.east_asian_width(ch) in ("W", "F")


def color_for(line: str, index: int) -> tuple:
    """按行内容决定字符颜色。"""
    if "PASS" in line and 0 <= index - line.find("PASS") < 4:
        return GREEN
    if "FAIL" in line and 0 <= index - line.find("FAIL") < 4:
        return (231, 72, 86)
    stripped = line.strip()
    if not stripped:
        return FG
    if set(stripped) <= set("=-") and len(stripped) > 3:
        return DIM
    if stripped.startswith(("一、", "二、", "三、", "四、")):
        return CYAN
    if stripped.startswith("结论"):
        return YELLOW
    if stripped.startswith("|"):
        return (196, 196, 196)
    if stripped.startswith("+"):
        return DIM
    return FG


def render(lines: list[str], command: str, title: str, size: int = 24, cols: int = 92,
           prompt: str = r"PS C:\Users\LEGION\...\lab01> ") -> Image.Image:
    mono = ImageFont.truetype(MONO, size)
    cjk = ImageFont.truetype(CJK, size)
    title_font = ImageFont.truetype(CJK, int(size * 0.72))
    cell = mono.getlength("0")
    line_h = int(size * 1.35)

    body_lines = [prompt + command] + lines
    cols = max(cols, max(width(l) for l in body_lines))
    pad_x, pad_y = int(cell * 1.4), int(line_h * 0.5)
    title_h = int(size * 1.55)

    w = int(cols * cell + pad_x * 2)
    h = title_h + pad_y * 2 + line_h * len(body_lines) + int(line_h * 0.4)

    img = Image.new("RGBA", (w, h), BG + (255,))
    d = ImageDraw.Draw(img)

    # 标题栏
    d.rectangle([0, 0, w, title_h], fill=(31, 31, 31, 255))
    d.rectangle([0, title_h - 1, w, title_h], fill=(58, 58, 58, 255))
    d.rounded_rectangle([pad_x, 8, pad_x + int(size * 1.1), 8 + int(size * 0.95)],
                        radius=4, fill=(1, 95, 206, 255))
    d.text((pad_x + int(size * 0.18), 9), CONSOLE_ICON, font=title_font, fill=(255, 255, 255))
    d.text((pad_x + int(size * 1.45), int(title_h * 0.26)), title, font=title_font, fill=(214, 214, 214))
    ctrl = "—   □   ×"
    d.text((w - pad_x - title_font.getlength(ctrl), int(title_h * 0.26)), ctrl,
           font=title_font, fill=(150, 150, 150))

    # 正文
    x0, y = pad_x, title_h + pad_y
    for row, line in enumerate(body_lines):
        is_prompt = row == 0
        col = 0
        for i, ch in enumerate(line):
            x = x0 + col * cell
            if is_prompt:
                color = WHITE if i >= len(prompt) else (170, 170, 170)
            else:
                color = color_for(line, i)
            if is_wide(ch):
                adv = cjk.getlength(ch)
                d.text((x + (2 * cell - adv) / 2, y), ch, font=cjk, fill=color)
                col += 2
            else:
                d.text((x, y), ch, font=mono, fill=color)
                col += 1
        y += line_h

    # 圆角 + 边框
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, w - 1, h - 1], radius=14, outline=(70, 70, 70, 255))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="把命令输出渲染成终端截图")
    p.add_argument("--input", required=True, help="命令输出文本（UTF-8）")
    p.add_argument("--output", required=True, help="输出 PNG")
    p.add_argument("--command", required=True, help="提示符后显示的命令")
    p.add_argument("--title", default="Windows PowerShell")
    p.add_argument("--prompt", default=r"PS C:\Users\LEGION\...\lab01> ")
    p.add_argument("--size", type=int, default=26)
    p.add_argument("--cols", type=int, default=88)
    args = p.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        lines = f.read().splitlines()
    img = render(lines, args.command, args.title, args.size, args.cols, args.prompt)
    img.save(args.output)
    print(f"{args.output}  {img.size[0]}x{img.size[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
