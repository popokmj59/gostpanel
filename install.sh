#!/bin/bash
# GOST Panel 一键安装脚本
# 项目地址: https://github.com/popokmj59/gostpanel

set -e
REPO="popokmj59/gostpanel"
BRANCH="main"
Green_font_prefix="\033[32m"
Red_font_prefix="\033[31m"
Font_color_suffix="\033[0m"
Info="${Green_font_prefix}[信息]${Font_color_suffix}"
Error="${Red_font_prefix}[错误]${Font_color_suffix}"

[[ $EUID -ne 0 ]] && echo -e "${Error} 请使用 root 运行此脚本" && exit 1

INSTALL_DIR="/root/gostpanel"
cd /tmp
rm -rf gostpanel-install
mkdir -p gostpanel-install
cd gostpanel-install

echo -e "${Info} 正在下载完整项目..."

# 方式1: 使用 git clone（最快，推荐）
if command -v git &>/dev/null; then
    git clone --depth 1 https://github.com/${REPO}.git .
    echo -e "${Info} 下载完成 (git)"
else
    # 方式2: 下载 zip 包
    if [[ -f /etc/redhat-release ]]; then
        yum install -y unzip 2>/dev/null || true
    else
        apt-get update -qq 2>/dev/null && apt-get install -y unzip 2>/dev/null || true
    fi
    if command -v unzip &>/dev/null; then
        wget -q --no-check-certificate "https://github.com/${REPO}/archive/refs/heads/${BRANCH}.zip" -O repo.zip 2>/dev/null || \
        curl -sSL "https://github.com/${REPO}/archive/refs/heads/${BRANCH}.zip" -o repo.zip 2>/dev/null || \
        wget -q --no-check-certificate "https://github.com/${REPO}/archive/refs/heads/master.zip" -O repo.zip
        unzip -q repo.zip
        EXTRACT_DIR=$(ls -d gostpanel-* 2>/dev/null | head -1)
        cp -r "$EXTRACT_DIR"/* .
        rm -rf "$EXTRACT_DIR" repo.zip
        echo -e "${Info} 下载完成 (zip)"
    else
        echo -e "${Error} 需要 git 或 unzip，请先安装: apt install git 或 apt install unzip"
        exit 1
    fi
fi

# 复制到安装目录并运行
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"
cd "$INSTALL_DIR"
chmod +x gost.sh
echo -e "${Info} 项目已下载到 $INSTALL_DIR"
echo -e "${Info} 启动安装脚本..."
./gost.sh
