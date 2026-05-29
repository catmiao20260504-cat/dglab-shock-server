# Changelog

本文件记录所有重要版本变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [Unreleased]

### 待办
- WebSocket 多终端广播支持
- 波形编辑器 Web UI

---

## [1.0.0] - 2026-05-29

### 新增
- `server/dglab_server.py`：WebSocket 中继服务（端口 5678）
- HTTP REST API（端口 5679）：`/status`、`/cmd`、`/send` 三个接口
- CORS 支持，所有浏览器可直接跨域调用
- `apps/control-panel/`：通用强度/波形控制面板
- `apps/dino-game/`：小恐龙跑酷 × 死亡电击联动游戏
- `docs/API.md`：完整接口文档（Markdown）
- `docs/dglab_server_api.docx`：接口文档（Word 排版版）
- `docs/WAVEFORM.md`：波形格式说明与预设库

### 接口
- `POST /cmd`：自动路由，无需传 clientId/targetId
- `POST /send`：手动指定 targetId
- WebSocket 绑定握手协议完整实现
