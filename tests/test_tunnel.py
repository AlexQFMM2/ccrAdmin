import unittest

from ccr_admin.tunnel import TunnelConfig, host_key_name


class TunnelHelpersTest(unittest.TestCase):
    def test_default_ssh_host_key_name(self) -> None:
        self.assertEqual(host_key_name("server.example.com", 22), "server.example.com")

    def test_nonstandard_ssh_host_key_name(self) -> None:
        self.assertEqual(host_key_name("example.com", 2222), "[example.com]:2222")

    def test_local_url(self) -> None:
        config = TunnelConfig(
            "server.example.com",
            22,
            "ssh-user",
            "one-time-secret",
            4567,
            local_port=18080,
        )
        self.assertEqual(config.local_url, "http://127.0.0.1:18080")


if __name__ == "__main__":
    unittest.main()
