# -*- coding: utf-8 -*-
"""
GOST 可视化管理面板 - Flask 后端
"""

import os
import subprocess
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from config_parser import load_rules, add_rule, update_rule, delete_rule

app = Flask(__name__, static_folder="static", template_folder="templates")

# 简单认证：从环境变量读取，默认 admin/admin
PANEL_USER = os.environ.get("GOST_PANEL_USER", "admin")
PANEL_PASS = os.environ.get("GOST_PANEL_PASS", "admin")
PANEL_SECRET = os.environ.get("GOST_PANEL_SECRET", "")  # 可选：Bearer Token


def check_auth(auth):
    """验证 Basic Auth 或 Bearer Token"""
    if PANEL_SECRET and auth and auth.startswith("Bearer "):
        return auth[7:] == PANEL_SECRET
    if auth and " " in auth:
        method, creds = auth.split(" ", 1)
        if method.lower() == "basic":
            import base64
            try:
                decoded = base64.b64decode(creds).decode("utf-8")
                user, passwd = decoded.split(":", 1)
                return user == PANEL_USER and passwd == PANEL_PASS
            except Exception:
                return False
    return False


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not check_auth(auth):
            return jsonify({"error": "未授权"}), 401
        return f(*args, **kwargs)
    return decorated


# 协议类型选项（供前端使用）
PROTOCOL_OPTIONS = [
    {"value": "nonencrypt", "label": "不加密转发", "category": "forward"},
    {"value": "encrypttls", "label": "TLS隧道(中转)", "category": "encrypt"},
    {"value": "encryptws", "label": "WS隧道(中转)", "category": "encrypt"},
    {"value": "encryptwss", "label": "WSS隧道(中转)", "category": "encrypt"},
    {"value": "decrypttls", "label": "TLS解密(落地)", "category": "decrypt"},
    {"value": "decryptws", "label": "WS解密(落地)", "category": "decrypt"},
    {"value": "decryptwss", "label": "WSS解密(落地)", "category": "decrypt"},
    {"value": "peerno", "label": "不加密均衡负载", "category": "peer"},
    {"value": "peertls", "label": "TLS均衡负载", "category": "peer"},
    {"value": "peerws", "label": "WS均衡负载", "category": "peer"},
    {"value": "peerwss", "label": "WSS均衡负载", "category": "peer"},
    {"value": "cdnno", "label": "不加密CDN", "category": "cdn"},
    {"value": "cdnws", "label": "WS隧道CDN", "category": "cdn"},
    {"value": "cdnwss", "label": "WSS隧道CDN", "category": "cdn"},
    {"value": "ss", "label": "Shadowsocks", "category": "proxy"},
    {"value": "socks", "label": "SOCKS5", "category": "proxy"},
    {"value": "http", "label": "HTTP代理", "category": "proxy"},
]


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/api/protocols", methods=["GET"])
@require_auth
def get_protocols():
    return jsonify({"protocols": PROTOCOL_OPTIONS})


@app.route("/api/rules", methods=["GET"])
@require_auth
def get_rules():
    try:
        rules = load_rules()
        return jsonify({"rules": rules})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rules", methods=["POST"])
@require_auth
def create_rule():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        required = ["type", "sourcePort", "destAddr", "destPort"]
        for k in required:
            if k not in data:
                return jsonify({"error": f"缺少字段: {k}"}), 400
        rules = add_rule(data)
        return jsonify({"rules": rules, "message": "添加成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rules/<int:rule_id>", methods=["PUT"])
@require_auth
def modify_rule(rule_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        required = ["type", "sourcePort", "destAddr", "destPort"]
        for k in required:
            if k not in data:
                return jsonify({"error": f"缺少字段: {k}"}), 400
        rules = update_rule(rule_id, data)
        return jsonify({"rules": rules, "message": "修改成功"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rules/<int:rule_id>", methods=["DELETE"])
@require_auth
def remove_rule(rule_id):
    try:
        rules = delete_rule(rule_id)
        return jsonify({"rules": rules, "message": "删除成功"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/restart", methods=["POST"])
@require_auth
def restart_gost():
    try:
        result = subprocess.run(
            ["systemctl", "restart", "gost"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return jsonify({
                "error": f"重启失败: {result.stderr or result.stdout}"
            }), 500
        return jsonify({"message": "重启成功"})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "重启超时"}), 500
    except FileNotFoundError:
        return jsonify({"error": "systemctl 不可用，请确保在 Linux 环境下运行"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
@require_auth
def get_status():
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "gost"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = "active" if result.returncode == 0 else "inactive"
        return jsonify({"status": status})
    except Exception:
        return jsonify({"status": "unknown"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
