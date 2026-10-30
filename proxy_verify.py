#!/usr/bin/env python3
"""
本地后端代理 · 安全验证骨架 (MODEL_PROXY_CHECKLIST.md 证据用)
仅用于校验：监听暴露 / 来源 / 鉴权 / CSRF-DNS-rebinding。不接任何模型。

部署决策（清单 §4 备选说明）：
  采用「明文 HTTP 仅回环」http://127.0.0.1:PORT。
  依据：流量不出本机、密钥不落地（仅存内存）；残留风险=本机恶意进程嗅探回环，
  由 §2 高熵令牌 + §5 进程归属缓解。若要求 HTTPS，请替换 TLS 层并补齐证书信任证据。
"""
import http.server
import secrets
import os
import sys
import json
import threading

BIND_HOST = "127.0.0.1"  # 严格单栈 IPv4 回环；绝不使用 0.0.0.0 / 其他网卡
BIND_PORT = int(os.environ.get("PROXY_PORT", "8123"))

# 令牌：优先读环境变量（生产/CI 不打印）；否则内存生成、仅本次启动打印一次
ENV_TOKEN = os.environ.get("PROXY_TOKEN")
AUTH_TOKEN = ENV_TOKEN if ENV_TOKEN else secrets.token_hex(32)
_TOKEN_PRINTED = not ENV_TOKEN

# 来源模型（清单 §0）：True=支持 file:// (Origin: null, 仅靠令牌)；False=仅代理同源
ALLOW_NULL_ORIGIN = os.environ.get("ALLOW_NULL_ORIGIN", "1") == "1"
ALLOWED_ORIGIN = f"http://{BIND_HOST}:{BIND_PORT}"


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "secure-proxy"  # 弱化版本指纹
    sys_version = ""

    def _deny(self, code):
        # 安全失败：不回显具体原因，避免给攻击者区分 Host/Token/Origin
        body = b"Access Denied"
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self):
        # 1) Host 精确校验（防 DNS rebinding）—— 只认 127.0.0.1:PORT
        host = self.headers.get("Host", "")
        if host != f"{BIND_HOST}:{BIND_PORT}":
            return False, 400
        # 2) Origin 校验
        origin = self.headers.get("Origin")
        if origin == "null":
            if not ALLOW_NULL_ORIGIN:
                return False, 403
        elif origin:
            if origin != ALLOWED_ORIGIN:
                return False, 403
        # 3) 令牌（短期高熵、不可预测、可撤销；timing-safe 比较）
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False, 401
        tok = auth.split(" ", 1)[1]
        if not secrets.compare_digest(tok, AUTH_TOKEN):
            return False, 401
        return True, 200

    def do_POST(self):
        ok, code = self._auth_ok()
        if not ok:
            self._deny(code)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        # 方案 B：file:// 跨源读取需显式放行 null
        origin = self.headers.get("Origin")
        if origin == "null" and ALLOW_NULL_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", "null")
            self.send_header("Access-Control-Allow-Headers", "Authorization")
        body = json.dumps(
            {"status": "verified", "evidence": "Proxy skeleton verification passed."}
        ).encode()
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # 方法约束：状态变更接口仅 POST；GET 显式拒绝
        body = b"Method Not Allowed"
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # 日志脱敏：仅记录方法+路径(去参)+响应码，绝不记录令牌/正文
        line = (fmt % args).split("?")[0]
        sys.stdout.write(f"[AUDIT] {line}\n")


def run():
    try:
        httpd = http.server.HTTPServer((BIND_HOST, BIND_PORT), Handler)
    except OSError as e:
        # 端口冲突或绑定失败 → 安全失败，绝不回退到 0.0.0.0
        print(f"[FATAL] 端口冲突或绑定失败，安全退出: {e}")
        return
    if _TOKEN_PRINTED:
        print(f"[SECURITY] 启动令牌(仅本次, 勿记入日志): {AUTH_TOKEN}")
    print(f"[STATUS] 已绑定 http://{BIND_HOST}:{BIND_PORT} (明文回环; 残留风险见文件头)")
    httpd.serve_forever()


def run_selftest():
    import socket
    # 选一个空闲端口，避免与遗留监听进程冲突（Windows SO_REUSEADDR 下旧监听可能仍在）
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((BIND_HOST, 0))
    port = s.getsockname()[1]
    s.close()
    global BIND_PORT, ALLOWED_ORIGIN
    BIND_PORT = port
    ALLOWED_ORIGIN = f"http://{BIND_HOST}:{BIND_PORT}"

    httpd = http.server.HTTPServer((BIND_HOST, BIND_PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    from http.client import HTTPConnection

    def call(method, headers, expect):
        conn = HTTPConnection(BIND_HOST, BIND_PORT, timeout=3)
        h = {"Content-Type": "application/json"}
        h.update(headers)
        conn.request(method, "/", body=b"{}", headers=h)
        code = conn.getresponse().status
        conn.close()
        return code == expect, code, expect

    good = {"Authorization": f"Bearer {AUTH_TOKEN}", "Host": f"{BIND_HOST}:{BIND_PORT}"}
    cases = [
        ("无令牌", call("POST", {}, 401)),
        ("错误令牌", call("POST", {"Authorization": "Bearer WRONG", "Host": f"{BIND_HOST}:{BIND_PORT}"}, 401)),
        ("正确令牌+错误Host", call("POST", {"Authorization": f"Bearer {AUTH_TOKEN}", "Host": "evil.example.com:8123"}, 400)),
        ("正确令牌+跨源Origin", call("POST", {**good, "Origin": "http://evil.example.com"}, 403)),
        ("GET方法", call("GET", good, 405)),
        ("正确令牌+null Origin", call("POST", {**good, "Origin": "null"}, 200 if ALLOW_NULL_ORIGIN else 403)),
    ]
    print("\n=== 负向/正向自测 (ALLOW_NULL_ORIGIN=%s) ===" % ALLOW_NULL_ORIGIN)
    allok = True
    for name, res in cases:
        ok, code, exp = res
        allok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: 得到 {code} 期望 {exp}")
    httpd.shutdown()
    print("结果:", "ALL PASS" if allok else "HAS FAILURE")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        run()
