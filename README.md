# 第 01 讲 实验：数制转换与存储容量估算

2026 秋《数字媒体程序设计》· 第 1 章 计算机原理 · 2 学时

本仓库是第 01 讲实验的完整提交物：把实验指南的 7 个步骤全部代码化，用手算 + 脚本 + 实测三方互证，
并给出可直接复现的压缩对比实验。

## 快速开始

```bash
# 1. 自检：把 7 项结果与实验指南的参考答案逐条比对
python estimate.py check

# 2. 完整演示（数制转换 / 容量估算 / 拓展）
python estimate.py demo

# 3. 单项计算
python estimate.py convert 10110101 --base 2
python estimate.py image 1920 1080 --depth 24
python estimate.py audio --minutes 4 --rate 44100 --depth 16 --channels 2
python estimate.py video --hours 2 --mbps 8
```

只依赖 Python 标准库（`estimate.py`）；生成测试图需要 `numpy` 与 `Pillow`。

## 结果一览

| 项目 | 计算式 | 结果（SI） | 结果（IEC） |
| --- | --- | --- | --- |
| 10110101₂ → 十进制 | 128+32+16+4+1 | **181** = 0xB5 | — |
| 255 → 十六进制 | 255÷16=15 余 F，15÷16=0 余 F | **FF₁₆** | — |
| 1A₁₆ → 二进制 | 1→0001，A→1010 | **11010₂** = 26 | — |
| 1920×1080×24 bit 照片 | 1920×1080×24÷8 | **6.2208 MB** | 5.9326 MiB |
| 4 min / 44.1 kHz / 16 bit / 双声道 | 44100×16×2×240÷8 | **42.336 MB** | 40.3748 MiB |
| 2 h / 8 Mbps 视频 | 8×10⁶×7200÷8 | **7.2 GB** | 6.7055 GiB |

压缩实测（同一内容换编码，`results/压缩对比.csv`）：

| 内容 | 未压缩 | PNG | JPEG q95 | JPEG q75 |
| --- | --- | --- | --- | --- |
| 界面截图 1080×2400 | 7.78 MB | 73.1 KB（106.3×） | 237.7 KB（32.7×） | 101.5 KB（76.6×） |
| 照片 1920×1080 | 6.22 MB | 3.66 MB（1.7×） | 1.35 MB（4.6×） | 154.2 KB（40.4×） |

> 结论：界面类图像 PNG 反而优于 JPEG，照片类则相反；「压缩后的体积」不能反推「未压缩体积」。

## 目录结构

```
lab01/
├─ estimate.py              # 主脚本：数制转换 + 容量估算 + 自检（CLI）
├─ tests/test_estimate.py   # 15 个单元测试
├─ tools/
│  ├─ make_test_images.py   # 生成测试图并实测 BMP/PNG/JPEG 体积
│  ├─ plot_compression.py   # 压缩对比图
│  └─ render_terminal.py    # 把命令输出渲染成报告插图
├─ docs/                    # 实验报告（docx / pdf）、一页结论
├─ assets/                  # 测试图、手机截图、报告插图
├─ results/                 # 运行记录与实测数据
└─ 提交说明.md               # Git / 网盘提交步骤
```

## 复现实验数据

```bash
python tools/make_test_images.py   # 重新生成 assets/ 与 results/压缩对比.csv
python -m unittest discover -s tests -v
```

## 许可

MIT，见 [LICENSE](LICENSE)。
