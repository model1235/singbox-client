"""主窗口"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QSystemTrayIcon,
    QMenu, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QCloseEvent

from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.profiles_page import ProfilesPage
from app.ui.pages.proxies_page import ProxiesPage
from app.ui.pages.connections_page import ConnectionsPage
from app.ui.pages.logs_page import LogsPage
from app.ui.pages.settings_page import SettingsPage


class SidebarButton(QPushButton):
    """侧边栏导航按钮"""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self, app_context):
        super().__init__()
        self.ctx = app_context
        self.setWindowTitle("SingBox Client")
        self.setMinimumSize(960, 640)
        self.resize(1100, 700)

        self._setup_ui()
        self._setup_tray()
        self._connect_signals()

        # 默认选中仪表盘
        self._nav_buttons[0].setChecked(True)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- 侧边栏 ----
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo 区
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 16, 16, 8)
        logo_label = QLabel("SingBox")
        logo_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        logo_sub = QLabel("Client")
        logo_sub.setStyleSheet("font-size: 12px; color: #a6adc8;")
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(logo_sub)
        sidebar_layout.addWidget(logo_widget)

        # 导航按钮
        nav_items = [
            ("⌂  仪表盘", 0),
            ("☰  配置管理", 1),
            ("◈  节点流量", 2),
            ("⇌  连接列表", 3),
            ("▤  日志", 4),
            ("⚙  设置", 5),
        ]

        self._nav_buttons: list[SidebarButton] = []
        for text, index in nav_items:
            btn = SidebarButton(text)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # 底部状态
        self._status_label = QLabel("● 已停止")
        self._status_label.setObjectName("status-off")
        self._status_label.setStyleSheet("padding: 12px 20px; font-size: 12px; color: #f38ba8;")
        sidebar_layout.addWidget(self._status_label)

        main_layout.addWidget(sidebar)

        # ---- 内容区 ----
        self._stack = QStackedWidget()
        self._stack.addWidget(DashboardPage(self.ctx))
        self._stack.addWidget(ProfilesPage(self.ctx))
        self._stack.addWidget(ProxiesPage(self.ctx))
        self._stack.addWidget(ConnectionsPage(self.ctx))
        self._stack.addWidget(LogsPage(self.ctx))
        self._stack.addWidget(SettingsPage(self.ctx))

        main_layout.addWidget(self._stack, 1)

    def _setup_tray(self):
        """设置系统托盘"""
        self._tray = QSystemTrayIcon(self)
        # 使用默认图标，后续可替换为自定义图标
        self._tray.setToolTip("SingBox Client")

        menu = QMenu()
        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self._show_window)
        menu.addAction(action_show)

        menu.addSeparator()

        self._tray_status = QAction("状态: 已停止", self)
        self._tray_status.setEnabled(False)
        menu.addAction(self._tray_status)

        menu.addSeparator()

        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self._quit_app)
        menu.addAction(action_quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _connect_signals(self):
        self.ctx.core.started.connect(self._on_core_started)
        self.ctx.core.stopped.connect(self._on_core_stopped)

    def _switch_page(self, index: int):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def _on_core_started(self):
        self._status_label.setText("● 运行中")
        self._status_label.setStyleSheet("padding: 12px 20px; font-size: 12px; color: #a6e3a1;")
        self._tray_status.setText("状态: 运行中")
        self._tray.setToolTip("SingBox Client - 运行中")

    def _on_core_stopped(self):
        self._status_label.setText("● 已停止")
        self._status_label.setStyleSheet("padding: 12px 20px; font-size: 12px; color: #f38ba8;")
        self._tray_status.setText("状态: 已停止")
        self._tray.setToolTip("SingBox Client - 已停止")

    def _show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def closeEvent(self, event: QCloseEvent):
        """关闭窗口时最小化到托盘"""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "SingBox Client",
            "已最小化到系统托盘",
            QSystemTrayIcon.Information,
            1000
        )

    def _quit_app(self):
        """真正退出"""
        # 停止核心
        if self.ctx.core.is_running:
            self.ctx.core.stop()
            # 清除系统代理
            from app.core.proxy_system import SystemProxy
            SystemProxy.clear_proxy()

        self._tray.hide()
        QApplication.quit()
