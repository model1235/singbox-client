"""节点页面 - outbound 分组、延迟测试、流量统计"""
import json
from collections import defaultdict

import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTabWidget, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Slot, QTimer


class TrafficCard(QFrame):
    """单个 outbound 的流量卡片"""

    def __init__(self, tag: str, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.setStyleSheet("""
            TrafficCard {
                background-color: #313244;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._tag_label = QLabel(tag)
        self._tag_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #cdd6f4;")

        self._type_label = QLabel("")
        self._type_label.setStyleSheet("font-size: 11px; color: #a6adc8;")

        self._traffic_label = QLabel("↑ 0 B  ↓ 0 B")
        self._traffic_label.setStyleSheet("font-size: 12px; color: #89b4fa;")

        self._conn_label = QLabel("连接数: 0")
        self._conn_label.setStyleSheet("font-size: 11px; color: #a6adc8;")

        layout.addWidget(self._tag_label)
        layout.addWidget(self._type_label)
        layout.addWidget(self._traffic_label)
        layout.addWidget(self._conn_label)

    def update_stats(self, upload: int, download: int, conn_count: int, ob_type: str = ""):
        self._traffic_label.setText(f"↑ {_fmt(upload)}  ↓ {_fmt(download)}")
        self._conn_label.setText(f"连接数: {conn_count}")
        if ob_type:
            self._type_label.setText(ob_type)


class ProxiesPage(QWidget):
    """节点与流量页面"""

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self._traffic_cards: dict[str, TrafficCard] = {}
        self._cumulative_upload: dict[str, int] = defaultdict(int)
        self._cumulative_download: dict[str, int] = defaultdict(int)
        self._known_conn_ids: set[str] = set()
        self._setup_ui()

        # 定时刷新
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 标题
        header = QHBoxLayout()
        title = QLabel("节点与流量")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.btn_test_all = QPushButton("全部测速")
        self.btn_test_all.setObjectName("primary")
        self.btn_test_all.clicked.connect(self._test_all_delay)

        self.btn_reset = QPushButton("重置统计")
        self.btn_reset.clicked.connect(self._reset_stats)

        header.addWidget(self.btn_reset)
        header.addWidget(self.btn_test_all)
        layout.addLayout(header)

        # 总流量
        total_layout = QHBoxLayout()
        self.total_label = QLabel("总流量  ↑ 0 B  ↓ 0 B")
        self.total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #cdd6f4;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        layout.addLayout(total_layout)

        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        # Tab 1: 流量统计（按 outbound 卡片展示）
        self._traffic_tab = QWidget()
        self._traffic_layout = QVBoxLayout(self._traffic_tab)
        self._traffic_layout.setContentsMargins(0, 12, 0, 0)

        self._cards_grid_widget = QWidget()
        self._cards_grid = QGridLayout(self._cards_grid_widget)
        self._cards_grid.setSpacing(10)
        self._traffic_layout.addWidget(self._cards_grid_widget)
        self._traffic_layout.addStretch()
        tabs.addTab(self._traffic_tab, "流量统计")

        # Tab 2: 节点列表（表格展示）
        nodes_widget = QWidget()
        nodes_layout = QVBoxLayout(nodes_widget)
        nodes_layout.setContentsMargins(0, 12, 0, 0)

        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(6)
        self.nodes_table.setHorizontalHeaderLabels([
            "节点名", "类型", "服务器", "端口", "延迟", "操作"
        ])
        self.nodes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.nodes_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.nodes_table.verticalHeader().setVisible(False)
        self.nodes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.nodes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        nodes_layout.addWidget(self.nodes_table)

        tabs.addTab(nodes_widget, "节点列表")

        # Tab 3: 分组管理
        groups_widget = QWidget()
        groups_layout = QVBoxLayout(groups_widget)
        groups_layout.setContentsMargins(0, 12, 0, 0)

        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(4)
        self.groups_table.setHorizontalHeaderLabels(["分组名", "类型", "当前节点", "节点列表"])
        self.groups_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.groups_table.verticalHeader().setVisible(False)
        self.groups_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        groups_layout.addWidget(self.groups_table)

        tabs.addTab(groups_widget, "分组管理")

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_nodes()
        self._refresh()

    def _refresh(self):
        """从 Clash API 获取连接数据，聚合流量"""
        if not self.ctx.core.is_running:
            return

        try:
            api_port = self.ctx.settings.get("api_port")
            resp = requests.get(f"http://127.0.0.1:{api_port}/connections", timeout=1)
            data = resp.json()
        except Exception:
            return

        connections = data.get("connections", []) or []

        # 当前活跃连接的流量（按 outbound 聚合）
        active_upload: dict[str, int] = defaultdict(int)
        active_download: dict[str, int] = defaultdict(int)
        active_count: dict[str, int] = defaultdict(int)

        current_conn_ids = set()
        for conn in connections:
            conn_id = conn.get("id", "")
            current_conn_ids.add(conn_id)
            chains = conn.get("chains", [])
            # chains[0] 是最终出站的 outbound tag
            outbound = chains[0] if chains else "unknown"

            ul = conn.get("upload", 0)
            dl = conn.get("download", 0)
            active_upload[outbound] += ul
            active_download[outbound] += dl
            active_count[outbound] += 1

        # 检测已关闭的连接，将其流量累加到 cumulative
        # （简化处理：每次刷新直接用 active 数据 + cumulative 历史）
        # 这里用 active + cumulative 来展示

        # 收集所有已知的 outbound
        all_outbounds = set(active_upload.keys()) | set(self._cumulative_upload.keys())

        # 获取 outbound 类型信息
        ob_types = self._get_outbound_types()

        # 更新/创建卡片
        total_up = 0
        total_down = 0

        for tag in sorted(all_outbounds):
            if tag in ("direct", "dns-out", "block"):
                continue  # 跳过内置 outbound

            up = active_upload.get(tag, 0) + self._cumulative_upload.get(tag, 0)
            down = active_download.get(tag, 0) + self._cumulative_download.get(tag, 0)
            count = active_count.get(tag, 0)
            total_up += up
            total_down += down

            if tag not in self._traffic_cards:
                card = TrafficCard(tag)
                self._traffic_cards[tag] = card
                idx = len(self._traffic_cards) - 1
                row, col = divmod(idx, 3)
                self._cards_grid.addWidget(card, row, col)

            self._traffic_cards[tag].update_stats(up, down, count, ob_types.get(tag, ""))

        self.total_label.setText(f"总流量  ↑ {_fmt(total_up)}  ↓ {_fmt(total_down)}")

    def _refresh_nodes(self):
        """刷新节点列表和分组表"""
        profile = self.ctx.config_manager.active_profile
        if not profile:
            return

        outbounds = self.ctx.config_manager.get_outbounds_info(profile.name)
        if not outbounds:
            return

        # 节点表（实际代理节点，排除 selector/urltest/direct/block/dns）
        group_types = {"selector", "urltest", "direct", "block", "dns"}
        nodes = [ob for ob in outbounds if ob["type"] not in group_types]
        groups = [ob for ob in outbounds if ob["type"] in ("selector", "urltest")]

        self.nodes_table.setRowCount(len(nodes))
        for i, node in enumerate(nodes):
            self.nodes_table.setItem(i, 0, QTableWidgetItem(node["tag"]))
            self.nodes_table.setItem(i, 1, QTableWidgetItem(node["type"]))
            self.nodes_table.setItem(i, 2, QTableWidgetItem(str(node.get("server", ""))))
            self.nodes_table.setItem(i, 3, QTableWidgetItem(str(node.get("server_port", ""))))
            self.nodes_table.setItem(i, 4, QTableWidgetItem("--"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_test = QPushButton("测速")
            btn_test.setFixedSize(50, 28)
            btn_test.clicked.connect(lambda _, tag=node["tag"], row=i: self._test_delay(tag, row))
            btn_layout.addWidget(btn_test)
            self.nodes_table.setCellWidget(i, 5, btn_widget)
            self.nodes_table.setRowHeight(i, 38)

        # 分组表
        self.groups_table.setRowCount(len(groups))
        for i, grp in enumerate(groups):
            self.groups_table.setItem(i, 0, QTableWidgetItem(grp["tag"]))
            self.groups_table.setItem(i, 1, QTableWidgetItem(grp["type"]))
            # 获取当前选中的节点
            now = self._get_group_now(grp["tag"])
            self.groups_table.setItem(i, 2, QTableWidgetItem(now))
            members = ", ".join(grp.get("outbounds", []))
            self.groups_table.setItem(i, 3, QTableWidgetItem(members))
            self.groups_table.setRowHeight(i, 38)

    def _get_outbound_types(self) -> dict[str, str]:
        """获取 outbound tag -> type 映射"""
        profile = self.ctx.config_manager.active_profile
        if not profile:
            return {}
        outbounds = self.ctx.config_manager.get_outbounds_info(profile.name)
        return {ob["tag"]: ob["type"] for ob in outbounds}

    def _get_group_now(self, group_tag: str) -> str:
        """获取分组当前选中的节点"""
        if not self.ctx.core.is_running:
            return "--"
        try:
            api_port = self.ctx.settings.get("api_port")
            resp = requests.get(f"http://127.0.0.1:{api_port}/proxies/{group_tag}", timeout=1)
            data = resp.json()
            return data.get("now", "--")
        except Exception:
            return "--"

    def _test_delay(self, tag: str, row: int):
        """测试单个节点延迟"""
        if not self.ctx.core.is_running:
            return
        try:
            api_port = self.ctx.settings.get("api_port")
            resp = requests.get(
                f"http://127.0.0.1:{api_port}/proxies/{tag}/delay",
                params={"timeout": 5000, "url": "https://www.gstatic.com/generate_204"},
                timeout=6
            )
            data = resp.json()
            delay = data.get("delay", 0)
            if delay > 0:
                item = QTableWidgetItem(f"{delay} ms")
                if delay < 200:
                    item.setForeground(Qt.green)
                elif delay < 500:
                    item.setForeground(Qt.yellow)
                else:
                    item.setForeground(Qt.red)
            else:
                item = QTableWidgetItem("超时")
                item.setForeground(Qt.red)
            self.nodes_table.setItem(row, 4, item)
        except Exception:
            self.nodes_table.setItem(row, 4, QTableWidgetItem("失败"))

    @Slot()
    def _test_all_delay(self):
        """测试所有节点延迟"""
        for row in range(self.nodes_table.rowCount()):
            tag_item = self.nodes_table.item(row, 0)
            if tag_item:
                self._test_delay(tag_item.text(), row)

    @Slot()
    def _reset_stats(self):
        """重置流量统计"""
        self._cumulative_upload.clear()
        self._cumulative_download.clear()
        self._known_conn_ids.clear()
        for card in self._traffic_cards.values():
            card.update_stats(0, 0, 0)
        self.total_label.setText("总流量  ↑ 0 B  ↓ 0 B")


def _fmt(b: int) -> str:
    """格式化字节数"""
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
