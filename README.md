# QR Reconstructor / QR 码重建工具

**从含 QR 码的图片中检测、增强、识别并重建内容。**

支持自动检测和手动框选两种定位方式，适配各种分辨率图片。

---

## 解决什么问题

日常工作中经常收到含 QR 码的文档截图，这些图片往往分辨率低、经过压缩，或者 QR 码嵌在表格/印章/文字中间。用手机扫码需要角度完美、光线合适，效率极低。

**QR Reconstructor** 自动识别图中的 QR 码位置，放大到可读级别，经过多步图像增强后解码，最终生成全新的高清 QR 码供你直接使用——全程在浏览器里完成，不需要安装任何 App。

---

## 效果

| 输入 | 输出 |
|------|------|
| 模糊/破损/小尺寸 QR 码图片 | 高清重建 QR 码 + 解码文本 |
| 多 QR 码混排文档 | 逐一裁剪、独立重建 |
| 自动检测不到 | 手动框选，兜底保证 |

## 功能

- 📷 **双引擎检测**：pyzbar + OpenCV 联合定位 QR 码
- 🔍 **预放大**：小图自适应放大提高检测率
- ✂️ **手动框选**：鼠标拖拽选区，人工精确调整
- ✨ **图像增强**：自适应对比度/锐化/去噪
- 📋 **内容重建**：去重 + 结构化展示
- 🌐 **Web 界面**：Flask + 原生前端，开箱即用

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

# 3. 打开浏览器
# http://localhost:8080
```

Windows 用户也可双击 `start.bat` 启动。

## 项目结构

```
qr-reconstructor/
├── app.py                  # Flask 主入口
├── core/
│   ├── pipeline.py         # 核心流水线（检测→增强→识别→重建）
│   ├── enhancer.py         # 图像增强模块
│   ├── recognizer.py       # QR 码识别模块
│   └── reconstructor.py    # 内容重建 + 去重
├── templates/
│   └── index.html          # Web 前端页面
├── static/
│   └── style.css           # 样式表
├── tests/                  # 单元测试
├── LICENSE                 # 许可证
└── requirements.txt        # Python 依赖
```

## 许可证

**双重许可 (Dual-License)**

- **默认**：非商业使用许可 — 自由用于个人、学习、非商业分享
- **商业使用**：需联系作者获取授权

详见 [LICENSE](./LICENSE) 文件。

## 作者

**80s-mouzhai** — [github.com/80s-mouzhai](https://github.com/80s-mouzhai)

> 欢迎技术交流与指导

---

© 2026 80s-mouzhai
