"""sing-box 配置文件管理 — 订阅合并 + inbounds 生成"""
import json
import os
import re
import time
import copy
from pathlib import Path
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal


class Profile:
    """订阅/配置档案"""

    def __init__(self, name: str, profile_type: str = "local",
                 url: str = "", file_path: str = "", updated_at: float = 0):
        self.name = name
        self.type = profile_type  # "local" | "remote"
        self.url = url
        self.file_path = file_path          # 订阅原始文件
        self.merged_path = ""               # 合并后的完整配置文件
        self.updated_at = updated_at or time.time()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "file_path": self.file_path,
            "merged_path": self.merged_path,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Profile":
        p = Profile(
            name=d["name"],
            profile_type=d.get("type", "local"),
            url=d.get("url", ""),
            file_path=d.get("file_path", ""),
            updated_at=d.get("updated_at", 0),
        )
        p.merged_path = d.get("merged_path", "")
        return p


class ConfigManager(QObject):
    """管理配置文件和订阅，负责合并生成完整 sing-box 配置"""

    profiles_changed = Signal()
    active_changed = Signal(str)

    def __init__(self, data_dir: Path, settings, parent=None):
        super().__init__(parent)
        self.data_dir = data_dir
        self.settings = settings
        self.config_dir = data_dir / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.merged_dir = data_dir / "merged"
        self.merged_dir.mkdir(parents=True, exist_ok=True)

        self._meta_path = data_dir / "profiles.json"
        self._profiles: list[Profile] = []
        self._active_name: Optional[str] = None
        self._load_meta()

    # ---- 属性 ----

    @property
    def profiles(self) -> list[Profile]:
        return self._profiles

    @property
    def active_profile(self) -> Optional[Profile]:
        for p in self._profiles:
            if p.name == self._active_name:
                return p
        return None

    @property
    def active_config_path(self) -> Optional[str]:
        """返回合并后的完整配置路径，供 sing-box 使用"""
        p = self.active_profile
        if p and p.merged_path and os.path.exists(p.merged_path):
            return p.merged_path
        return None

    # ---- 配置操作 ----

    def add_local_profile(self, name: str, config_content: str) -> Profile:
        """添加本地配置（完整配置，不做合并）"""
        file_path = str(self.config_dir / f"{name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config_content)

        profile = Profile(name=name, profile_type="local", file_path=file_path)
        profile.merged_path = file_path  # 本地完整配置不需要合并
        self._profiles.append(profile)
        self._save_meta()
        self.profiles_changed.emit()
        return profile

    def import_local_file(self, name: str, source_path: str) -> Profile:
        """导入本地配置文件"""
        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.add_local_profile(name, content)

    def add_subscription(self, name: str, url: str) -> Optional[Profile]:
        """添加远程订阅"""
        file_path = str(self.config_dir / f"{name}.json")
        merged_path = str(self.merged_dir / f"{name}.json")
        profile = Profile(name=name, profile_type="remote", url=url, file_path=file_path)
        profile.merged_path = merged_path
        self._profiles.append(profile)

        if self.update_subscription(profile):
            self._save_meta()
            self.profiles_changed.emit()
            return profile
        else:
            self._profiles.remove(profile)
            return None

    def update_subscription(self, profile: Profile) -> bool:
        """更新远程订阅并重新合并配置"""
        if profile.type != "remote" or not profile.url:
            return False

        try:
            resp = requests.get(profile.url, timeout=30,
                                headers={"User-Agent": "singbox-client/1.0"})
            resp.raise_for_status()
            content = resp.text

            sub_config = json.loads(content)

            # 保存订阅原始文件
            with open(profile.file_path, "w", encoding="utf-8") as f:
                json.dump(sub_config, f, indent=2, ensure_ascii=False)

            # 从订阅配置中同步设置
            self._sync_settings_from_config(sub_config)

            # 合并生成完整配置
            self._merge_config(profile, sub_config)

            profile.updated_at = time.time()
            self._save_meta()
            return True
        except Exception as e:
            print(f"更新订阅失败 [{profile.name}]: {e}")
            return False

    def update_all_subscriptions(self) -> list[str]:
        """更新所有远程订阅，返回失败列表"""
        failed = []
        for p in self._profiles:
            if p.type == "remote":
                if not self.update_subscription(p):
                    failed.append(p.name)
        return failed

    def rebuild_merged_config(self, profile_name: str):
        """用户修改设置后，重新合并指定配置"""
        for p in self._profiles:
            if p.name == profile_name and p.type == "remote":
                if os.path.exists(p.file_path):
                    with open(p.file_path, "r", encoding="utf-8") as f:
                        sub_config = json.load(f)
                    self._merge_config(p, sub_config)

    def rebuild_all_merged(self):
        """重新合并所有远程订阅配置（设置变更后调用）"""
        for p in self._profiles:
            if p.type == "remote":
                self.rebuild_merged_config(p.name)

    def set_active(self, name: str):
        self._active_name = name
        self._save_meta()
        self.active_changed.emit(name)

    def remove_profile(self, name: str):
        self._profiles = [p for p in self._profiles if p.name != name]
        for path in [self.config_dir / f"{name}.json", self.merged_dir / f"{name}.json"]:
            if path.exists():
                path.unlink()
        if self._active_name == name:
            self._active_name = None
        self._save_meta()
        self.profiles_changed.emit()

    def get_config_content(self, name: str, merged: bool = False) -> str:
        """读取配置内容。merged=True 返回合并后的，否则返回原始订阅内容"""
        for p in self._profiles:
            if p.name == name:
                path = p.merged_path if merged else p.file_path
                if path and os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        return f.read()
        return ""

    def save_config_content(self, name: str, content: str):
        """保存配置内容（本地配置直接保存，远程订阅保存后重新合并）"""
        for p in self._profiles:
            if p.name == name:
                with open(p.file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                if p.type == "remote":
                    try:
                        sub_config = json.loads(content)
                        self._merge_config(p, sub_config)
                    except json.JSONDecodeError:
                        pass
                break

    def get_outbounds_info(self, name: str) -> list[dict]:
        """获取配置中的 outbounds 节点信息"""
        content = self.get_config_content(name)
        if not content:
            return []
        try:
            config = json.loads(content)
            outbounds = config.get("outbounds", [])
            result = []
            for ob in outbounds:
                info = {
                    "tag": ob.get("tag", ""),
                    "type": ob.get("type", ""),
                    "server": ob.get("server", ""),
                    "server_port": ob.get("server_port", ""),
                }
                if ob["type"] in ("selector", "urltest"):
                    info["outbounds"] = ob.get("outbounds", [])
                if ob.get("tls", {}).get("server_name"):
                    info["server_name"] = ob["tls"]["server_name"]
                result.append(info)
            return result
        except Exception:
            return []

    # ---- 配置合并 ----

    def _merge_config(self, profile: Profile, sub_config: dict):
        """将订阅配置与客户端生成的 inbounds/log 合并"""
        merged = copy.deepcopy(sub_config)

        # 生成 log
        merged["log"] = self._build_log()

        # 生成 inbounds（如果订阅中没有的话）
        if "inbounds" not in merged or not merged["inbounds"]:
            merged["inbounds"] = self._build_inbounds()
        else:
            # 订阅中有 inbounds，按用户设置更新端口
            self._update_inbound_ports(merged["inbounds"])

        # 确保 experimental.clash_api 存在且端口正确
        self._ensure_clash_api(merged)

        # 写入合并后的文件
        if not profile.merged_path:
            profile.merged_path = str(self.merged_dir / f"{profile.name}.json")

        with open(profile.merged_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

    def _build_log(self) -> dict:
        return {
            "level": self.settings.get("log_level", "info"),
            "timestamp": True,
        }

    def _build_inbounds(self) -> list[dict]:
        """根据用户设置生成 inbounds"""
        inbounds = []
        s = self.settings

        # TUN 模式
        if s.get("enable_tun"):
            tun = {
                "type": "tun",
                "tag": "tun-in",
                "address": [
                    "172.18.0.1/30",
                    "fdfe:dcba:9876::1/126"
                ],
                "auto_route": True,
                "strict_route": s.get("tun_strict_route", True),
                "stack": s.get("tun_stack", "mixed"),
                "sniff": True,
                "sniff_override_destination": s.get("sniff_override", True),
            }
            inbounds.append(tun)

        # Mixed 代理（HTTP + SOCKS5 合一）
        if s.get("enable_mixed"):
            mixed = {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": s.get("listen_address", "127.0.0.1"),
                "listen_port": s.get("mixed_port", 2080),
                "sniff": True,
                "sniff_override_destination": s.get("sniff_override", True),
            }
            inbounds.append(mixed)

        # HTTP 代理
        if s.get("enable_http"):
            http = {
                "type": "http",
                "tag": "http-in",
                "listen": s.get("listen_address", "127.0.0.1"),
                "listen_port": s.get("http_port", 2081),
                "sniff": True,
                "sniff_override_destination": s.get("sniff_override", True),
            }
            inbounds.append(http)

        # SOCKS5 代理
        if s.get("enable_socks"):
            socks = {
                "type": "socks",
                "tag": "socks-in",
                "listen": s.get("listen_address", "127.0.0.1"),
                "listen_port": s.get("socks_port", 2082),
                "sniff": True,
                "sniff_override_destination": s.get("sniff_override", True),
            }
            inbounds.append(socks)

        # 如果什么都没开，至少加一个 mixed
        if not inbounds:
            inbounds.append({
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "127.0.0.1",
                "listen_port": 2080,
                "sniff": True,
                "sniff_override_destination": True,
            })

        return inbounds

    def _update_inbound_ports(self, inbounds: list[dict]):
        """更新已有 inbounds 中的端口为用户设置值"""
        s = self.settings
        port_map = {
            "mixed": s.get("mixed_port", 2080),
            "http": s.get("http_port", 2081),
            "socks": s.get("socks_port", 2082),
        }
        for ib in inbounds:
            ib_type = ib.get("type", "")
            if ib_type in port_map:
                ib["listen_port"] = port_map[ib_type]
                ib["listen"] = s.get("listen_address", "127.0.0.1")

    def _ensure_clash_api(self, config: dict):
        """确保 clash API 配置正确"""
        api_port = self.settings.get("api_port", 9090)
        exp = config.setdefault("experimental", {})
        clash_api = exp.setdefault("clash_api", {})
        clash_api["external_controller"] = f"127.0.0.1:{api_port}"

    def _sync_settings_from_config(self, sub_config: dict):
        """从订阅配置中提取设置同步到应用"""
        # 同步 clash API 端口
        try:
            controller = sub_config.get("experimental", {}).get("clash_api", {}).get("external_controller", "")
            if controller:
                match = re.search(r":(\d+)$", controller)
                if match:
                    port = int(match.group(1))
                    self.settings.set("api_port", port)
        except Exception:
            pass

        # 同步 DNS 服务器信息（记录但不覆盖用户设置）
        try:
            dns_servers = sub_config.get("dns", {}).get("servers", [])
            if dns_servers:
                self.settings.set("_sub_dns_servers",
                                  [s.get("server", "") for s in dns_servers if s.get("server")])
        except Exception:
            pass

    # ---- 持久化 ----

    def _load_meta(self):
        if self._meta_path.exists():
            try:
                with open(self._meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._profiles = [Profile.from_dict(d) for d in data.get("profiles", [])]
                self._active_name = data.get("active")
            except Exception:
                self._profiles = []
                self._active_name = None

    def _save_meta(self):
        data = {
            "profiles": [p.to_dict() for p in self._profiles],
            "active": self._active_name,
        }
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
