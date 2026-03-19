#!/bin/bash
# GOST 管理面板安装脚本

set -e
Green_font_prefix="\033[32m"
Red_font_prefix="\033[31m"
Font_color_suffix="\033[0m"
Info="${Green_font_prefix}[信息]${Font_color_suffix}"
Error="${Red_font_prefix}[错误]${Font_color_suffix}"

[[ $EUID -ne 0 ]] && echo -e "${Error} 请使用 root 运行此脚本" && exit 1

PANEL_DIR="/opt/gost-panel"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${Info} 安装 GOST 管理面板..."

# 检查 Python3 和 venv
if ! command -v python3 &>/dev/null; then
    echo -e "${Info} 正在安装 python3..."
    if [[ -f /etc/redhat-release ]]; then
        yum install -y python3
    else
        apt-get update && apt-get install -y python3 python3-venv
    fi
elif ! python3 -c "import venv" 2>/dev/null; then
    echo -e "${Info} 正在安装 python3-venv..."
    if [[ -f /etc/redhat-release ]]; then
        yum install -y python3-virtualenv 2>/dev/null || true
    else
        apt-get update && apt-get install -y python3-venv
    fi
fi

# 创建目录并复制文件
mkdir -p "$PANEL_DIR"
cp -r "$SCRIPT_DIR"/* "$PANEL_DIR/"
cd "$PANEL_DIR"

# 使用虚拟环境安装依赖（兼容 Debian/Ubuntu 的 PEP 668 限制）
echo -e "${Info} 创建虚拟环境并安装依赖..."
if ! python3 -m venv "$PANEL_DIR/venv" 2>/dev/null; then
    echo -e "${Info} 正在安装 python3-venv..."
    if [[ -f /etc/redhat-release ]]; then
        yum install -y python3-virtualenv || true
    else
        apt-get update && apt-get install -y python3-venv
    fi
    python3 -m venv "$PANEL_DIR/venv"
fi
"$PANEL_DIR/venv/bin/pip" install -r requirements.txt -q

# 安装 systemd 服务
cp gost-panel.service /usr/lib/systemd/system/
systemctl daemon-reload
systemctl enable gost-panel
systemctl start gost-panel

SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo -e "${Info} 面板安装完成！"
echo -e "  访问地址: http://${SERVER_IP:-服务器IP}:5000"
echo -e "  默认账号: admin / admin"
echo -e "  修改账号: 编辑 /usr/lib/systemd/system/gost-panel.service 中的 Environment"
echo -e "  重启面板: systemctl restart gost-panel"
