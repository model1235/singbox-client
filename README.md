# SingBox Client

跨平台的 [sing-box](https://github.com/SagerNet/sing-box) 图形客户端，基于 Python + PySide6 (Qt6) 构建。

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-GPL--3.0-green)
![Platform](https://img.shields.io/badge/Platform-macOS%20|%20Windows-lightgrey)

## 功能

- **配置管理** — 本地配置导入、远程订阅添加/更新
- **配置合并** — 订阅（outbounds/dns/route）+ 客户端生成（inbounds/log）自动合并
- **入站设置** — 支持 TUN / Mixed / HTTP / SOCKS 入站，可视化配置端口和选项
- **节点与流量** — 按 outbound 统计流量，节点延迟测试，分组管理
- **连接列表** — 实时显示活跃连接，支持一键关闭
- **系统代理** — 启动核心时自动设置系统代理（macOS networksetup / Windows registry）
- **TUN 模式** — 自动权限提升，全局代理
- **系统托盘** — 最小化到托盘，后台运行
- **暗色主题** — Catppuccin Mocha 风格 UI

## 截图

<!-- TODO: 添加截图 -->

## 安装

### 下载

从 [Releases](../../releases) 页面下载：

- **macOS (Apple Silicon)**: `SingBox-Client-macos-arm64.dmg`
- **Windows (x64)**: `SingBox-Client-windows-x64.zip`

### 准备 sing-box 核心

客户端不内置 sing-box，需要自行下载：https://github.com/SagerNet/sing-box/releases

安装后在客户端「设置」中指定 sing-box 路径。

### macOS 安装

1. 打开 DMG，将 SingBox Client 拖到 Applications
2. 首次打开前在终端执行（macOS Sequoia 15+ 必须）：
   ```bash
   xattr -cr /Applications/SingBox\ Client.app
   ```
3. 双击打开，在设置中指定 sing-box 路径

### Windows 安装

1. 解压 zip
2. 运行 `SingBox Client.exe`，在设置中指定 sing-box 路径

## 从源码运行

```bash
# 克隆
git clone https://github.com/model1235/singbox-client.git
cd singbox-client

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

需要在设置中指定 sing-box 二进制路径，或将其加入系统 PATH。

## 构建

```bash
# 安装打包工具
pip install pyinstaller

# 打包
pyinstaller singbox-client.spec --noconfirm

# 产物
# macOS: dist/SingBox Client.app
# Windows: dist/SingBox Client.exe
```

## 技术栈

- **UI**: PySide6 (Qt6)
- **核心**: sing-box
- **打包**: PyInstaller
- **CI/CD**: GitHub Actions

## License

[GPL-3.0](LICENSE)
