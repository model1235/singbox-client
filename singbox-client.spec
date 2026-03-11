# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置

使用方法:
  pyinstaller singbox-client.spec

打包前准备:
  1. 将对应平台的 sing-box 二进制放到 resources/ 目录:
     - macOS:   resources/sing-box
     - Windows: resources/sing-box.exe
  2. (可选) 将应用图标放到 resources/ 目录:
     - macOS:   resources/icon.icns
     - Windows: resources/icon.ico
"""
import platform
import os

system = platform.system()
block_cipher = None

# sing-box 二进制和资源文件
datas = []
binaries = []

resources_dir = os.path.join(os.getcwd(), 'resources')
if system == 'Windows':
    singbox_bin = os.path.join(resources_dir, 'sing-box.exe')
else:
    singbox_bin = os.path.join(resources_dir, 'sing-box')

if os.path.exists(singbox_bin):
    binaries.append((singbox_bin, 'resources'))

# 图标
icon_file = None
if system == 'Darwin':
    icon_path = os.path.join(resources_dir, 'icon.icns')
    if os.path.exists(icon_path):
        icon_file = icon_path
elif system == 'Windows':
    icon_path = os.path.join(resources_dir, 'icon.ico')
    if os.path.exists(icon_path):
        icon_file = icon_path

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest',
        'pydoc', 'doctest',
        'PySide6.QtQuick', 'PySide6.QtQml',
        'PySide6.Qt3DCore', 'PySide6.QtBluetooth',
        'PySide6.QtMultimedia', 'PySide6.QtWebEngine',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if system == 'Darwin':
    # macOS: 打包为 .app
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='SingBox Client',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=icon_file,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        name='SingBox Client',
    )
    app = BUNDLE(
        coll,
        name='SingBox Client.app',
        icon=icon_file,
        bundle_identifier='com.singbox.client',
        info_plist={
            'CFBundleDisplayName': 'SingBox Client',
            'CFBundleShortVersionString': '1.0.0',
            'LSMinimumSystemVersion': '10.15',
            'LSBackgroundOnly': False,
            'NSHighResolutionCapable': True,
            'LSUIElement': False,
        },
    )
else:
    # Windows: 打包为 .exe
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='SingBox Client',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon=icon_file,
    )
