"""系统代理设置（Mac/Windows）"""
import platform
import subprocess
from typing import Optional


class SystemProxy:
    """管理系统代理设置"""

    @staticmethod
    def set_proxy(host: str = "127.0.0.1", http_port: int = 2080, socks_port: int = 2081):
        """设置系统代理"""
        system = platform.system()
        if system == "Darwin":
            SystemProxy._set_mac_proxy(host, http_port, socks_port)
        elif system == "Windows":
            SystemProxy._set_windows_proxy(host, http_port)

    @staticmethod
    def clear_proxy():
        """清除系统代理"""
        system = platform.system()
        if system == "Darwin":
            SystemProxy._clear_mac_proxy()
        elif system == "Windows":
            SystemProxy._clear_windows_proxy()

    @staticmethod
    def _get_mac_services() -> list[str]:
        """获取 Mac 网络服务列表"""
        result = subprocess.run(
            ["networksetup", "-listallnetworkservices"],
            capture_output=True, text=True
        )
        services = []
        for line in result.stdout.strip().splitlines()[1:]:  # 跳过第一行说明
            if not line.startswith("*"):
                services.append(line.strip())
        return services

    @staticmethod
    def _set_mac_proxy(host: str, http_port: int, socks_port: int):
        for service in SystemProxy._get_mac_services():
            # HTTP 代理
            subprocess.run(
                ["networksetup", "-setwebproxy", service, host, str(http_port)],
                capture_output=True
            )
            # HTTPS 代理
            subprocess.run(
                ["networksetup", "-setsecurewebproxy", service, host, str(http_port)],
                capture_output=True
            )
            # SOCKS 代理
            subprocess.run(
                ["networksetup", "-setsocksfirewallproxy", service, host, str(socks_port)],
                capture_output=True
            )

    @staticmethod
    def _clear_mac_proxy():
        for service in SystemProxy._get_mac_services():
            subprocess.run(["networksetup", "-setwebproxystate", service, "off"], capture_output=True)
            subprocess.run(["networksetup", "-setsecurewebproxystate", service, "off"], capture_output=True)
            subprocess.run(["networksetup", "-setsocksfirewallproxystate", service, "off"], capture_output=True)

    @staticmethod
    def _set_windows_proxy(host: str, http_port: int):
        proxy = f"{host}:{http_port}"
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy)
        winreg.CloseKey(key)

    @staticmethod
    def _clear_windows_proxy():
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
