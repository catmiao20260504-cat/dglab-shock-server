# DG-Lab Shock Server · 接口文档

> Version: 1.0.0 · WebSocket Port: 5678 · HTTP Port: 5679 · 仅支持郊狼 3.0

---

## 目录

1. [系统架构](#1-系统架构)
2. [HTTP API](#2-http-api)
   - [GET /status](#21-get-status)
   - [POST /cmd](#22-post-cmd--推荐)
   - [POST /send](#23-post-send)
3. [WebSocket 接口](#3-websocket-接口)
   - [消息格式](#31-消息通用格式)
   - [绑定握手](#32-绑定握手流程)
   - [心跳保活](#33-心跳保活)
4. [指令参考](#4-指令参考)
   - [强度控制](#41-强度控制-strength)
   - [波形下发](#42-波形下发-pulse)
   - [清除指令](#43-清除指令-clear)
5. [错误码](#5-错误码)
6. [代码示例](#6-代码示例)

---

## 1. 系统架构

```
郊狼 App（被控端）
        │
        │  WebSocket  ws://IP:5678
        ▼
┌─────────────────────────┐
│   dglab_server.py       │  ← 中继服务（本地运行）
│   WebSocket :5678       │
│   HTTP API  :5679       │
└─────────────────────────┘
        │
        ├── WebSocket  ← 控制终端（HTML / 游戏）
        └── HTTP REST  ← 外部脚本 / 小程序（推荐）
```

**两种接入方式：**

| 方式 | 地址 | 适合场景 |
|------|------|----------|
| HTTP REST API | `http://IP:5679` | 脚本、网页、触发式控制（推荐） |
| WebSocket | `ws://IP:5678` | 需要实时双向通信的终端 |

---

## 2. HTTP API

所有接口支持 CORS，响应为 UTF-8 JSON。

### 2.1 GET /status

查询当前连接状态与设备强度。

**请求**

```
GET http://localhost:5679/status
```

**响应示例**

```json
{
  "terminals": ["uuid-terminal-1"],
  "bindings": {
    "uuid-app-1": "uuid-terminal-1"
  },
  "deviceState": {
    "uuid-app-1": {
      "a":       20,
      "b":       10,
      "maxA":    100,
      "maxB":    100,
      "updated": "2026-05-28T12:00:00"
    }
  },
  "terminalId": "uuid-terminal-1"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `terminals` | `string[]` | 已注册控制终端的 UUID 列表 |
| `bindings` | `object` | App UUID → Terminal UUID 绑定映射 |
| `deviceState` | `object` | 设备当前强度（a/b）及上限（maxA/maxB） |
| `terminalId` | `string\|null` | 当前活跃终端 ID，`/cmd` 自动路由目标 |

---

### 2.2 POST /cmd  ★推荐

自动路由指令。服务端自动查找当前绑定的终端，无需传 ID。**外部程序首选接口。**

**请求**

```
POST http://localhost:5679/cmd
Content-Type: application/json

{ "message": "strength-20+10+3+3" }
```

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | `string` | ✅ | 指令内容，见第 4 章 |

**响应**

```json
// 成功 HTTP 200
{ "ok": true, "sent": "strength-20+10+3+3" }

// 失败 HTTP 400（未绑定）
{ "ok": false, "error": "未绑定或终端不存在" }
```

---

### 2.3 POST /send

手动指定 targetId 的精确路由接口。适合多终端场景。

**请求**

```
POST http://localhost:5679/send
Content-Type: application/json

{
  "targetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "message":  "strength-30+20+3+3"
}
```

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `targetId` | `string` | ✅ | 目标终端 UUID，从 `/status` 获取 |
| `message` | `string` | ✅ | 指令内容 |

---

## 3. WebSocket 接口

地址：`ws://IP:5678`  
消息格式：UTF-8 JSON，单条最大 1950 字节。

### 3.1 消息通用格式

```json
{
  "type":     "msg | bind | heartbeat",
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "targetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "message":  "指令内容字符串"
}
```

| type | 方向 | 说明 |
|------|------|------|
| `bind` | 双向 | 连接注册与绑定握手 |
| `msg` | 终端 → App | 下发控制指令 |
| `msg` | App → 终端 | 上报设备当前强度 |
| `heartbeat` | 双向 | 保活，服务端回 `message: "200"` |

---

### 3.2 绑定握手流程

```
① 服务端 → 终端   type=bind  message="targetId"          分配 clientId
② 终端 → 服务端   type=bind  message="targetId"          注册为控制终端
③ 服务端 → 终端   type=bind  message="200"               App 扫码成功，绑定完成
④ 终端 → App      type=msg   message="strength-..."      开始下发指令
```

**JavaScript 示例**

```js
const ws = new WebSocket('ws://localhost:5678');
let myId, appId;

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);

  // ① 收到 clientId
  if (msg.type === 'bind' && !myId) {
    myId = msg.clientId;
    // ② 注册为终端
    ws.send(JSON.stringify({ type: 'bind', clientId: myId, targetId: '', message: 'targetId' }));
  }

  // ③ 绑定成功
  if (msg.type === 'bind' && msg.message === '200' && msg.targetId) {
    appId = msg.targetId;
  }
};

// ④ 发送指令
function send(message) {
  ws.send(JSON.stringify({ type: 'msg', clientId: myId, targetId: appId, message }));
}
```

---

### 3.3 心跳保活

建议每 25 秒发送一次：

```json
{ "type": "heartbeat", "clientId": "<id>", "targetId": "<id>", "message": "" }
```

服务端回应：`{ "type": "heartbeat", ..., "message": "200" }`

---

## 4. 指令参考

以下指令均填写在 `message` 字段，通过 HTTP `/cmd` 或 WebSocket `msg` 下发。

---

### 4.1 强度控制 (strength)

**格式：** `strength-A+B+opA+opB`

| 参数 | 范围 | 说明 |
|------|------|------|
| A | 0 ~ 200 | A 通道操作数值 |
| B | 0 ~ 200 | B 通道操作数值 |
| opA | 0 / 1 / 2 / 3 | A 通道操作模式 |
| opB | 0 / 1 / 2 / 3 | B 通道操作模式 |

**op 模式说明：**

| op | 效果 | 示例（当前强度=10，值=5） |
|----|------|--------------------------|
| 0 | 不操作，保持当前强度 | 保持 10 |
| 1 | 相对增加 | 10 + 5 = 15 |
| 2 | 相对减少 | 10 − 5 = 5 |
| 3 | 直接设置（推荐） | 直接变为 5 |

**常用速查：**

```
"strength-20+10+3+3"   → A=20 B=10（绝对值）
"strength-0+0+3+3"     → 归零 / 紧急停止
"strength-5+0+1+0"     → A 增加 5，B 不变
"strength-0+5+0+1"     → A 不变，B 增加 5
"strength-5+5+2+2"     → A、B 各减少 5
"strength-30+0+3+0"    → 仅设置 A=30，B 不变
```

---

### 4.2 波形下发 (pulse)

**格式：** `pulse-x:["hex1","hex2","hex3","hex4"]`

- `x`：通道，`a` 或 `b`
- 每帧为 16 进制字符串，最多 4 帧/次，每 100ms 自动消耗一帧

**内置波形 HEX 参考：**

| 波形 | HEX 帧 | 特征 |
|------|--------|------|
| 连续稳定 | `1E9082B46464646464646464646464640000FF00` | 持续均匀 |
| 脉冲节奏 | `14508000000000000000000000000000FFFFFF00` | 短促跳动 |
| 呼吸渐变 | `145082B41414141414141414141414140000FF00` | 渐强渐弱 |
| 强力冲击 | `3C9082B43C3C3C3C3C3C3C3C3C3C3C3C3CFFFFFF` | 高强度 |

**示例：**

```
pulse-a:["1E9082B46464646464646464646464640000FF00","1E9082B46464646464646464646464640000FF00"]
pulse-b:["14508000000000000000000000000000FFFFFF00"]
```

> ⚠️ pulse 只写波形队列，不改变强度。请先用 `strength` 设置强度，再下发波形。

---

### 4.3 清除指令 (clear)

| 指令 | 作用 |
|------|------|
| `clear-a` | 清除 A 通道波形队列 |
| `clear-b` | 清除 B 通道波形队列 |

**完全停止输出（三条连发）：**

```
strength-0+0+3+3
clear-a
clear-b
```

---

## 5. 错误码

| HTTP 状态 | error 字段 | 原因 | 解决 |
|-----------|-----------|------|------|
| 400 | 未绑定或终端不存在 | App 未扫码 / 终端未注册 | 检查 App 扫码和终端 WS 连接 |
| 400 | 目标不存在或未绑定 | /send 的 targetId 无效 | 重新从 /status 获取 |
| 500 | （具体异常） | 服务端内部错误 | 查看终端日志 |
| - | Connection refused | 服务端未启动 | `python server/dglab_server.py` |

---

## 6. 代码示例

### JavaScript（HTTP，最简）

```js
const BASE = 'http://localhost:5679';

async function cmd(message) {
  const r = await fetch(`${BASE}/cmd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  return r.json();
}

// 触发电击
async function shock(a = 20, b = 10, ms = 1500) {
  const frame = '1E9082B46464646464646464646464640000FF00';
  await cmd(`strength-${a}+${b}+3+3`);
  await cmd(`pulse-a:["${frame}","${frame}"]`);
  await cmd(`pulse-b:["${frame}","${frame}"]`);
  setTimeout(async () => {
    await cmd('strength-0+0+3+3');
    await cmd('clear-a');
    await cmd('clear-b');
  }, ms);
}
```

### Python

```python
import requests, time

BASE = 'http://localhost:5679'

def cmd(message):
    return requests.post(f'{BASE}/cmd', json={'message': message}, timeout=3).json()

def shock(a=20, b=10, duration=1.5):
    frame = '1E9082B46464646464646464646464640000FF00'
    cmd(f'strength-{a}+{b}+3+3')
    cmd(f'pulse-a:["{frame}","{frame}"]')
    cmd(f'pulse-b:["{frame}","{frame}"]')
    time.sleep(duration)
    cmd('strength-0+0+3+3')
    cmd('clear-a')
    cmd('clear-b')
```

### cURL

```bash
# 查状态
curl http://localhost:5679/status

# 设强度
curl -X POST http://localhost:5679/cmd \
  -H "Content-Type: application/json" \
  -d '{"message":"strength-20+10+3+3"}'

# 紧急停止
curl -X POST http://localhost:5679/cmd \
  -H "Content-Type: application/json" \
  -d '{"message":"strength-0+0+3+3"}'
```

---

*DG-Lab Shock Server · v1.0.0 · MIT License · 仅支持郊狼 3.0*
