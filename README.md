# qrflow / QR 码重建工具

**从含 QR 码的图片中检测、增强、识别并重建内容。**

支持自动检测和手动框选两种定位方式，适配各种分辨率图片。

---

## 解决什么问题

日常工作中经常收到含 QR 码的文档截图，这些图片往往分辨率低、经过压缩，或者 QR 码嵌在表格/印章/文字中间。用手机扫码需要角度完美、光线合适，效率极低。

**qrflow** 自动识别图中的 QR 码位置，放大到可读级别，经过多步图像增强后解码，最终生成全新的高清 QR 码供你直接使用——全程在浏览器里完成，不需要安装任何 App。

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
- ✨ **图像增强**：7 步增强流水线（对比度/去噪/二值化/形态学/透视矫正/超分辨率）
- 🧩 **多方案识别**：pyzbar / OpenCV / WeChat QR / zxing-cpp 四后端自动切换
- 📋 **内容重建**：去重 + 高清 QR 码生成
- 🌐 **Web 界面**：FastAPI + 原生前端，开箱即用

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 启动服务
uv run python -m qrflow.cli serve

# 3. 或通过 CLI 自定义参数
uv run qrflow serve -p 3000 --debug
```

也可以构建为 wheel 安装后使用：

```bash
uv build
pip install dist/qrflow-*.whl
qrflow serve -p 8080
```

## CLI 使用

```bash
qrflow serve --help

# 选项
#   -h, --host         绑定地址 (默认 0.0.0.0)
#   -p, --port         端口 (默认 8080)
#   --debug            调试模式 (热重载)
#   --upload-dir       上传目录
#   --output-dir       输出目录
#   --max-upload-mb    最大上传大小 (MB)
#   --no-browser       不自动打开浏览器

# 环境变量
QRFLOW_PORT=3000 qrflow serve
```

## 项目结构

```
qrflow/
├── pyproject.toml              # 项目元数据 + 依赖
├── uv.lock                     # 依赖锁文件
├── src/qrflow/
│   ├── cli.py                  # typer CLI 入口
│   ├── main.py                 # 应用启动
│   ├── api/                    # FastAPI 路由层
│   │   └── routes/             # upload / detect / process / crop
│   ├── core/                   # 核心业务
│   │   ├── pipeline.py         # 编排器
│   │   ├── protocols.py        # 组件接口协议
│   │   ├── enhance/            # 增强步骤 (7 个, 策略模式)
│   │   ├── recognize/          # 识别后端 (4 个, 策略模式)
│   │   └── reconstruct/        # 去重 + QR 生成
│   ├── config/settings.py      # pydantic-settings 配置
│   └── utils/                  # 工具函数
├── templates/index.html        # Web 前端
├── static/style.css            # 样式
└── tests/                      # pytest (42 用例)
```

## 许可证

[MIT](./LICENSE)

## 作者

**jianjunwu** — [github.com/jianjunwu/qrflow](https://github.com/jianjunwu/qrflow)

> 欢迎技术交流与指导

---

© 2026 jianjunwu
