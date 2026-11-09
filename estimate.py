#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 01 讲 实验：数制转换与存储容量估算 —— 验证脚本（estimate.py）

本脚本把实验指南中的 7 个步骤全部代码化，用于复核手算结果：
    * 二 / 十 / 十六进制互转，打印位权展开、除基取余、一位拆四位的过程；
    * 由分辨率、位深、采样率、声道数、码率推导照片 / 音频 / 视频的存储体积；
    * 同时给出 SI（10^3）与 IEC（2^10）两套单位，避免 MB 与 MiB 混用；
    * 用 `check` 子命令把结果与实验指南的参考答案逐条比对（CI 可直接用）。

用法示例
--------
    python estimate.py demo                    # 完整演示（步骤 1-6）
    python estimate.py demo --only convert     # 只演示数制转换
    python estimate.py demo --only size        # 只演示容量估算
    python estimate.py convert 10110101 --base 2
    python estimate.py convert 255 --to 16
    python estimate.py convert 1A --base 16 --to 2
    python estimate.py image 1920 1080 --depth 24
    python estimate.py audio --minutes 4 --rate 44100 --depth 16 --channels 2
    python estimate.py video --hours 2 --mbps 8
    python estimate.py extend --capacity 256 --photo 4
    python estimate.py check                   # 自检，全部通过返回 0

作者：数字媒体程序设计 2026 秋 · 第 01 讲实验
许可：MIT
"""

from __future__ import annotations

import argparse
import platform
import sys
import unicodedata
from typing import Iterable, Sequence

__version__ = "1.0.0"

DIGITS = "0123456789ABCDEF"
SI_UNITS = (("B", 1), ("KB", 10**3), ("MB", 10**6), ("GB", 10**9), ("TB", 10**12))
IEC_UNITS = (("B", 1), ("KiB", 2**10), ("MiB", 2**20), ("GiB", 2**30), ("TiB", 2**40))


# --------------------------------------------------------------------------
# 终端排版工具：按“显示宽度”补空格，中文字符占 2 格，保证表格对齐
# --------------------------------------------------------------------------
def disp_width(text: str) -> int:
    """返回字符串在等宽终端中的显示宽度（CJK 全角字符记 2）。"""
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text: str, width: int, align: str = "<") -> str:
    """把 text 填充到 width 个显示宽度。"""
    text = str(text)
    space = width - disp_width(text)
    if space <= 0:
        return text
    if align == ">":
        return " " * space + text
    if align == "^":
        left = space // 2
        return " " * left + text + " " * (space - left)
    return text + " " * space


def table(headers: Sequence[str], rows: Iterable[Sequence[object]], aligns: str | None = None) -> str:
    """用纯 ASCII 边框渲染表格（避免制表符在不同字体下宽度不一致）。"""
    rows = [[str(c) for c in row] for row in rows]
    cols = len(headers)
    aligns = aligns or "<" * cols
    widths = [disp_width(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], disp_width(cell))

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines = [border, "| " + " | ".join(pad(str(h), widths[i], "^") for i, h in enumerate(headers)) + " |", border]
    for row in rows:
        lines.append("| " + " | ".join(pad(row[i], widths[i], aligns[i]) for i in range(cols)) + " |")
    lines.append(border)
    return "\n".join(lines)


def rule(char: str = "=", width: int = 66) -> str:
    return char * width


def num(n: float) -> str:
    """格式化数字：整数加千分位，小数最多保留 4 位并去掉尾随 0。"""
    if isinstance(n, int) or float(n).is_integer():
        return f"{int(n):,}"
    return f"{n:,.4f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------
# 一、数制转换
# --------------------------------------------------------------------------
def parse_int(text: str, base: int) -> int:
    """把任意进制的字符串转成十进制整数（支持 0b / 0o / 0x 前缀与下划线）。"""
    s = text.strip().replace("_", "")
    prefix = {"0b": 2, "0o": 8, "0x": 16}
    for head, b in prefix.items():
        if s.lower().startswith(head):
            s, base = s[2:], b
            break
    if not 2 <= base <= 16:
        raise ValueError(f"进制必须在 2-16 之间，收到 {base}")
    value = 0
    for ch in s.upper():
        digit = DIGITS.index(ch) if ch in DIGITS else -1
        if digit < 0 or digit >= base:
            raise ValueError(f"字符 {ch!r} 不是 {base} 进制的合法数字：{text!r}")
        value = value * base + digit
    return value


def to_base(value: int, base: int) -> str:
    """十进制整数转 base 进制字符串（除基取余、余数倒序）。"""
    if value < 0:
        return "-" + to_base(-value, base)
    if value == 0:
        return "0"
    out = []
    while value:
        value, rem = divmod(value, base)
        out.append(DIGITS[rem])
    return "".join(reversed(out))


def weight_table(digits: str, base: int) -> tuple[int, str]:
    """按权展开：返回十进制值与逐位权值表。"""
    digits = digits.upper()
    total = 0
    rows = []
    n = len(digits)
    for i, ch in enumerate(digits):
        pos = n - 1 - i
        digit = int(ch, base)
        weight = base**pos
        total += digit * weight
        rows.append([pos, f"{base}^{pos} = {num(weight)}", digit, num(digit * weight)])
    text = table(["位号", "位权", "数字", "乘积"], rows, "><>>")
    return total, text


def division_steps(value: int, base: int) -> str:
    """除基取余的过程表。"""
    rows = []
    n = value
    while n:
        q, r = divmod(n, base)
        rows.append([n, q, r, DIGITS[r]])
        n = q
    text = table(["被除数", "商", "余数", "十六进制位"], rows, ">>>>")
    return text


def hex_to_binary_steps(text: str) -> str:
    """十六进制一位拆四位。"""
    rows = [[ch, f"{int(ch, 16):04b}"] for ch in text.upper()]
    return table(["十六进制位", "4 位二进制"], rows, "^^")


def convert_report(raw: str, base: int, target: int | None = None) -> str:
    """生成一组数制转换的完整推导文本。"""
    value = parse_int(raw, base)
    label = {2: "二进制", 8: "八进制", 10: "十进制", 16: "十六进制"}.get(base, f"{base} 进制")
    prefix = {2: "0b", 8: "0o", 16: "0x"}.get(base, "")
    raw = raw.upper()
    out = [f"输入：{prefix}{raw}（{label}，共 {len(raw)} 位）"]

    if base == 16:
        out.append("步骤 1：一位拆四位（4 个二进制位 = 1 个十六进制位）")
        out.append(hex_to_binary_steps(raw))
        bits = "".join(f"{int(ch, 16):04b}" for ch in raw).lstrip("0") or "0"
        out.append(f"  → 拼接得 {bits:0>{4 * len(raw)}}，去掉前导 0 为 {bits}")
        detail = " + ".join(f"{int(ch, 16)}×{16 ** (len(raw) - 1 - i)}" for i, ch in enumerate(raw))
        out.append(f"步骤 2：按权展开复核：{detail} = {num(value)}")
    elif base == 10:
        out.append("步骤 1：除 16 取余，余数倒序排列")
        out.append(division_steps(value, 16))
        out.append(f"  → {to_base(value, 16)}")
    else:
        out.append(f"步骤 1：按权展开，逐位乘以 {base} 的位次幂后求和")
        _, table_text = weight_table(raw, base)
        out.append(table_text)
        terms = " + ".join(
            str(int(ch, base) * base ** (len(raw) - 1 - i)) for i, ch in enumerate(raw) if ch != "0"
        )
        out.append(f"  只保留非零项：{terms} = {num(value)}")

    if base == 16:
        out.append(f"结论：{raw}(16) = {num(value)}(10) = 0b{to_base(value, 2)}(2)")
    elif base == 10:
        out.append(f"结论：{raw}(10) = 0x{to_base(value, 16)}(16) = 0b{to_base(value, 2)}(2)")
    elif base == 2:
        out.append(f"结论：{raw}(2) = {num(value)}(10) = 0x{to_base(value, 16)}(16)")
    else:
        out.append(f"结论：{raw}({base}) = {num(value)}(10) = 0x{to_base(value, 16)}(16) = "
                   f"0b{to_base(value, 2)}(2)")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 二、存储容量估算
# --------------------------------------------------------------------------
def image_bytes(width: int, height: int, depth: int = 24) -> int:
    """未压缩位图：宽 × 高 × 位深 ÷ 8。depth=24 即 RGB 各 8 位。"""
    return width * height * depth // 8


def audio_bytes(seconds: float, rate: int = 44100, depth: int = 16, channels: int = 2) -> int:
    """未压缩 PCM：采样率 × 位深 × 声道数 × 时长 ÷ 8。"""
    return int(rate * depth * channels * seconds) // 8


def video_bytes(seconds: float, mbps: float) -> int:
    """按码率估算：码率(Mbit/s) × 时长(s) ÷ 8。"""
    return int(mbps * 10**6 * seconds) // 8


def human_si(n: float) -> str:
    for name, factor in reversed(SI_UNITS):
        if abs(n) >= factor:
            return f"{n / factor:.4f}".rstrip("0").rstrip(".") + f" {name}"
    return f"{n:.0f} B"


def human_iec(n: float) -> str:
    for name, factor in reversed(IEC_UNITS):
        if abs(n) >= factor:
            return f"{n / factor:.4f}".rstrip("0").rstrip(".") + f" {name}"
    return f"{n:.0f} B"


def dual(n: float) -> str:
    return f"{human_si(n)} / {human_iec(n)}"


def size_block(title: str, formula: str, total_bytes: int, extra: Sequence[str] = ()) -> str:
    """把一个估算对象渲染成“公式 → 比特 → 字节 → 双单位”的推导块。"""
    lines = [f"{title}", f"  公式：{formula}", f"  = {num(total_bytes * 8)} bit",
             f"  ÷ 8 = {num(total_bytes)} B", f"  = {dual(total_bytes)}"]
    lines.extend(f"  {line}" for line in extra)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 三、演示与自检
# --------------------------------------------------------------------------
def demo_convert() -> str:
    out = [rule(), "一、数制转换：按权展开 / 除基取余 / 一位拆四位", rule()]
    out.append("[1] 二进制 10110101 → 十进制")
    out.append(convert_report("10110101", 2))
    out.append("[2] 十进制 255 → 十六进制")
    out.append(convert_report("255", 10, target=16))
    out.append("[3] 十六进制 1A → 二进制")
    out.append(convert_report("1A", 16, target=2))
    out.append("[4] Python 内置函数复核")
    pairs = [("int('10110101', 2)", int("10110101", 2)), ("hex(255)", hex(255)),
             ("int('1A', 16)", int("1A", 16)), ("bin(0x1A)", bin(0x1A))]
    out.append(table(["表达式", "结果"], [[k, v] for k, v in pairs], "<<"))
    return "\n".join(out)


def demo_size() -> str:
    img = image_bytes(1920, 1080, 24)
    aud = audio_bytes(240, 44100, 16, 2)
    vid = video_bytes(7200, 8)
    out = [rule(), "二、存储容量估算：先算字节，再换算单位", rule()]
    out.append(size_block(
        "[1] 1920×1080、24 位未压缩照片",
        "1920 × 1080 × 24 bit ÷ 8",
        img,
        [f"像素数 = 1920 × 1080 = {num(1920 * 1080)}",
         "结论：理论值 6.2 MB（5.9 MiB），JPEG 压缩后可降到 1 MB 量级"]))

    out.append("")
    out.append(size_block(
        "[2] 4 分钟、44.1 kHz / 16 bit / 双声道歌曲",
        "44100 × 16 × 2 × 240 s ÷ 8",
        aud,
        [f"每秒字节 = 44100 × 16 × 2 ÷ 8 = {num(44100 * 16 * 2 // 8)} B/s（CD 标准 176.4 KB/s）",
         f"1 分钟 = {human_si(audio_bytes(60, 44100, 16, 2))}"]))

    out.append("")
    out.append(size_block(
        "[3] 2 小时、8 Mbps 电影",
        "8 Mbit/s × 7200 s ÷ 8",
        vid,
        ["注意：8 Mbps 已是 H.264 压缩后的码流，不能再用 RGB 原始像素反推"]))

    out.append("")
    out.append("单位换算一览（同一份 6220800 B 的两种写法）")
    rows = [["十进制 SI", human_si(img)], ["二进制 IEC", human_iec(img)],
            ["差值", f"{(img / 10**6) / (img / 2**20):.4f} 倍"]]
    out.append(table(["口径", "数值"], rows, "<<"))
    return "\n".join(out)


def demo_extend(capacity_gb: float = 256, photo_mb: float = 4.0, reserve: float = 0.12) -> str:
    usable = capacity_gb * (1 - reserve)
    photos = usable * 10**9 / (photo_mb * 10**6)
    high = usable * 10**9 / (12 * 10**6)
    hours_4k = usable * 10**9 / (100 * 10**6 * 3600 / 8)
    out = [rule(), "三、拓展：256 GB 手机还能存多少张照片", rule()]
    out.append(f"  标称容量 {capacity_gb:g} GB，系统与缓存预留 {reserve:.0%} → 可用 {usable:.2f} GB"
               f"（{usable * 10**9 / 2**30:.2f} GiB）")
    out.append(table(
        ["场景", "单张/每小时体积", "可存数量"],
        [["日常 1200 万像素 JPEG", f"{photo_mb:g} MB", f"{photos:,.0f} 张"],
         ["高像素 4800 万像素 JPEG", "12 MB", f"{high:,.0f} 张"],
         ["4K / 100 Mbps 视频", "45 GB", f"{hours_4k:.1f} 小时"]], "<>>"))
    out.append("  取舍：照片按 4 MB 估算能存 5 万多张，但 4K 视频 1 小时就要 45 GB；")
    out.append("        拍摄前先按“码率 × 时长 ÷ 8”算账，给系统与备份留出余量。")
    return "\n".join(out)


def check() -> tuple[bool, str]:
    """把关键结果与实验指南的参考答案逐条比对。"""
    img = image_bytes(1920, 1080, 24)
    aud = audio_bytes(240, 44100, 16, 2)
    vid = video_bytes(7200, 8)
    cases = [
        ("10110101(2) → 十进制", 181, parse_int("10110101", 2)),
        ("255 → 十六进制", "FF", to_base(255, 16)),
        ("1A(16) → 十进制", 26, parse_int("1A", 16)),
        ("1920×1080×24bit", "6.2 MB", f"{img / 10**6:.1f} MB"),
        ("同一照片（IEC）", "5.9 MiB", f"{img / 2**20:.1f} MiB"),
        ("4 min / 44.1k / 16bit / 双声道", "42.3 MB", f"{aud / 10**6:.1f} MB"),
        ("2 h / 8 Mbps", "7.2 GB", f"{vid / 10**9:.1f} GB"),
    ]
    rows = []
    ok = True
    for name, want, got in cases:
        passed = str(want) == str(got)
        ok &= passed
        rows.append([name, want, got, "PASS" if passed else "FAIL"])
    text = table(["检查项", "参考答案", "脚本结果", "判定"], rows, "<^^^")
    return ok, text


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="estimate.py", description="第 01 讲：数制转换与存储容量估算验证脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"estimate.py {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_demo = sub.add_parser("demo", help="完整演示（数制转换 + 容量估算 + 拓展）")
    p_demo.add_argument("--only", choices=["convert", "size", "extend", "all"], default="all")

    p_conv = sub.add_parser("convert", help="进制转换并打印推导过程")
    p_conv.add_argument("value")
    p_conv.add_argument("--base", type=int, default=10, help="输入进制（默认 10）")
    p_conv.add_argument("--to", type=int, default=None, help="目标进制（可选）")

    p_img = sub.add_parser("image", help="估算未压缩照片体积")
    p_img.add_argument("width", type=int)
    p_img.add_argument("height", type=int)
    p_img.add_argument("--depth", type=int, default=24, help="位深（默认 24，即 RGB888）")

    p_aud = sub.add_parser("audio", help="估算 PCM 音频体积")
    p_aud.add_argument("--minutes", type=float, default=4)
    p_aud.add_argument("--rate", type=int, default=44100)
    p_aud.add_argument("--depth", type=int, default=16)
    p_aud.add_argument("--channels", type=int, default=2)

    p_vid = sub.add_parser("video", help="按码率估算视频体积")
    p_vid.add_argument("--hours", type=float, default=2)
    p_vid.add_argument("--mbps", type=float, default=8)

    p_ext = sub.add_parser("extend", help="拓展：手机可存照片数量")
    p_ext.add_argument("--capacity", type=float, default=256, help="标称容量 GB")
    p_ext.add_argument("--photo", type=float, default=4.0, help="单张照片 MB")
    p_ext.add_argument("--reserve", type=float, default=0.12, help="系统预留比例")

    sub.add_parser("check", help="与实验指南参考答案比对")

    args = parser.parse_args(argv)

    if args.command == "demo":
        blocks = []
        if args.only in ("convert", "all"):
            blocks.append(demo_convert())
        if args.only in ("size", "all"):
            blocks.append(demo_size())
        if args.only in ("extend", "all"):
            blocks.append(demo_extend())
        print(rule())
        print(f" 第 01 讲 实验验证脚本 v{__version__}    Python {platform.python_version()} / {platform.system()}")
        print("\n\n".join(blocks))
        return 0

    if args.command == "convert":
        print(convert_report(args.value, args.base, args.to))
        return 0

    if args.command == "image":
        total = image_bytes(args.width, args.height, args.depth)
        print(size_block(f"{args.width}×{args.height}、{args.depth} 位未压缩位图",
                         f"{args.width} × {args.height} × {args.depth} bit ÷ 8", total))
        return 0

    if args.command == "audio":
        seconds = args.minutes * 60
        total = audio_bytes(seconds, args.rate, args.depth, args.channels)
        print(size_block(f"{args.minutes:g} 分钟、{args.rate} Hz / {args.depth} bit / {args.channels} 声道",
                         f"{args.rate} × {args.depth} × {args.channels} × {seconds:g} s ÷ 8", total))
        return 0

    if args.command == "video":
        seconds = args.hours * 3600
        total = video_bytes(seconds, args.mbps)
        print(size_block(f"{args.hours:g} 小时、{args.mbps:g} Mbps",
                         f"{args.mbps:g} Mbit/s × {seconds:g} s ÷ 8", total))
        return 0

    if args.command == "extend":
        print(demo_extend(args.capacity, args.photo, args.reserve))
        return 0

    if args.command == "check":
        ok, text = check()
        print(text)
        print("全部通过：脚本结果与实验指南一致。" if ok else "存在不一致，请检查。")
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
