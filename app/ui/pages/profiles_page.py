"""配置管理页面"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QFormLayout, QFileDialog, QTextEdit, QMessageBox,
    QComboBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot
import time


class AddProfileDialog(QDialog):
    """添加配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加配置")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["远程订阅", "本地文件", "手动输入"])
        form.addRow("类型:", self.type_combo)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("配置名称")
        form.addRow("名称:", self.name_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("订阅链接 URL")
        form.addRow("URL:", self.url_edit)

        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择配置文件...")
        self.file_edit.setReadOnly(True)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_edit)
        self.btn_browse = QPushButton("浏览")
        self.btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(self.btn_browse)
        form.addRow("文件:", file_layout)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("粘贴 sing-box 配置 JSON...")
        self.content_edit.setMinimumHeight(150)
        form.addRow("内容:", self.content_edit)

        layout.addLayout(form)

        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self._on_type_changed(0)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("确定")
        btn_ok.setObjectName("primary")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _on_type_changed(self, index):
        self.url_edit.setVisible(index == 0)
        self.file_edit.setVisible(index == 1)
        self.btn_browse.setVisible(index == 1)
        self.content_edit.setVisible(index == 2)
        # 调整 form 行的 label
        self.url_edit.parent().findChild(QLabel, "")

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON Files (*.json);;All Files (*)"
        )
        if path:
            self.file_edit.setText(path)

    def get_data(self) -> dict:
        return {
            "type": ["remote", "local_file", "local_input"][self.type_combo.currentIndex()],
            "name": self.name_edit.text().strip(),
            "url": self.url_edit.text().strip(),
            "file_path": self.file_edit.text().strip(),
            "content": self.content_edit.toPlainText().strip(),
        }


class ProfilesPage(QWidget):
    """配置管理页面"""

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self._setup_ui()
        self._connect_signals()
        self._refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 标题 + 操作按钮
        header = QHBoxLayout()
        title = QLabel("配置管理")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.btn_add = QPushButton("+ 添加")
        self.btn_add.setObjectName("primary")
        self.btn_update_all = QPushButton("↻ 全部更新")
        header.addWidget(self.btn_update_all)
        header.addWidget(self.btn_add)
        layout.addLayout(header)

        # 配置表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["名称", "类型", "更新时间", "状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, 1)

    def _connect_signals(self):
        self.btn_add.clicked.connect(self._on_add)
        self.btn_update_all.clicked.connect(self._on_update_all)
        self.ctx.config_manager.profiles_changed.connect(self._refresh_table)

    def _refresh_table(self):
        profiles = self.ctx.config_manager.profiles
        self.table.setRowCount(len(profiles))
        active = self.ctx.config_manager.active_profile

        for i, p in enumerate(profiles):
            self.table.setItem(i, 0, QTableWidgetItem(p.name))
            self.table.setItem(i, 1, QTableWidgetItem(
                "订阅" if p.type == "remote" else "本地"
            ))
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(p.updated_at))
            self.table.setItem(i, 2, QTableWidgetItem(t))

            is_active = active and active.name == p.name
            status_item = QTableWidgetItem("● 使用中" if is_active else "")
            if is_active:
                status_item.setForeground(Qt.green)
            self.table.setItem(i, 3, status_item)

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            btn_use = QPushButton("使用")
            btn_use.setObjectName("primary")
            btn_use.setFixedSize(50, 28)
            btn_use.clicked.connect(lambda _, name=p.name: self._on_use(name))

            btn_edit = QPushButton("编辑")
            btn_edit.setFixedSize(50, 28)
            btn_edit.clicked.connect(lambda _, name=p.name: self._on_edit(name))

            btn_del = QPushButton("删除")
            btn_del.setObjectName("danger")
            btn_del.setFixedSize(50, 28)
            btn_del.clicked.connect(lambda _, name=p.name: self._on_delete(name))

            btn_layout.addWidget(btn_use)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)

            self.table.setCellWidget(i, 4, btn_widget)
            self.table.setRowHeight(i, 42)

    @Slot()
    def _on_add(self):
        dlg = AddProfileDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            name = data["name"]
            if not name:
                QMessageBox.warning(self, "提示", "请输入配置名称")
                return

            cm = self.ctx.config_manager
            if data["type"] == "remote":
                if not data["url"]:
                    QMessageBox.warning(self, "提示", "请输入订阅 URL")
                    return
                result = cm.add_subscription(name, data["url"])
                if not result:
                    QMessageBox.warning(self, "错误", "订阅获取失败，请检查 URL")
            elif data["type"] == "local_file":
                if not data["file_path"]:
                    QMessageBox.warning(self, "提示", "请选择配置文件")
                    return
                cm.import_local_file(name, data["file_path"])
            elif data["type"] == "local_input":
                if not data["content"]:
                    QMessageBox.warning(self, "提示", "请输入配置内容")
                    return
                cm.add_local_profile(name, data["content"])

    def _on_use(self, name: str):
        self.ctx.config_manager.set_active(name)
        self._refresh_table()

    def _on_edit(self, name: str):
        content = self.ctx.config_manager.get_config_content(name)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"编辑配置 - {name}")
        dlg.setMinimumSize(600, 500)
        layout = QVBoxLayout(dlg)

        editor = QTextEdit()
        editor.setPlainText(content)
        editor.setStyleSheet("""
            font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            font-size: 13px;
        """)
        layout.addWidget(editor, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(dlg.reject)
        btn_save = QPushButton("保存")
        btn_save.setObjectName("primary")

        def save():
            self.ctx.config_manager.save_config_content(name, editor.toPlainText())
            dlg.accept()

        btn_save.clicked.connect(save)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        dlg.exec()

    def _on_delete(self, name: str):
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除配置「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.ctx.config_manager.remove_profile(name)

    @Slot()
    def _on_update_all(self):
        failed = self.ctx.config_manager.update_all_subscriptions()
        if failed:
            QMessageBox.warning(self, "更新结果", f"以下订阅更新失败:\n{', '.join(failed)}")
        else:
            QMessageBox.information(self, "更新完成", "所有订阅已更新")
        self._refresh_table()
