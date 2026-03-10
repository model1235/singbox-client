"""sing-box 核心进程管理"""
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, QProcess, QTimer


class SingBoxCore(QObject):
    """管理 sing-box 核心进程的启动、停止和状态监控"""

    started = Signal()
    stopped = Signal()
    error = Signal(str)
    log_output = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process: Optional[QProcess] = None
        self._sudo_process: Optional[subprocess.Popen] = None
        self._config_path: Optional[str] = None
        self._needs_sudo = False

        # 数据目录
        self.data_dir = self._get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # sing-box 二进制路径
        self.bin_path = self._find_binary()

        # sudo 进程日志读取定时器
        self._sudo_timer = QTimer(self)
        self._sudo_timer.timeout.connect(self._read_sudo_output)

    def _get_data_dir(self) -> Path:
        if platform.system() == "Windows":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path.home() / ".config"
        return base / "singbox-client"

    def _find_binary(self) -> Optional[str]:
        system = platform.system()
        name = "sing-box.exe" if system == "Windows" else "sing-box"

        # 打包后的资源目录
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            app_dir = Path(sys._MEIPASS)
        else:
            app_dir = Path(__file__).parent.parent.parent
        bundled = app_dir / "resources" / name
        if bundled.exists():
            return str(bundled)

        # 数据目录
        data_bin = self.data_dir / "bin" / name
        if data_bin.exists():
            return str(data_bin)

        # 系统 PATH
        found = shutil.which("sing-box")
        if found:
            return found

        return None

    @property
    def is_running(self) -> bool:
        if self._needs_sudo:
            return self._sudo_process is not None and self._sudo_process.poll() is None
        return self._process is not None and self._process.state() == QProcess.Running

    @property
    def config_dir(self) -> Path:
        return self.data_dir / "configs"

    @property
    def active_config_path(self) -> Optional[str]:
        return self._config_path

    def start(self, config_path: str, need_sudo: bool = False) -> bool:
        """启动 sing-box。need_sudo=True 时以管理员权限运行（TUN 模式需要）"""
        if self.is_running:
            self.error.emit("sing-box 已在运行中")
            return False

        if not self.bin_path:
            self.error.emit("未找到 sing-box 二进制文件，请在设置中配置路径")
            return False

        if not os.path.exists(config_path):
            self.error.emit(f"配置文件不存在: {config_path}")
            return False

        self._config_path = config_path
        self._needs_sudo = need_sudo

        args = ["run", "-c", config_path, "--disable-color"]

        if need_sudo:
            return self._start_with_sudo(args)
        else:
            return self._start_normal(args)

    def _start_normal(self, args: list[str]) -> bool:
        """普通权限启动"""
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)

        self.log_output.emit(f"启动: {self.bin_path} {' '.join(args)}")
        self._process.start(self.bin_path, args)

        if self._process.waitForStarted(5000):
            self.started.emit()
            return True
        else:
            self.error.emit("sing-box 启动超时")
            self._process = None
            return False

    def _start_with_sudo(self, args: list[str]) -> bool:
        """以管理员权限启动（TUN 模式）"""
        system = platform.system()
        cmd_args = [self.bin_path] + args

        try:
            if system == "Darwin":
                # macOS: 用 osascript 弹出密码框
                escaped_cmd = " ".join(
                    arg.replace("\\", "\\\\").replace('"', '\\"') for arg in cmd_args
                )
                script = (
                    f'do shell script "{escaped_cmd}" '
                    f'with administrator privileges '
                    f'without altering line endings'
                )
                # osascript 会阻塞等密码输入，所以不能直接用
                # 改用一个 helper 脚本方式：先用 osascript 授权安装 sing-box 到 /usr/local/bin 并设置权限
                # 更实际的方案：用 subprocess 以 sudo 运行，配合 askpass
                self.log_output.emit("启动 TUN 模式 (需要管理员权限)...")

                # 创建一个 askpass 脚本让 sudo 弹出图形化密码框
                askpass_script = self.data_dir / "askpass.sh"
                askpass_script.write_text(
                    '#!/bin/bash\n'
                    'osascript -e \'display dialog "SingBox Client 需要管理员权限来创建 TUN 网卡" '
                    'default answer "" with hidden answer with title "输入密码" '
                    'buttons {"取消","确定"} default button "确定"\' '
                    '-e \'text returned of result\' 2>/dev/null\n'
                )
                askpass_script.chmod(0o755)

                env = os.environ.copy()
                env["SUDO_ASKPASS"] = str(askpass_script)

                self._sudo_process = subprocess.Popen(
                    ["sudo", "-A"] + cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                )

            elif system == "Windows":
                # Windows: 用 runas 提权
                import ctypes
                self.log_output.emit("启动 TUN 模式 (需要管理员权限)...")

                # 检查是否已有管理员权限
                if ctypes.windll.shell32.IsUserAnAdmin():
                    self._sudo_process = subprocess.Popen(
                        cmd_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
                else:
                    # 用 gsudo 或直接以管理员权限重启
                    gsudo = shutil.which("gsudo")
                    if gsudo:
                        self._sudo_process = subprocess.Popen(
                            [gsudo] + cmd_args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                        )
                    else:
                        # 用 PowerShell Start-Process -Verb RunAs
                        ps_cmd = (
                            f'Start-Process -FilePath "{self.bin_path}" '
                            f'-ArgumentList "{" ".join(args)}" '
                            f'-Verb RunAs -Wait'
                        )
                        self._sudo_process = subprocess.Popen(
                            ["powershell", "-Command", ps_cmd],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                        )
            else:
                self.error.emit(f"不支持的系统: {system}")
                return False

            # 启动日志读取定时器
            self._sudo_timer.start(500)
            self.log_output.emit("sing-box (TUN) 进程已启动")
            self.started.emit()
            return True

        except Exception as e:
            self.error.emit(f"提权启动失败: {e}")
            return False

    def stop(self):
        """停止 sing-box"""
        if self._needs_sudo and self._sudo_process:
            self._stop_sudo()
        elif self._process and self._process.state() == QProcess.Running:
            self._process.terminate()
            if not self._process.waitForFinished(5000):
                self._process.kill()
                self._process.waitForFinished(3000)

    def _stop_sudo(self):
        """停止以 sudo 运行的进程"""
        if not self._sudo_process:
            return

        self._sudo_timer.stop()

        try:
            system = platform.system()
            if system == "Darwin":
                # macOS: 用 sudo kill 来终止
                subprocess.run(
                    ["sudo", "-A", "kill", str(self._sudo_process.pid)],
                    env={"SUDO_ASKPASS": str(self.data_dir / "askpass.sh"),
                         "PATH": os.environ.get("PATH", "")},
                    timeout=5
                )
            elif system == "Windows":
                self._sudo_process.terminate()

            self._sudo_process.wait(timeout=5)
        except Exception:
            try:
                self._sudo_process.kill()
            except Exception:
                pass

        self._sudo_process = None
        self.log_output.emit("sing-box (TUN) 已停止")
        self.stopped.emit()

    def restart(self, config_path: Optional[str] = None):
        path = config_path or self._config_path
        if not path:
            self.error.emit("没有可用的配置文件")
            return
        need_sudo = self._needs_sudo
        self.stop()
        self.start(path, need_sudo=need_sudo)

    def check_config(self, config_path: str) -> tuple[bool, str]:
        if not self.bin_path:
            return False, "未找到 sing-box 二进制文件"
        try:
            result = subprocess.run(
                [self.bin_path, "check", "-c", config_path],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, "配置文件有效"
            return False, result.stderr.strip() or result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def set_binary_path(self, path: str):
        if os.path.exists(path):
            self.bin_path = path

    def _read_sudo_output(self):
        """读取 sudo 进程的输出"""
        if not self._sudo_process:
            self._sudo_timer.stop()
            return

        # 检查进程是否已退出
        ret = self._sudo_process.poll()
        if ret is not None:
            # 读取剩余输出
            remaining = self._sudo_process.stdout.read()
            if remaining:
                for line in remaining.decode("utf-8", errors="replace").strip().splitlines():
                    self.log_output.emit(line)
            self._sudo_timer.stop()
            self._sudo_process = None
            self.log_output.emit(f"sing-box (TUN) 已退出 (code={ret})")
            self.stopped.emit()
            return

        # 非阻塞读取
        try:
            import select
            if hasattr(select, 'select'):
                readable, _, _ = select.select([self._sudo_process.stdout], [], [], 0)
                if readable:
                    line = self._sudo_process.stdout.readline()
                    if line:
                        self.log_output.emit(line.decode("utf-8", errors="replace").rstrip())
        except Exception:
            pass

    def _on_output(self):
        if self._process:
            data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            for line in data.strip().splitlines():
                self.log_output.emit(line)

    def _on_finished(self, exit_code, exit_status):
        self.log_output.emit(f"sing-box 已退出 (code={exit_code})")
        self._process = None
        self.stopped.emit()

    def _on_error(self, error):
        error_msg = {
            QProcess.FailedToStart: "启动失败，请检查二进制文件路径",
            QProcess.Crashed: "进程异常崩溃",
            QProcess.Timedout: "操作超时",
            QProcess.WriteError: "写入错误",
            QProcess.ReadError: "读取错误",
        }.get(error, f"未知错误: {error}")
        self.error.emit(error_msg)
