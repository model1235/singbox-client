#!/bin/bash
# SingBox Client 打包脚本
set -e

echo "=== SingBox Client 打包 ==="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q PySide6 requests pyinstaller

# 检查 sing-box 二进制
if [ ! -f "resources/sing-box" ] && [ ! -f "resources/sing-box.exe" ]; then
    echo ""
    echo "⚠ 注意: resources/ 目录下未找到 sing-box 二进制文件"
    echo "  请下载对应平台的 sing-box 并放入 resources/ 目录"
    echo "  下载地址: https://github.com/SagerNet/sing-box/releases"
    echo ""
    echo "  macOS:   放入 resources/sing-box"
    echo "  Windows: 放入 resources/sing-box.exe"
    echo ""
    read -p "是否继续打包（不包含 sing-box）？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 打包
echo "开始打包..."
pyinstaller singbox-client.spec --noconfirm

echo ""
echo "=== 打包完成 ==="
if [ "$(uname)" == "Darwin" ]; then
    echo "输出: dist/SingBox Client.app"
    echo "运行: open 'dist/SingBox Client.app'"
else
    echo "输出: dist/SingBox Client.exe"
fi
