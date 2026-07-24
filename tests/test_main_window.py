import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from ccr_admin.main_window import MainWindow


class MainWindowSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        settings_path = Path(self.temp_dir.name) / "ccrAdmin.ini"
        settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
        self.window = MainWindow(settings)

    def tearDown(self) -> None:
        self.window.close()
        self.temp_dir.cleanup()

    def test_first_run_has_no_server_identity_defaults(self) -> None:
        self.assertEqual(self.window.host_edit.text(), "")
        self.assertEqual(self.window.username_edit.text(), "")
        self.assertEqual(self.window.ccr_port_edit.value(), 0)
        self.assertEqual(self.window.password_edit.text(), "")

    def test_password_is_cleared_as_soon_as_connection_starts(self) -> None:
        start = Mock()
        self.window._controller.start = start
        self.window.host_edit.setText("server.example.com")
        self.window.username_edit.setText("admin")
        self.window.password_edit.setText("one-time-secret")
        self.window.ccr_port_edit.setValue(4567)

        self.window._connect()

        config = start.call_args.args[0]
        self.assertEqual(config.remote_port, 4567)
        self.assertEqual(config.password, "one-time-secret")
        self.assertEqual(self.window.password_edit.text(), "")
        self.assertFalse(self.window.show_password_checkbox.isChecked())


if __name__ == "__main__":
    unittest.main()
