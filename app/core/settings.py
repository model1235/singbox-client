"""应用设置"""
import json
from pathlib import Path


class Settings:
    """读写应用设置"""

    DEFAULTS = {
        # Inbound - TUN
        "enable_tun": False,
        "tun_stack": "mixed",          # system | gvisor | mixed
        "tun_strict_route": True,

        # Inbound - Mixed
        "enable_mixed": True,
        "mixed_port": 2080,

        # Inbound - HTTP
        "enable_http": False,
        "http_port": 2081,

        # Inbound - SOCKS
        "enable_socks": False,
        "socks_port": 2082,

        # Inbound 通用
        "listen_address": "127.0.0.1",
        "sniff_override": True,

        # Clash API
        "api_port": 9090,

        # 日志
        "log_level": "info",  # trace | debug | info | warn | error | fatal | panic

        # 系统代理
        "auto_set_proxy": True,
        "system_proxy_port": 2080,     # 系统代理使用的端口（一般与 mixed 相同）

        # 启动行为
        "auto_start_core": False,
        "start_minimized": False,
        "auto_launch": False,

        # sing-box 核心
        "singbox_binary": "",

        # 主题
        "theme": "dark",
    }

    def __init__(self, data_dir: Path):
        self._path = data_dir / "settings.json"
        self._data: dict = {}
        self._load()

    def get(self, key: str, default=None):
        if default is not None:
            return self._data.get(key, default)
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def all(self) -> dict:
        merged = dict(self.DEFAULTS)
        merged.update(self._data)
        return merged

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
