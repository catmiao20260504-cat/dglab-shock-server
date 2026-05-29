# ⚡ DG-Lab Shock Server

> 郊狼 3.0 WebSocket 中继服务 + 开放接口 · 用于游戏、小程序与脚本二次开发

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![WebSocket](https://img.shields.io/badge/WebSocket-5678-purple.svg)]()
[![HTTP API](https://img.shields.io/badge/HTTP_API-5679-cyan.svg)]()

---

## 目录

- [项目简介](#项目简介)
- [快速开始](#快速开始)
- [仓库结构](#仓库结构)
- [接口文档](#接口文档)
- [应用列表](#应用列表)
- [二次开发](#二次开发)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

本项目是一个运行在本地的 **WebSocket 中继服务**，基于 [DG-LAB 官方 Socket 协议](https://github.com/DG-LAB-OPENSOURCE/DG-LAB-OPENSOURCE)实现。

核心功能：
- 郊狼 App 通过扫码与服务端建立 WebSocket 连接
- 第三方程序（网页 / 游戏 / 脚本）通过 **HTTP API** 或 **WebSocket** 向设备下发强度与波形指令
- 所有接口标准化、文档化，方便社区持续扩展小程序

**支持设备：** DG-Lab 郊狼 3.0  
**支持系统：** Windows / macOS / Linux

---

## 快速开始

### 1. 安装依赖

```bash
pip install 'websockets' 'qrcode[pil]'
```

### 2. 启动服务端

```bash
python server/dglab_server.py
```

终端会打印二维码，用**郊狼 App → Socket 控制 → 扫码连接**扫描。

### 3. 验证连接

```bash
curl http://localhost:5679/status
```

返回 `bindings` 非空则说明 App 已成功绑定。

### 4. 发送第一条指令

```bash
# 设置 A 通道强度 20，B 通道 10
curl -X POST http://localhost:5679/cmd \
  -H "Content-Type: application/json" \
  -d '{"message":"strength-20+10+3+3"}'
```

---

## 仓库结构

```
dglab-shock-server/
│
├── server/                     # 核心服务端
│   ├── dglab_server.py         # WebSocket + HTTP 中继服务（主程序）
│   └── requirements.txt        # Python 依赖
│
├── apps/                       # 小程序集合（每个子目录为一个独立应用）
│   ├── control-panel/          # 通用控制面板
│   │   └── index.html
│   ├── dino-game/              # 小恐龙跑酷 × 电击联动
│   │   └── index.html
│   └── _template/              # 新应用开发模板
│       ├── index.html
│       └── README.md
│
├── docs/                       # 文档
│   ├── API.md                  # 接口文档（纯文本 Markdown 版）
│   ├── dglab_server_api.docx   # 接口文档（Word 排版版）
│   └── WAVEFORM.md             # 波形格式说明
│
├── scripts/                    # 辅助脚本
│   └── test_connection.py      # 快速连接测试脚本
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── new_app.md          # 提交新小程序的 Issue 模板
│   └── workflows/
│       └── validate.yml        # CI：检查新提交的 app 文件结构
│
├── CHANGELOG.md                # 版本更新记录
├── CONTRIBUTING.md             # 贡献指南
├── LICENSE                     # MIT License
└── README.md                   # 本文件
```

---

## 接口文档

完整接口文档见 [`docs/API.md`](docs/API.md)

| 接口 | 地址 | 说明 |
|------|------|------|
| WebSocket | `ws://IP:5678` | 郊狼 App 扫码 + 终端双向通信 |
| `GET /status` | `http://IP:5679/status` | 查询连接与设备强度状态 |
| `POST /cmd` | `http://IP:5679/cmd` | **推荐** 自动路由指令（无需 ID） |
| `POST /send` | `http://IP:5679/send` | 手动指定 targetId 发送（高级） |

**最简接入（任何语言）：**

```js
fetch('http://localhost:5679/cmd', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'strength-20+10+3+3' })
})
```

---

## 应用列表

| 应用 | 路径 | 描述 |
|------|------|------|
| 通用控制面板 | `apps/control-panel/` | 强度调节、波形选择、日志查看 |
| 小恐龙跑酷 | `apps/dino-game/` | 死亡触发电击，可调通道强度与波形 |
| _(你的应用)_ | `apps/your-app/` | 欢迎提交 PR！ |

---

## 二次开发

任何 HTML 页面只需以下代码即可接入，详见 [`docs/API.md`](docs/API.md)：

```python
# Python
import requests
requests.post('http://localhost:5679/cmd', json={'message': 'strength-20+10+3+3'})
```

开发新小程序请参考 [`apps/_template/`](apps/_template/) 模板，提交时附上独立的 `README.md`。

---

## 贡献指南

见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 许可证

[MIT License](LICENSE) · 本项目与 DG-LAB 官方无关，仅供学习与个人娱乐使用。

> ⚠️ **安全提示**：服务端默认监听局域网所有设备。请在受信任的网络环境中使用，切勿暴露至公网。
