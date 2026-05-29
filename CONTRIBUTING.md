# 贡献指南

欢迎为 DG-Lab Shock Server 贡献代码或小程序！本文说明如何参与。

---

## 贡献方式

| 类型 | 说明 |
|------|------|
| 🐛 Bug 修复 | 修复服务端或现有 app 的问题 |
| ⚡ 新小程序 | 在 `apps/` 下添加新的 HTML 应用 |
| 📄 文档改进 | 完善 API 文档、README 或注释 |
| 🌊 新波形 | 向 `docs/WAVEFORM.md` 贡献波形预设 |

---

## 提交新小程序

### 文件结构要求

每个小程序放在 `apps/<你的应用名>/` 目录下：

```
apps/your-app/
├── index.html      # 主文件（必须，单文件 HTML）
└── README.md       # 应用说明（必须）
```

### README.md 必须包含

```markdown
# 应用名称

一句话描述这个应用做什么。

## 功能
- 功能 1
- 功能 2

## 使用方法
1. 启动服务端
2. 打开 index.html
3. ...

## 电击触发条件
说明什么情况下会触发电击，默认强度是多少。

## 依赖
- dglab_server.py（HTTP API /cmd 接口）
```

### 提交流程

```bash
# 1. Fork 本仓库
# 2. 创建分支
git checkout -b app/your-app-name

# 3. 添加文件
apps/your-app/index.html
apps/your-app/README.md

# 4. 提交
git add apps/your-app/
git commit -m "app: add your-app-name"

# 5. 发起 Pull Request，标题格式：
# [App] 应用名称 - 一句话描述
```

---

## 代码规范

**服务端（Python）**
- 遵循 PEP 8
- 新增接口须同步更新 `docs/API.md`
- 提交前确认能通过 `python server/dglab_server.py` 正常启动

**小程序（HTML）**
- 单文件，CSS/JS 均内嵌
- 不引用外部资源（可使用 CDN 的公开字体/图标库）
- 接入服务端只使用 `POST /cmd` 接口，不硬编码 clientId/targetId
- 页面需提供服务端地址输入框，默认值 `http://localhost:5679`

---

## Issue 规范

- Bug：使用 Bug Report 模板，附上操作系统、Python 版本、错误日志
- 新功能：说明使用场景和预期效果
- 新小程序想法：使用 New App 模板

---

## 行为准则

- 本项目仅供**个人娱乐和学习**使用
- 禁止提交任何涉及未成年人、非自愿使用的内容
- 禁止提交用于远程未授权控制他人设备的功能
