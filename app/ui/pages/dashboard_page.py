"""仪表盘页面 - 主页概览"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QPlainTextEdit
)
from PySide6.QtCore import Qt, Slot


class StatusCard(QFrame):
    """状态卡片"""

    def __init__(self, title: str, value: str = "--", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            StatusCard {
                background-color: #313244;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self._title = QLabel(title)
        self._title.setStyleSheet("color: #a6adc8; font-size: 12px;")

        self._value = QLabel(value)
        self._value.setStyleSheet("font-size: 24px; font-weight: bold; color: #cdd6f4;")

        layout.addWidget(self._title)
        layout.addWidget(self._value)

    def set_value(self, value: str):
        self._value.setText(value)

    def set_color(self, color: str):
        self._value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")


class DashboardPage(QWidget):
    """仪表盘主页"""

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("仪表盘")
        title.setObjectName("title")
        layout.addWidget(title)

        # 状态卡片
        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)

        self.card_status = StatusCard("核心状态", "已停止")
        self.card_status.set_color("#f38ba8")
        self.card_profile = StatusCard("当前配置", "未选择")
        self.card_mode = StatusCard("代理模式", "--")
        self.card_proxy = StatusCard("系统代理", "关闭")

        cards_layout.addWidget(self.card_status, 0, 0)
        cards_layout.addWidget(self.card_profile, 0, 1)
        cards_layout.addWidget(self.card_mode, 0, 2)
        cards_layout.addWidget(self.card_proxy, 0, 3)

        layout.addLayout(cards_layout)

        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_start = QPushButton("▶ 启动")
        self.btn_start.setObjectName("success")
        self.btn_start.setFixedHeight(40)
        self.btn_start.setMinimumWidth(120)

        self.btn_stop = QPushButton("■ 停止")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setMinimumWidth(120)
        self.btn_stop.setEnabled(False)

        self.btn_restart = QPushButton("↻ 重启")
        self.btn_restart.setFixedHeight(40)
        self.btn_restart.setMinimumWidth(120)
        self.btn_restart.setEnabled(False)

        self.btn_proxy = QPushButton("系统代理: 关")
        self.btn_proxy.setFixedHeight(40)
        self.btn_proxy.setMinimumWidth(140)
        self.btn_proxy.setCheckable(True)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_restart)
        btn_layout.addWidget(self.btn_proxy)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Inbound 信息
        info_layout = QHBoxLayout()
        self.inbound_info = QLabel("")
        self.inbound_info.setStyleSheet("color: #a6adc8; font-size: 12px;")
        info_layout.addWidget(self.inbound_info)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        self._update_inbound_info()

        # 日志
        log_label = QLabel("运行日志")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(log_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(1000)
        self.log_view.setStyleSheet("""
            QPlainTextEdit {
                font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
                font-size: 12px;
                background-color: #11111b;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.log_view, 1)

    def _connect_signals(self):
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_restart.clicked.connect(self._on_restart)
        self.btn_proxy.clicked.connect(self._on_toggle_proxy)

        core = self.ctx.core
        core.started.connect(self._on_core_started)
        core.stopped.connect(self._on_core_stopped)
        core.log_output.connect(self._on_log)
        core.error.connect(self._on_error)

    def _update_inbound_info(self):
        """显示当前 inbound 配置概览"""
        s = self.ctx.settings
        parts = []
        if s.get("enable_tun"):
            parts.append(f"TUN({s.get('tun_stack')})")
        if s.get("enable_mixed"):
            parts.append(f"Mixed:{s.get('mixed_port')}")
        if s.get("enable_http"):
            parts.append(f"HTTP:{s.get('http_port')}")
        if s.get("enable_socks"):
            parts.append(f"SOCKS:{s.get('socks_port')}")
        if not parts:
            parts.append(f"Mixed:{s.get('mixed_port')}(默认)")

        self.inbound_info.setText("入站: " + "  |  ".join(parts) +
                                  f"  |  API:{s.get('api_port')}")

    @Slot()
    def _on_start(self):
        config_path = self.ctx.config_manager.active_config_path
        if not config_path:
            self._on_log("⚠ 请先在「配置管理」中选择一个配置")
            return
        need_sudo = self.ctx.settings.get("enable_tun", False)
        self.ctx.core.start(config_path, need_sudo=need_sudo)

    @Slot()
    def _on_stop(self):
        self.ctx.core.stop()
        if self.btn_proxy.isChecked():
            self.btn_proxy.setChecked(False)
            self._on_toggle_proxy()

    @Slot()
    def _on_restart(self):
        self.ctx.core.restart()

    @Slot()
    def _on_toggle_proxy(self):
        from app.core.proxy_system import SystemProxy
        s = self.ctx.settings
        if self.btn_proxy.isChecked():
            port = s.get("system_proxy_port")
            SystemProxy.set_proxy(http_port=port, socks_port=port)
            self.btn_proxy.setText("系统代理: 开")
            self.btn_proxy.setObjectName("success")
            self.card_proxy.set_value("开启")
            self.card_proxy.set_color("#a6e3a1")
            self._on_log(f"✓ 系统代理已开启 (127.0.0.1:{port})")
        else:
            SystemProxy.clear_proxy()
            self.btn_proxy.setText("系统代理: 关")
            self.btn_proxy.setObjectName("")
            self.card_proxy.set_value("关闭")
            self.card_proxy.set_color("#cdd6f4")
            self._on_log("✗ 系统代理已关闭")
        self.btn_proxy.style().unpolish(self.btn_proxy)
        self.btn_proxy.style().polish(self.btn_proxy)

    @Slot()
    def _on_core_started(self):
        self.card_status.set_value("运行中")
        self.card_status.set_color("#a6e3a1")
        profile = self.ctx.config_manager.active_profile
        if profile:
            self.card_profile.set_value(profile.name)
        self.card_mode.set_value("规则模式")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_restart.setEnabled(True)
        self._update_inbound_info()

        if self.ctx.settings.get("auto_set_proxy"):
            self.btn_proxy.setChecked(True)
            self._on_toggle_proxy()

    @Slot()
    def _on_core_stopped(self):
        self.card_status.set_value("已停止")
        self.card_status.set_color("#f38ba8")
        self.card_mode.set_value("--")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_restart.setEnabled(False)

    @Slot(str)
    def _on_log(self, text: str):
        self.log_view.appendPlainText(text)

    @Slot(str)
    def _on_error(self, text: str):
        self.log_view.appendPlainText(f"❌ {text}")
