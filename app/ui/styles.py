"""全局样式表"""

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

/* 侧边栏 */
#sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}

#sidebar QPushButton {
    text-align: left;
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    margin: 2px 8px;
    color: #a6adc8;
    font-size: 13px;
}

#sidebar QPushButton:hover {
    background-color: #313244;
    color: #cdd6f4;
}

#sidebar QPushButton:checked {
    background-color: #45475a;
    color: #cdd6f4;
    font-weight: bold;
}

/* 标题栏 */
#header {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 8px 16px;
}

/* 卡片 */
.card {
    background-color: #313244;
    border-radius: 8px;
    padding: 12px;
}

/* 按钮 */
QPushButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #585b70;
}

QPushButton:pressed {
    background-color: #6c7086;
}

QPushButton#primary {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}

QPushButton#primary:hover {
    background-color: #74c7ec;
}

QPushButton#danger {
    background-color: #f38ba8;
    color: #1e1e2e;
}

QPushButton#danger:hover {
    background-color: #eba0ac;
}

QPushButton#success {
    background-color: #a6e3a1;
    color: #1e1e2e;
}

/* 输入框 */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #89b4fa;
}

/* 表格 */
QTableWidget {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 6px;
    gridline-color: #313244;
}

QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #313244;
}

QTableWidget::item:selected {
    background-color: #45475a;
}

QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    border: none;
    border-bottom: 1px solid #313244;
    padding: 8px;
    font-weight: bold;
}

/* 滚动条 */
QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1e1e2e;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 4px;
    min-width: 30px;
}

/* 标签页 */
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px 16px;
    border: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #313244;
    color: #cdd6f4;
}

/* 下拉框 */
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
}

/* 复选框 */
QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #45475a;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

/* 分组框 */
QGroupBox {
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 8px;
}

/* 标签 */
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #cdd6f4;
}

QLabel#subtitle {
    color: #a6adc8;
    font-size: 12px;
}

QLabel#status-on {
    color: #a6e3a1;
    font-weight: bold;
}

QLabel#status-off {
    color: #f38ba8;
}

/* 系统托盘菜单 */
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #45475a;
}

QMenu::separator {
    height: 1px;
    background-color: #45475a;
    margin: 4px 8px;
}
"""
