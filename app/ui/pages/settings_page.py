"""设置页面"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QGroupBox, QFormLayout, QFileDialog,
    QSpinBox, QComboBox, QMessageBox, QScrollArea
)
from PySide6.QtCore import Slot


class SettingsPage(QWidget):
    """应用设置"""

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("设置")
        title.setObjectName("title")
        layout.addWidget(title)

        # ---- sing-box 核心 ----
        core_group = QGroupBox("核心设置")
        core_form = QFormLayout(core_group)

        self.singbox_path = QLineEdit()
        self.singbox_path.setPlaceholderText("留空则自动查找")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.singbox_path)
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self._browse_binary)
        path_layout.addWidget(btn_browse)
        core_form.addRow("sing-box 路径:", path_layout)

        self.log_level = QComboBox()
        self.log_level.addItems(["trace", "debug", "info", "warn", "error", "fatal", "panic"])
        core_form.addRow("日志级别:", self.log_level)

        layout.addWidget(core_group)

        # ---- Inbound 设置 ----
        inbound_group = QGroupBox("入站设置 (Inbounds)")
        inbound_form = QFormLayout(inbound_group)

        self.listen_address = QLineEdit()
        self.listen_address.setPlaceholderText("127.0.0.1")
        inbound_form.addRow("监听地址:", self.listen_address)

        self.sniff_override = QCheckBox("覆盖目标地址 (sniff_override_destination)")
        inbound_form.addRow(self.sniff_override)

        # TUN
        inbound_form.addRow(QLabel(""))  # spacer
        tun_header = QLabel("TUN 模式")
        tun_header.setStyleSheet("font-weight: bold; color: #89b4fa;")
        inbound_form.addRow(tun_header)

        self.enable_tun = QCheckBox("启用 TUN")
        inbound_form.addRow(self.enable_tun)

        self.tun_stack = QComboBox()
        self.tun_stack.addItems(["mixed", "system", "gvisor"])
        inbound_form.addRow("TUN 栈:", self.tun_stack)

        self.tun_strict_route = QCheckBox("严格路由 (strict_route)")
        inbound_form.addRow(self.tun_strict_route)

        # Mixed
        inbound_form.addRow(QLabel(""))
        mixed_header = QLabel("Mixed 代理 (HTTP + SOCKS5)")
        mixed_header.setStyleSheet("font-weight: bold; color: #89b4fa;")
        inbound_form.addRow(mixed_header)

        self.enable_mixed = QCheckBox("启用 Mixed")
        inbound_form.addRow(self.enable_mixed)

        self.mixed_port = QSpinBox()
        self.mixed_port.setRange(1024, 65535)
        inbound_form.addRow("Mixed 端口:", self.mixed_port)

        # HTTP
        inbound_form.addRow(QLabel(""))
        http_header = QLabel("HTTP 代理")
        http_header.setStyleSheet("font-weight: bold; color: #89b4fa;")
        inbound_form.addRow(http_header)

        self.enable_http = QCheckBox("启用 HTTP")
        inbound_form.addRow(self.enable_http)

        self.http_port = QSpinBox()
        self.http_port.setRange(1024, 65535)
        inbound_form.addRow("HTTP 端口:", self.http_port)

        # SOCKS
        inbound_form.addRow(QLabel(""))
        socks_header = QLabel("SOCKS5 代理")
        socks_header.setStyleSheet("font-weight: bold; color: #89b4fa;")
        inbound_form.addRow(socks_header)

        self.enable_socks = QCheckBox("启用 SOCKS5")
        inbound_form.addRow(self.enable_socks)

        self.socks_port = QSpinBox()
        self.socks_port.setRange(1024, 65535)
        inbound_form.addRow("SOCKS5 端口:", self.socks_port)

        layout.addWidget(inbound_group)

        # ---- Clash API ----
        api_group = QGroupBox("Clash API")
        api_form = QFormLayout(api_group)

        self.api_port = QSpinBox()
        self.api_port.setRange(1024, 65535)
        api_form.addRow("API 端口:", self.api_port)

        layout.addWidget(api_group)

        # ---- 系统代理 ----
        proxy_group = QGroupBox("系统代理")
        proxy_form = QFormLayout(proxy_group)

        self.auto_set_proxy = QCheckBox("启动核心时自动设置系统代理")
        proxy_form.addRow(self.auto_set_proxy)

        self.system_proxy_port = QSpinBox()
        self.system_proxy_port.setRange(1024, 65535)
        proxy_form.addRow("系统代理端口:", self.system_proxy_port)
        proxy_form.addRow(QLabel("(通常与 Mixed 端口相同)"))

        layout.addWidget(proxy_group)

        # ---- 通用 ----
        general_group = QGroupBox("通用")
        general_form = QFormLayout(general_group)

        self.auto_start_core = QCheckBox("启动应用时自动启动核心")
        general_form.addRow(self.auto_start_core)

        self.start_minimized = QCheckBox("启动时最小化到托盘")
        general_form.addRow(self.start_minimized)

        self.auto_launch = QCheckBox("开机自动启动")
        general_form.addRow(self.auto_launch)

        layout.addWidget(general_group)

        # 保存按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("保存设置")
        self.btn_save.setObjectName("primary")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setMinimumWidth(120)
        self.btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_settings(self):
        s = self.ctx.settings
        self.singbox_path.setText(s.get("singbox_binary", ""))
        self.log_level.setCurrentText(s.get("log_level"))
        self.listen_address.setText(s.get("listen_address"))
        self.sniff_override.setChecked(s.get("sniff_override"))

        self.enable_tun.setChecked(s.get("enable_tun"))
        self.tun_stack.setCurrentText(s.get("tun_stack"))
        self.tun_strict_route.setChecked(s.get("tun_strict_route"))

        self.enable_mixed.setChecked(s.get("enable_mixed"))
        self.mixed_port.setValue(s.get("mixed_port"))

        self.enable_http.setChecked(s.get("enable_http"))
        self.http_port.setValue(s.get("http_port"))

        self.enable_socks.setChecked(s.get("enable_socks"))
        self.socks_port.setValue(s.get("socks_port"))

        self.api_port.setValue(s.get("api_port"))
        self.auto_set_proxy.setChecked(s.get("auto_set_proxy"))
        self.system_proxy_port.setValue(s.get("system_proxy_port"))

        self.auto_start_core.setChecked(s.get("auto_start_core"))
        self.start_minimized.setChecked(s.get("start_minimized"))
        self.auto_launch.setChecked(s.get("auto_launch"))

    @Slot()
    def _save_settings(self):
        s = self.ctx.settings
        s.set("singbox_binary", self.singbox_path.text().strip())
        s.set("log_level", self.log_level.currentText())
        s.set("listen_address", self.listen_address.text().strip() or "127.0.0.1")
        s.set("sniff_override", self.sniff_override.isChecked())

        s.set("enable_tun", self.enable_tun.isChecked())
        s.set("tun_stack", self.tun_stack.currentText())
        s.set("tun_strict_route", self.tun_strict_route.isChecked())

        s.set("enable_mixed", self.enable_mixed.isChecked())
        s.set("mixed_port", self.mixed_port.value())

        s.set("enable_http", self.enable_http.isChecked())
        s.set("http_port", self.http_port.value())

        s.set("enable_socks", self.enable_socks.isChecked())
        s.set("socks_port", self.socks_port.value())

        s.set("api_port", self.api_port.value())
        s.set("auto_set_proxy", self.auto_set_proxy.isChecked())
        s.set("system_proxy_port", self.system_proxy_port.value())

        s.set("auto_start_core", self.auto_start_core.isChecked())
        s.set("start_minimized", self.start_minimized.isChecked())
        s.set("auto_launch", self.auto_launch.isChecked())

        # 更新 sing-box 路径
        if self.singbox_path.text().strip():
            self.ctx.core.set_binary_path(self.singbox_path.text().strip())

        # 重新合并所有配置（inbound 设置可能变了）
        self.ctx.config_manager.rebuild_all_merged()

        QMessageBox.information(self, "提示", "设置已保存，配置已重新生成")

    def _browse_binary(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 sing-box 可执行文件", "", "All Files (*)"
        )
        if path:
            self.singbox_path.setText(path)
