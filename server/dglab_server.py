#!/usr/bin/env python3
"""
DG-Lab 郊狼 3.0 WebSocket 测试服务端
基于官方 Socket 协议文档实现
支持郊狼 App 扫码连接 + HTML 控制面板

使用方法：
  pip install websockets qrcode[pil]
  python dglab_server.py

然后用郊狼 App "扫码连接" 扫描终端输出的二维码，
并在浏览器中打开 dglab_panel.html 进行控制。
"""

import asyncio
import json
import uuid
import logging
import argparse
import socket
import sys
from datetime import datetime

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("请先安装依赖: pip install websockets qrcode[pil]")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("dglab")

# ─── 全局状态 ────────────────────────────────────────────────────────────────

# ws_id → WebSocket 连接
clients: dict[str, WebSocketServerProtocol] = {}

# app_id → terminal_id  （郊狼 App 已绑定的终端）
bindings: dict[str, str] = {}

# 终端 id → app_id 反查
reverse_bindings: dict[str, str] = {}

# 设备状态缓存（供前端查询）
device_state: dict[str, dict] = {}

# HTML 控制终端的 ws_id（最后一个连接的终端）
terminal_id: str | None = None

# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def make_msg(type_: str, client_id: str, target_id: str, message: str) -> str:
    """构造协议 JSON 字符串"""
    return json.dumps({
        "type": type_,
        "clientId": client_id,
        "targetId": target_id,
        "message": message,
    }, ensure_ascii=False)


def log_event(event: str, data: dict | None = None):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    msg = f"[{ts}] {event}"
    if data:
        msg += " | " + json.dumps(data, ensure_ascii=False)
    log.info(msg)


def print_qrcode(ws_url: str):
    """在终端打印二维码（郊狼 App 扫描用）"""
    try:
        import qrcode  # type: ignore
        qr = qrcode.QRCode(border=1)
        qr.add_data(ws_url)
        qr.make(fit=True)
        print("\n── 郊狼 App 扫码连接 ──")
        qr.print_ascii(invert=True)
        print(f"URL: {ws_url}\n")
    except ImportError:
        print(f"\n请安装 qrcode 库以显示二维码: pip install qrcode[pil]")
        print(f"App 连接 URL: {ws_url}\n")


# ─── WebSocket 处理 ───────────────────────────────────────────────────────────

async def handler(ws: WebSocketServerProtocol):
    """每个 WebSocket 连接的处理协程"""
    global terminal_id

    # 分配 clientId
    cid = str(uuid.uuid4())
    clients[cid] = ws
    log_event("连接建立", {"clientId": cid})

    # 发送 clientId 给对端
    await ws.send(make_msg("bind", cid, "", "targetId"))
    log_event("发送 clientId", {"clientId": cid})

    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                log.warning(f"无效 JSON: {raw[:200]}")
                continue

            await dispatch(ws, cid, data)

    except websockets.exceptions.ConnectionClosed as e:
        log_event("连接断开", {"clientId": cid, "reason": str(e)})
    finally:
        clients.pop(cid, None)
        # 清理绑定关系
        app_id = reverse_bindings.pop(cid, None)
        if app_id:
            bindings.pop(app_id, None)
            log_event("绑定解除(终端断开)", {"terminalId": cid, "appId": app_id})
        # 如果是 App 断开
        for aid, tid in list(bindings.items()):
            if aid == cid:
                reverse_bindings.pop(tid, None)
                bindings.pop(aid, None)
                log_event("绑定解除(App断开)", {"appId": aid, "terminalId": tid})
        if terminal_id == cid:
            terminal_id = None


async def dispatch(ws: WebSocketServerProtocol, cid: str, data: dict):
    """处理协议消息"""
    global terminal_id

    msg_type = data.get("type", "")
    client_id = data.get("clientId", "")
    target_id = data.get("targetId", "")
    message = data.get("message", "")

    log_event(f"收到 type={msg_type}", {"from": cid, "message": str(message)[:120]})

    # ── 绑定请求（App 或终端发起）──────────────────────────────────────────
    if msg_type == "bind":
        if message == "targetId":
            # 终端注册自己（HTML 控制面板连上来）
            terminal_id = cid
            log_event("终端注册", {"terminalId": cid})
            # 通知前端已就绪，等待 App 扫码
            await ws.send(make_msg("bind", cid, "", "200"))

        elif message.startswith("targetId:"):
            # App 发来绑定请求，带着它想绑定的 terminalId
            app_id = cid  # App 的 clientId 就是当前连接
            wanted_terminal = message.split(":", 1)[1]
            # 记录绑定
            bindings[app_id] = wanted_terminal
            reverse_bindings[wanted_terminal] = app_id
            log_event("App 绑定成功", {"appId": app_id, "terminalId": wanted_terminal})
            # 回复 App 200
            await ws.send(make_msg("bind", app_id, wanted_terminal, "200"))
            # 通知对应终端绑定成功
            if wanted_terminal in clients:
                await clients[wanted_terminal].send(
                    make_msg("bind", wanted_terminal, app_id, "200")
                )
            # 推送初始强度给终端
            await push_heartbeat(app_id, wanted_terminal)

    # ── 强度/波形上报（App → 终端转发）──────────────────────────────────────
    elif msg_type == "msg":
        # 查找转发目标
        forward_to = bindings.get(client_id) or reverse_bindings.get(client_id)
        if not forward_to:
            log.warning(f"无法转发：{client_id} 未绑定")
            return

        # 缓存设备状态（强度类消息）
        if message.startswith("strength-"):
            _parse_strength(client_id, message)

        if forward_to in clients:
            await clients[forward_to].send(
                make_msg("msg", client_id, forward_to, message)
            )
            log_event("转发消息", {"from": client_id, "to": forward_to, "msg": message[:80]})

    # ── 心跳 ─────────────────────────────────────────────────────────────────
    elif msg_type == "heartbeat":
        await ws.send(make_msg("heartbeat", cid, target_id, "200"))


async def push_heartbeat(app_id: str, terminal_id: str):
    """App 绑定后，向终端推送一次强度查询（触发 App 上报当前强度）"""
    if terminal_id in clients:
        await clients[terminal_id].send(
            make_msg("msg", terminal_id, app_id, "strength-0+0+0+0")
        )


def _parse_strength(client_id: str, message: str):
    """解析 strength 消息，缓存状态"""
    # strength-A+B+maxA+maxB
    try:
        _, vals = message.split("-", 1)
        parts = vals.split("+")
        if len(parts) >= 2:
            device_state[client_id] = {
                "a": int(parts[0]),
                "b": int(parts[1]),
                "maxA": int(parts[2]) if len(parts) > 2 else 200,
                "maxB": int(parts[3]) if len(parts) > 3 else 200,
                "updated": datetime.now().isoformat(),
            }
    except Exception:
        pass


# ─── HTTP REST 端点（给前端用，内嵌在同一 WS 服务里）───────────────────────
# 这里用一个独立的轻量 HTTP 服务暴露状态接口

async def http_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """极简 HTTP 服务，支持 CORS，给前端轮询状态用"""
    try:
        raw = await asyncio.wait_for(reader.read(4096), timeout=5)
        req = raw.decode(errors="replace")
        first_line = req.split("\r\n")[0]
        method, path, *_ = first_line.split(" ")

        if method == "OPTIONS":
            # CORS preflight
            resp = (
                "HTTP/1.1 204 No Content\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type\r\n"
                "Content-Length: 0\r\n"
                "Connection: close\r\n\r\n"
            )
            writer.write(resp.encode())
            await writer.drain()
            return

        body = "{}"
        status = "200 OK"

        if path == "/status":
            body = json.dumps({
                "terminals": list(clients.keys()),
                "bindings": bindings,
                "deviceState": device_state,
                "terminalId": terminal_id,
            }, ensure_ascii=False)
        elif path == "/cmd" and method == "POST":
            # /cmd  —— 自动使用当前已绑定终端，无需传 targetId
            body_raw = req.split("\r\n\r\n", 1)[-1] if "\r\n\r\n" in req else "{}"
            try:
                payload = json.loads(body_raw)
                msg = payload.get("message", "")
                tid = terminal_id
                app_id = reverse_bindings.get(tid) if tid else None
                if tid and app_id and tid in clients:
                    await clients[tid].send(make_msg("msg", tid, app_id, msg))
                    body = json.dumps({"ok": True, "sent": msg})
                    log_event("/cmd 发送", {"msg": msg[:60]})
                else:
                    body = json.dumps({"ok": False, "error": "未绑定或终端不存在"})
                    status = "400 Bad Request"
            except Exception as e:
                body = json.dumps({"ok": False, "error": str(e)})
                status = "500 Internal Server Error"

        elif path == "/send" and method == "POST":
            # POST /send  body: {"targetId":"...", "message":"..."}
            body_raw = req.split("\r\n\r\n", 1)[-1] if "\r\n\r\n" in req else "{}"
            try:
                payload = json.loads(body_raw)
                tid = payload.get("targetId", "")
                msg = payload.get("message", "")
                app_id = reverse_bindings.get(tid) or bindings.get(tid)
                if tid in clients and app_id:
                    await clients[tid].send(
                        make_msg("msg", tid, app_id, msg)
                    )
                    body = json.dumps({"ok": True, "sent": msg})
                else:
                    body = json.dumps({"ok": False, "error": "目标不存在或未绑定"})
                    status = "400 Bad Request"
            except Exception as e:
                body = json.dumps({"ok": False, "error": str(e)})
                status = "500 Internal Server Error"
        else:
            status = "404 Not Found"
            body = json.dumps({"error": "not found"})

        resp = (
            f"HTTP/1.1 {status}\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
            "Access-Control-Allow-Headers: Content-Type\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            "Connection: close\r\n\r\n"
            + body
        )
        writer.write(resp.encode())
        await writer.drain()
    except Exception as e:
        log.debug(f"HTTP handler error: {e}")
    finally:
        writer.close()


# ─── 主入口 ──────────────────────────────────────────────────────────────────

async def main(ws_port: int, http_port: int):
    local_ip = get_local_ip()
    ws_url = f"ws://{local_ip}:{ws_port}"

    print("=" * 55)
    print("  DG-Lab 郊狼 WebSocket 测试服务端")
    print("=" * 55)
    print(f"  WebSocket: {ws_url}")
    print(f"  HTTP API : http://{local_ip}:{http_port}/status")
    print(f"  控制面板 : 用浏览器打开 dglab_panel.html")
    print("=" * 55)

    # 打印二维码供 App 扫描
    print_qrcode(ws_url)

    # 启动 WebSocket 服务
    ws_server = await websockets.serve(handler, "0.0.0.0", ws_port)

    # 启动 HTTP 服务
    http_server = await asyncio.start_server(http_handler, "0.0.0.0", http_port)

    log.info(f"WebSocket 服务已启动，等待连接... (Ctrl+C 退出)")
    async with ws_server, http_server:
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DG-Lab WebSocket 测试服务端")
    parser.add_argument("--ws-port", type=int, default=5678, help="WebSocket 端口 (默认 5678)")
    parser.add_argument("--http-port", type=int, default=5679, help="HTTP API 端口 (默认 5679)")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.ws_port, args.http_port))
    except KeyboardInterrupt:
        print("\n服务已停止")
