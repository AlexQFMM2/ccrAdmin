import tempfile
import unittest
from pathlib import Path

from PyQt6.QtCore import QSettings

from ccr_admin.settings import ConnectionSettings, SavedConnection


class ConnectionSettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.temp_dir.name) / "ccrAdmin.ini"
        backend = QSettings(str(self.settings_path), QSettings.Format.IniFormat)
        self.settings = ConnectionSettings(backend)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_empty_settings_have_no_server_defaults(self) -> None:
        self.assertTrue(self.settings.remember_enabled)
        self.assertIsNone(self.settings.load())

    def test_saves_only_non_sensitive_connection_fields(self) -> None:
        connection = SavedConnection(
            host="server.example.com",
            ssh_port=22,
            username="admin",
            ccr_port=4567,
            local_port=13458,
        )
        self.settings.save(connection)

        self.assertEqual(self.settings.load(), connection)
        stored_text = self.settings_path.read_text(encoding="utf-8")
        self.assertNotIn("password", stored_text.lower())
        self.assertNotIn("secret", stored_text.lower())

    def test_disabling_remember_removes_saved_connection(self) -> None:
        self.settings.save(
            SavedConnection("server.example.com", 22, "admin", 4567, 13458)
        )

        self.settings.set_remember_enabled(False)

        self.assertFalse(self.settings.remember_enabled)
        self.assertIsNone(self.settings.load())


if __name__ == "__main__":
    unittest.main()
