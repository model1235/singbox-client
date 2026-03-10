"""SingBox Client 入口"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.core.singbox import SingBoxCore
from app.core.config_manager import ConfigManager
from app.core.settings import Settings
from app.ui.styles import DARK_STYLE
from app.ui.main_window import MainWindow


class AppContext:
    """应用上下文，持有核心组件的引用"""

    def __init__(self):
        self.core = SingBoxCore()
        self.settings = Settings(self.core.data_dir)
        self.config_manager = ConfigManager(self.core.data_dir, self.settings)

        # 应用 settings 中的 sing-box 路径
        custom_bin = self.settings.get("singbox_binary")
        if custom_bin:
            self.core.set_binary_path(custom_bin)


def main():
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SingBox Client")
    app.setOrganizationName("SingBoxClient")

    # 应用暗色主题
    app.setStyleSheet(DARK_STYLE)

    # 防止关闭最后一个窗口时退出（使用系统托盘）
    app.setQuitOnLastWindowClosed(False)

    # 初始化上下文
    ctx = AppContext()

    # 创建主窗口
    window = MainWindow(ctx)

    # 根据设置决定是否最小化启动
    if ctx.settings.get("start_minimized"):
        pass  # 不显示窗口，只在托盘
    else:
        window.show()

    # 自动启动核心
    if ctx.settings.get("auto_start_core"):
        config_path = ctx.config_manager.active_config_path
        if config_path:
            ctx.core.start(config_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
