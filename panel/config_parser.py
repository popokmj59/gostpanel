# -*- coding: utf-8 -*-
"""
GOST 配置解析与生成模块
与 gost.sh 的 rawconf 格式完全兼容
"""

import json
import os
from typing import List, Dict, Optional, Any

# 路径配置
GOST_CONF_PATH = "/etc/gost/config.json"
RAW_CONF_PATH = "/etc/gost/rawconf"
GOST_CERT_DIR = os.path.expanduser("~/gost_cert")

# 协议类型与中文标签映射
TYPE_LABELS = {
    "nonencrypt": "不加密转发",
    "encrypttls": "TLS隧道",
    "encryptws": "WS隧道",
    "encryptwss": "WSS隧道",
    "decrypttls": "TLS解密",
    "decryptws": "WS解密",
    "decryptwss": "WSS解密",
    "peerno": "不加密均衡负载",
    "peertls": "TLS均衡负载",
    "peerws": "WS均衡负载",
    "peerwss": "WSS均衡负载",
    "cdnno": "不加密CDN",
    "cdnws": "WS隧道CDN",
    "cdnwss": "WSS隧道CDN",
    "ss": "Shadowsocks",
    "socks": "SOCKS5",
    "http": "HTTP代理",
}


def parse_rawconf_line(line: str) -> Optional[Dict[str, str]]:
    """
    解析单行 rawconf
    格式: protocol/source_port#dest_ip#dest_port
    对于 ss/socks/http: protocol/password#username_or_encryption#port
    对于 cdn: protocol/port#ip:port#host
    对于 peer: protocol/port#filename#strategy
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split("#", 2)
    if len(parts) < 3:
        return None

    flag_s_port = parts[0]  # protocol/source
    d_ip = parts[1]
    d_port = parts[2]

    if "/" not in flag_s_port:
        return None

    is_encrypt, s_port = flag_s_port.split("/", 1)
    return {
        "type": is_encrypt,
        "sourcePort": s_port,
        "destAddr": d_ip,
        "destPort": d_port,
    }


def load_rules() -> List[Dict[str, Any]]:
    """从 rawconf 加载所有规则"""
    rules = []
    if not os.path.exists(RAW_CONF_PATH):
        return rules

    with open(RAW_CONF_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            parsed = parse_rawconf_line(line)
            if parsed:
                parsed["id"] = i
                parsed["typeLabel"] = TYPE_LABELS.get(
                    parsed["type"], parsed["type"]
                )
                rules.append(parsed)
    return rules


def _has_custom_cert() -> bool:
    """检查是否有自定义 TLS 证书"""
    cert_path = os.path.join(GOST_CERT_DIR, "cert.pem")
    key_path = os.path.join(GOST_CERT_DIR, "key.pem")
    return os.path.exists(cert_path) and os.path.exists(key_path)


def _get_serve_nodes(
    rule: Dict[str, str], is_first: bool, use_cert: bool
) -> List[Any]:
    """
    根据规则类型生成 ServeNodes 配置
    返回 list 或 dict (含 ChainNodes)
    """
    rtype = rule["type"]
    s_port = rule["sourcePort"]
    d_ip = rule["destAddr"]
    d_port = rule["destPort"]

    cert_suffix = "?secure=true" if use_cert and rtype in ("encrypttls", "encryptwss") else ""
    if d_port.endswith("?secure=true"):
        d_port_clean = d_port
    else:
        d_port_clean = d_port + cert_suffix if cert_suffix else d_port

    cert_path = f"{GOST_CERT_DIR}/cert.pem"
    key_path = f"{GOST_CERT_DIR}/key.pem"

    nodes = []

    if rtype == "nonencrypt":
        nodes = [
            f"tcp://:{s_port}/{d_ip}:{d_port}",
            f"udp://:{s_port}/{d_ip}:{d_port}",
        ]
    elif rtype == "cdnno":
        nodes = [
            f"tcp://:{s_port}/{d_ip}?host={d_port}",
            f"udp://:{s_port}/{d_ip}?host={d_port}",
        ]
    elif rtype == "peerno":
        ip_file = f"/root/{d_ip}.txt" if not d_ip.endswith(".txt") else f"/root/{d_ip}"
        nodes = [
            f"tcp://:{s_port}?ip={ip_file}&strategy={d_port}",
            f"udp://:{s_port}?ip={ip_file}&strategy={d_port}",
        ]
    elif rtype == "encrypttls":
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+tls://{d_ip}:{d_port_clean}"],
        }
    elif rtype == "encryptws":
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+ws://{d_ip}:{d_port}"],
        }
    elif rtype == "encryptwss":
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+wss://{d_ip}:{d_port_clean}"],
        }
    elif rtype == "peertls":
        ip_file = f"/root/{d_ip}.txt" if not d_ip.endswith(".txt") else f"/root/{d_ip}"
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+tls://:?ip={ip_file}&strategy={d_port}"],
        }
    elif rtype == "peerws":
        ip_file = f"/root/{d_ip}.txt" if not d_ip.endswith(".txt") else f"/root/{d_ip}"
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+ws://:?ip={ip_file}&strategy={d_port}"],
        }
    elif rtype == "peerwss":
        ip_file = f"/root/{d_ip}.txt" if not d_ip.endswith(".txt") else f"/root/{d_ip}"
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+wss://:?ip={ip_file}&strategy={d_port}"],
        }
    elif rtype == "cdnws":
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+ws://{d_ip}?host={d_port}"],
        }
    elif rtype == "cdnwss":
        return {
            "ServeNodes": [
                f"tcp://:{s_port}",
                f"udp://:{s_port}",
            ],
            "ChainNodes": [f"relay+wss://{d_ip}?host={d_port}"],
        }
    elif rtype == "decrypttls":
        if use_cert:
            nodes = [
                f"relay+tls://:{s_port}/{d_ip}:{d_port}?cert={cert_path}&key={key_path}"
            ]
        else:
            nodes = [f"relay+tls://:{s_port}/{d_ip}:{d_port}"]
    elif rtype == "decryptws":
        nodes = [f"relay+ws://:{s_port}/{d_ip}:{d_port}"]
    elif rtype == "decryptwss":
        if use_cert:
            nodes = [
                f"relay+wss://:{s_port}/{d_ip}:{d_port}?cert={cert_path}&key={key_path}"
            ]
        else:
            nodes = [f"relay+wss://:{s_port}/{d_ip}:{d_port}"]
    elif rtype == "ss":
        # ss: password 在 sourcePort, encryption 在 destAddr, port 在 destPort
        nodes = [f"ss://{d_ip}:{s_port}@:{d_port}"]
    elif rtype == "socks":
        nodes = [f"socks5://{d_ip}:{s_port}@:{d_port}"]
    elif rtype == "http":
        nodes = [f"http://{d_ip}:{s_port}@:{d_port}"]
    else:
        nodes = []

    return {"ServeNodes": nodes} if isinstance(nodes, list) else nodes


def rules_to_rawconf(rules: List[Dict[str, Any]]) -> str:
    """将规则列表转换为 rawconf 格式"""
    lines = []
    for r in rules:
        line = f"{r['type']}/{r['sourcePort']}#{r['destAddr']}#{r['destPort']}"
        lines.append(line)
    return "\n".join(lines)


def generate_config_json(rules: List[Dict[str, Any]]) -> dict:
    """根据规则列表生成 GOST config.json"""
    use_cert = _has_custom_cert()

    if not rules:
        return {
            "Debug": False,
            "Retries": 0,
            "ServeNodes": ["udp://127.0.0.1:65532"],
        }

    base = {
        "Debug": False,
        "Retries": 0,
    }

    first_rule = rules[0]
    first_nodes = _get_serve_nodes(first_rule, True, use_cert)

    if isinstance(first_nodes, dict) and "ChainNodes" in first_nodes:
        base["ServeNodes"] = first_nodes["ServeNodes"]
        base["ChainNodes"] = first_nodes["ChainNodes"]
    else:
        base["ServeNodes"] = first_nodes.get("ServeNodes", first_nodes)

    if len(rules) == 1:
        return base

    routes = []
    for rule in rules[1:]:
        nodes = _get_serve_nodes(rule, False, use_cert)
        route = {"Retries": 0}
        if isinstance(nodes, dict) and "ChainNodes" in nodes:
            route["ServeNodes"] = nodes["ServeNodes"]
            route["ChainNodes"] = nodes["ChainNodes"]
        else:
            route["ServeNodes"] = nodes.get("ServeNodes", nodes)
        routes.append(route)

    base["Routes"] = routes
    return base


def save_config(rules: List[Dict[str, Any]]) -> None:
    """保存配置到 rawconf 和 config.json"""
    os.makedirs(os.path.dirname(RAW_CONF_PATH), exist_ok=True)
    with open(RAW_CONF_PATH, "w", encoding="utf-8") as f:
        f.write(rules_to_rawconf(rules))

    config = generate_config_json(rules)
    with open(GOST_CONF_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def add_rule(rule: Dict[str, str]) -> List[Dict[str, Any]]:
    """添加新规则"""
    rules = load_rules()
    new_rule = {
        "type": rule["type"],
        "sourcePort": str(rule["sourcePort"]),
        "destAddr": str(rule["destAddr"]),
        "destPort": str(rule["destPort"]),
    }
    rules.append(new_rule)
    save_config(rules)
    return load_rules()


def update_rule(rule_id: int, rule: Dict[str, str]) -> List[Dict[str, Any]]:
    """更新指定规则"""
    rules = load_rules()
    idx = rule_id - 1
    if idx < 0 or idx >= len(rules):
        raise ValueError("规则不存在")
    rules[idx] = {
        "type": rule["type"],
        "sourcePort": str(rule["sourcePort"]),
        "destAddr": str(rule["destAddr"]),
        "destPort": str(rule["destPort"]),
    }
    save_config(rules)
    return load_rules()


def delete_rule(rule_id: int) -> List[Dict[str, Any]]:
    """删除指定规则"""
    rules = load_rules()
    idx = rule_id - 1
    if idx < 0 or idx >= len(rules):
        raise ValueError("规则不存在")
    rules.pop(idx)
    save_config(rules)
    return load_rules()
