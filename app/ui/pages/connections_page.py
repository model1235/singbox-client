"""连接列表页面"""
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot, QTimer

import requests


class ConnectionsPage(QWidget):
    """活跃连接列表"""

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self._setup_ui()

        # 自动刷新定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("连接列表")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.label_count = QLabel("连接数: 0")
        header.addWidget(self.label_count)

        self.btn_close_all = QPushButton("关闭所有连接")
        self.btn_close_all.setObjectName("danger")
        self.btn_close_all.clicked.connect(self._close_all)
        header.addWidget(self.btn_close_all)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "类型", "来源", "目标", "规则", "链路", "下载/上传"
        ])
        for i in range(6):
            self.table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.Stretch if i in (2, 4) else QHeaderView.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, 1)

    def _refresh(self):
        if not self.ctx.core.is_running:
            return
        try:
            api_port = self.ctx.settings.get("api_port")
            resp = requests.get(f"http://127.0.0.1:{api_port}/connections", timeout=1)
            data = resp.json()
            connections = data.get("connections", []) or []
            self.label_count.setText(f"连接数: {len(connections)}")

            self.table.setRowCount(len(connections))
            for i, conn in enumerate(connections):
                meta = conn.get("metadata", {})
                self.table.setItem(i, 0, QTableWidgetItem(meta.get("network", "")))
                self.table.setItem(i, 1, QTableWidgetItem(
                    f"{meta.get('sourceIP', '')}:{meta.get('sourcePort', '')}"
                ))
                dest = meta.get("destinationIP", "") or meta.get("host", "")
                self.table.setItem(i, 2, QTableWidgetItem(
                    f"{dest}:{meta.get('destinationPort', '')}"
                ))
                self.table.setItem(i, 3, QTableWidgetItem(conn.get("rule", "")))
                chains = conn.get("chains", [])
                self.table.setItem(i, 4, QTableWidgetItem(" → ".join(chains)))

                dl = self._format_bytes(conn.get("download", 0))
                ul = self._format_bytes(conn.get("upload", 0))
                self.table.setItem(i, 5, QTableWidgetItem(f"↓{dl} ↑{ul}"))
        except Exception:
            pass

    def _close_all(self):
        try:
            api_port = self.ctx.settings.get("api_port")
            requests.delete(f"http://127.0.0.1:{api_port}/connections", timeout=2)
        except Exception:
            pass

    @staticmethod
    def _format_bytes(b: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.1f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
