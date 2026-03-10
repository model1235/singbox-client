"""日志页面"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QComboBox
)
from PySide6.QtCore import Slot


class LogsPage(QWidget):
    """实时日志查看"""

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("运行日志")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "INFO", "WARN", "ERROR"])
        header.addWidget(QLabel("日志级别:"))
        header.addWidget(self.level_combo)

        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._clear)
        header.addWidget(self.btn_clear)

        layout.addLayout(header)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
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
        self.ctx.core.log_output.connect(self._on_log)

    @Slot(str)
    def _on_log(self, text: str):
        level = self.level_combo.currentText()
        if level == "全部" or level.lower() in text.lower():
            self.log_view.appendPlainText(text)

    def _clear(self):
        self.log_view.clear()
