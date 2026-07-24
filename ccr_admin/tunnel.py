from __future__ import annotations

import base64
import errno
import hashlib
import select
import socket
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

try:
    import paramiko
except ImportError as exc:  # pragma: no cover - exercised on machines without dependencies
    paramiko = None  # type: ignore[assignment]
    PARAMIKO_IMPORT_ERROR: Exception | None = exc
else:
    PARAMIKO_IMPORT_ERROR = None


@dataclass(frozen=True, slots=True)
class TunnelConfig:
    host: str
    ssh_port: int
    username: str
    password: str
    remote_port: int
    local_port: int = 13458
    remote_host: str = "127.0.0.1"

    @property
    def local_url(self) -> str:
        return f"http://127.0.0.1:{self.local_port}"


def host_key_name(host: str, port: int) -> str:
    return host if port == 22 else f"[{host}]:{port}"


def sha256_fingerprint(key: Any) -> str:
    digest = hashlib.sha256(key.asbytes()).digest()
    value = base64.b64encode(digest).decode("ascii").rstrip("=")
    return f"SHA256:{value}"


class _ForwardServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    transport: Any
    remote_host: str
    remote_port: int


class _ForwardHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        server: _ForwardServer = self.server  # type: ignore[assignment]
        try:
            channel = server.transport.open_channel(
                "direct-tcpip",
                (server.remote_host, server.remote_port),
                self.request.getpeername(),
            )
        except Exception:
            return

        if channel is None:
            return

        try:
            while True:
                readable, _, _ = select.select([self.request, channel], [], [], 1.0)
                if self.request in readable:
                    data = self.request.recv(65536)
                    if not data:
                        break
                    channel.sendall(data)
                if channel in readable:
                    data = channel.recv(65536)
                    if not data:
                        break
                    self.request.sendall(data)
        except (OSError, EOFError):
            pass
        finally:
            channel.close()


class TunnelController(QObject):
    connected = pyqtSignal(str)
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    host_key_confirmation = pyqtSignal(str, str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._server: _ForwardServer | None = None
        self._transport: Any | None = None
        self._stop_event = threading.Event()
        self._host_key_event = threading.Event()
        self._host_key_accepted = False

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def start(self, config: TunnelConfig) -> None:
        if self.is_running:
            self.error.emit("已经有一个连接正在运行。")
            return

        self._stop_event.clear()
        self._host_key_event.clear()
        self._host_key_accepted = False
        self._thread = threading.Thread(
            target=self._run,
            args=(config,),
            name="ccr-ssh-tunnel",
            daemon=True,
        )
        self._thread.start()

    def answer_host_key(self, accepted: bool) -> None:
        self._host_key_accepted = accepted
        self._host_key_event.set()

    def stop(self) -> None:
        self._stop_event.set()
        self._host_key_event.set()
        with self._lock:
            server = self._server
            transport = self._transport

        if server is not None:
            server.shutdown()
        if transport is not None:
            transport.close()

    def close(self, timeout: float = 3.0) -> None:
        self.stop()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def _run(self, config: TunnelConfig) -> None:
        if PARAMIKO_IMPORT_ERROR is not None:
            self.error.emit("缺少 paramiko，请先执行：python -m pip install -r requirements.txt")
            self.disconnected.emit()
            return

        transport = None
        server = None
        try:
            sock = socket.create_connection((config.host, config.ssh_port), timeout=12)
            transport = paramiko.Transport(sock)
            with self._lock:
                self._transport = transport

            transport.start_client(timeout=15)
            remote_key = transport.get_remote_server_key()
            self._verify_host_key(config, remote_key)
            if self._stop_event.is_set():
                return

            transport.auth_password(config.username, config.password, fallback=True)
            if not transport.is_authenticated():
                raise RuntimeError("SSH 用户名或密码不正确。")

            server = _ForwardServer(("127.0.0.1", config.local_port), _ForwardHandler)
            server.transport = transport
            server.remote_host = config.remote_host
            server.remote_port = config.remote_port
            with self._lock:
                self._server = server

            self.connected.emit(config.local_url)
            server.serve_forever(poll_interval=0.2)
        except Exception as exc:
            if not self._stop_event.is_set():
                self.error.emit(self._friendly_error(exc, config))
        finally:
            if server is not None:
                server.server_close()
            if transport is not None:
                transport.close()
            with self._lock:
                self._server = None
                self._transport = None
            self.disconnected.emit()

    def _verify_host_key(self, config: TunnelConfig, remote_key: Any) -> None:
        system_known_hosts_path = Path.home() / ".ssh" / "known_hosts"
        app_known_hosts_path = Path.home() / ".ccrAdmin" / "known_hosts"
        system_keys = paramiko.HostKeys()
        app_keys = paramiko.HostKeys()
        if system_known_hosts_path.exists():
            system_keys.load(str(system_known_hosts_path))
        if app_known_hosts_path.exists():
            app_keys.load(str(app_known_hosts_path))

        name = host_key_name(config.host, config.ssh_port)
        known = app_keys.lookup(name) or system_keys.lookup(name)
        key_type = remote_key.get_name()
        fingerprint = sha256_fingerprint(remote_key)

        if known is not None and key_type in known:
            if known[key_type] != remote_key:
                raise RuntimeError(
                    "SSH 主机密钥与已保存的记录不一致，已拒绝连接。"
                    f"\n服务器：{name}\n收到的指纹：{fingerprint}"
                )
            return

        self._host_key_event.clear()
        self._host_key_accepted = False
        self.host_key_confirmation.emit(name, key_type, fingerprint)

        while not self._host_key_event.wait(timeout=0.2):
            if self._stop_event.is_set():
                raise RuntimeError("连接已取消。")

        if not self._host_key_accepted or self._stop_event.is_set():
            raise RuntimeError("未接受 SSH 主机密钥，连接已取消。")

        app_known_hosts_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        app_keys.add(name, key_type, remote_key)
        app_keys.save(str(app_known_hosts_path))

    @staticmethod
    def _friendly_error(exc: Exception, config: TunnelConfig) -> str:
        if paramiko is not None:
            if isinstance(exc, paramiko.AuthenticationException):
                return "SSH 认证失败，请检查用户名和密码。"
            if isinstance(exc, paramiko.SSHException):
                return f"SSH 连接失败：{exc}"
        if isinstance(exc, socket.gaierror):
            return "无法解析服务器地址，请检查 IP 或主机名。"
        if isinstance(exc, (TimeoutError, socket.timeout)):
            return "连接服务器超时，请检查网络和 SSH 端口。"
        if isinstance(exc, OSError) and getattr(exc, "errno", None) in {
            errno.EADDRINUSE,
            10048,  # Windows WSAEADDRINUSE
        }:
            return f"本地端口 {config.local_port} 已被占用，请关闭占用程序或更换端口。"
        return str(exc) or exc.__class__.__name__
