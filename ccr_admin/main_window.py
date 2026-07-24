from __future__ import annotations

from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtGui import QCloseEvent, QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .settings import ConnectionSettings, SavedConnection
from .tunnel import TunnelConfig, TunnelController


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None) -> None:
        super().__init__()
        self.setWindowTitle("myModels CCR 管理工具")
        self.setMinimumSize(540, 570)
        self.resize(580, 610)
        self._current_url = ""
        self._closing = False
        self._connection_settings = ConnectionSettings(settings)

        self._controller = TunnelController(self)
        self._controller.connected.connect(self._on_connected)
        self._controller.disconnected.connect(self._on_disconnected)
        self._controller.error.connect(self._on_error)
        self._controller.host_key_confirmation.connect(self._confirm_host_key)

        self._build_ui()
        self._load_saved_connection()
        self._set_status("未连接", "#6b7280")

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("myModels CCR 管理工具")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        description = QLabel("通过 SSH 安全隧道打开 CCR 管理界面。密码只用于本次连接，不会保存。")
        description.setWordWrap(True)
        description.setStyleSheet("color: #4b5563;")
        layout.addWidget(description)

        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form = QFormLayout(form_frame)
        form.setContentsMargins(18, 16, 18, 16)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("服务器 IP 或主机名")
        form.addRow("服务器：", self.host_edit)

        self.ssh_port_edit = QSpinBox()
        self.ssh_port_edit.setRange(1, 65535)
        self.ssh_port_edit.setValue(22)
        form.addRow("SSH 端口：", self.ssh_port_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("SSH 用户名")
        form.addRow("用户名：", self.username_edit)

        password_row = QWidget()
        password_layout = QHBoxLayout(password_row)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("服务器 SSH 密码")
        self.password_edit.returnPressed.connect(self._connect)
        self.show_password_checkbox = QCheckBox("显示")
        self.show_password_checkbox.toggled.connect(self._toggle_password)
        password_layout.addWidget(self.password_edit, 1)
        password_layout.addWidget(self.show_password_checkbox)
        form.addRow("密码：", password_row)

        self.ccr_port_edit = QSpinBox()
        self.ccr_port_edit.setRange(0, 65535)
        self.ccr_port_edit.setSpecialValueText("请输入")
        self.ccr_port_edit.setValue(0)
        form.addRow("服务器 CCR 端口：", self.ccr_port_edit)

        self.local_port_edit = QSpinBox()
        self.local_port_edit.setRange(1024, 65535)
        self.local_port_edit.setValue(13458)
        form.addRow("本地端口：", self.local_port_edit)

        remember_row = QWidget()
        remember_layout = QHBoxLayout(remember_row)
        remember_layout.setContentsMargins(0, 0, 0, 0)
        remember_layout.setSpacing(8)
        self.remember_checkbox = QCheckBox("记住连接信息（不含密码）")
        self.remember_checkbox.setChecked(self._connection_settings.remember_enabled)
        self.remember_checkbox.toggled.connect(self._on_remember_toggled)
        self.clear_saved_button = QPushButton("清除记录")
        self.clear_saved_button.clicked.connect(self._clear_saved_connection)
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch(1)
        remember_layout.addWidget(self.clear_saved_button)
        form.addRow("", remember_row)
        layout.addWidget(form_frame)

        status_row = QHBoxLayout()
        status_label = QLabel("状态：")
        self.status_value = QLabel()
        status_row.addWidget(status_label)
        status_row.addWidget(self.status_value)
        status_row.addStretch(1)
        layout.addLayout(status_row)

        button_row = QHBoxLayout()
        self.connect_button = QPushButton("连接服务器")
        self.connect_button.clicked.connect(self._connect)
        self.disconnect_button = QPushButton("断开连接")
        self.disconnect_button.clicked.connect(self._disconnect)
        self.disconnect_button.setEnabled(False)
        self.open_button = QPushButton("打开 CCR 管理界面")
        self.open_button.clicked.connect(self._open_admin)
        self.open_button.setEnabled(False)
        button_row.addWidget(self.connect_button)
        button_row.addWidget(self.disconnect_button)
        button_row.addStretch(1)
        button_row.addWidget(self.open_button)
        layout.addLayout(button_row)

        hint = QLabel(
            "SSH 密码每次连接都必须重新输入。关闭此应用会自动断开隧道，"
            "已打开的管理页面随后将无法访问。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6b7280; font-size: 12px;")
        layout.addWidget(hint)
        layout.addStretch(1)

        self.setCentralWidget(root)

    def _connect(self) -> None:
        host = self.host_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        ccr_port = self.ccr_port_edit.value()
        if not host or not username or not password or ccr_port == 0:
            QMessageBox.warning(
                self,
                "信息不完整",
                "请填写服务器、用户名、密码和服务器 CCR 端口。",
            )
            return

        config = TunnelConfig(
            host=host,
            ssh_port=self.ssh_port_edit.value(),
            username=username,
            password=password,
            local_port=self.local_port_edit.value(),
            remote_port=ccr_port,
        )
        self.password_edit.clear()
        self.show_password_checkbox.setChecked(False)
        self._set_connecting_ui(True)
        self._set_status("正在连接…", "#d97706")
        self._controller.start(config)

    def _disconnect(self) -> None:
        self.disconnect_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self._set_status("正在断开…", "#d97706")
        self._controller.stop()

    def _on_connected(self, url: str) -> None:
        self._current_url = url
        if self.remember_checkbox.isChecked():
            self._connection_settings.save(self._current_saved_connection())
            self.clear_saved_button.setEnabled(True)
        self.open_button.setEnabled(True)
        self.disconnect_button.setEnabled(True)
        self._set_status(f"已连接 · {url}", "#15803d")

    def _on_disconnected(self) -> None:
        self._current_url = ""
        self.password_edit.clear()
        self.show_password_checkbox.setChecked(False)
        if not self._closing:
            self._set_connecting_ui(False)
            self._set_status("未连接", "#6b7280")

    def _on_error(self, message: str) -> None:
        if not self._closing:
            QMessageBox.critical(self, "连接失败", message)

    def _confirm_host_key(self, server: str, key_type: str, fingerprint: str) -> None:
        message = (
            "这是首次连接该服务器。请先向管理员核对以下 SSH 主机密钥指纹：\n\n"
            f"服务器：{server}\n"
            f"类型：{key_type}\n"
            f"指纹：{fingerprint}\n\n"
            "确认指纹无误后，是否信任并继续？"
        )
        result = QMessageBox.question(
            self,
            "确认 SSH 主机密钥",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        self._controller.answer_host_key(result == QMessageBox.StandardButton.Yes)

    def _open_admin(self) -> None:
        if self._current_url:
            QDesktopServices.openUrl(QUrl(self._current_url))

    def _toggle_password(self, visible: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)

    def _load_saved_connection(self) -> None:
        connection = self._connection_settings.load()
        if connection is not None:
            self.host_edit.setText(connection.host)
            self.ssh_port_edit.setValue(connection.ssh_port)
            self.username_edit.setText(connection.username)
            self.ccr_port_edit.setValue(connection.ccr_port)
            self.local_port_edit.setValue(connection.local_port)
        self.clear_saved_button.setEnabled(connection is not None)

    def _current_saved_connection(self) -> SavedConnection:
        return SavedConnection(
            host=self.host_edit.text().strip(),
            ssh_port=self.ssh_port_edit.value(),
            username=self.username_edit.text().strip(),
            ccr_port=self.ccr_port_edit.value(),
            local_port=self.local_port_edit.value(),
        )

    def _on_remember_toggled(self, enabled: bool) -> None:
        self._connection_settings.set_remember_enabled(enabled)
        self.clear_saved_button.setEnabled(
            enabled and self._connection_settings.has_saved_connection
        )

    def _clear_saved_connection(self) -> None:
        self._connection_settings.clear()
        self.remember_checkbox.setChecked(False)
        self.clear_saved_button.setEnabled(False)
        if not self._controller.is_running:
            self.host_edit.clear()
            self.ssh_port_edit.setValue(22)
            self.username_edit.clear()
            self.password_edit.clear()
            self.show_password_checkbox.setChecked(False)
            self.ccr_port_edit.setValue(0)
            self.local_port_edit.setValue(13458)

    def _set_connecting_ui(self, connecting: bool) -> None:
        self.connect_button.setEnabled(not connecting)
        self.disconnect_button.setEnabled(connecting)
        self.open_button.setEnabled(False)
        for widget in (
            self.host_edit,
            self.ssh_port_edit,
            self.username_edit,
            self.password_edit,
            self.show_password_checkbox,
            self.ccr_port_edit,
            self.local_port_edit,
            self.remember_checkbox,
            self.clear_saved_button,
        ):
            widget.setEnabled(not connecting)

    def _set_status(self, text: str, color: str) -> None:
        self.status_value.setText(f"● {text}")
        self.status_value.setStyleSheet(f"color: {color}; font-weight: 600;")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API
        self._closing = True
        self._controller.close()
        event.accept()
