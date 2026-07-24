from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSettings


@dataclass(frozen=True, slots=True)
class SavedConnection:
    """Non-sensitive connection fields that may be persisted."""

    host: str
    ssh_port: int
    username: str
    ccr_port: int
    local_port: int


class ConnectionSettings:
    """Store connection metadata while deliberately excluding passwords."""

    PREFIX = "connection"

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings or QSettings()

    @property
    def remember_enabled(self) -> bool:
        return self._settings.value(
            f"{self.PREFIX}/remember",
            True,
            type=bool,
        )

    @property
    def has_saved_connection(self) -> bool:
        return self.load() is not None

    def load(self) -> SavedConnection | None:
        if not self.remember_enabled:
            return None

        host = str(self._settings.value(f"{self.PREFIX}/host", "")).strip()
        username = str(self._settings.value(f"{self.PREFIX}/username", "")).strip()
        try:
            ssh_port = int(self._settings.value(f"{self.PREFIX}/ssh_port", 0))
            ccr_port = int(self._settings.value(f"{self.PREFIX}/ccr_port", 0))
            local_port = int(self._settings.value(f"{self.PREFIX}/local_port", 0))
        except (TypeError, ValueError):
            return None

        ports = (ssh_port, ccr_port, local_port)
        if not host or not username or not all(1 <= port <= 65535 for port in ports):
            return None

        return SavedConnection(
            host=host,
            ssh_port=ssh_port,
            username=username,
            ccr_port=ccr_port,
            local_port=local_port,
        )

    def save(self, connection: SavedConnection) -> None:
        values = {
            "remember": True,
            "host": connection.host,
            "ssh_port": connection.ssh_port,
            "username": connection.username,
            "ccr_port": connection.ccr_port,
            "local_port": connection.local_port,
        }
        for key, value in values.items():
            self._settings.setValue(f"{self.PREFIX}/{key}", value)
        self._settings.sync()

    def set_remember_enabled(self, enabled: bool) -> None:
        self._settings.setValue(f"{self.PREFIX}/remember", enabled)
        if not enabled:
            self._remove_connection_values()
        self._settings.sync()

    def clear(self) -> None:
        self.set_remember_enabled(False)

    def _remove_connection_values(self) -> None:
        for key in ("host", "ssh_port", "username", "ccr_port", "local_port"):
            self._settings.remove(f"{self.PREFIX}/{key}")
