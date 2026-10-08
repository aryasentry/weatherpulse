"""Standard-library checks for the native launcher's real preflight behavior."""
import importlib.util
import os
import socket
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher = None
        if (ROOT / "run.py").is_file():
            spec = importlib.util.spec_from_file_location("weather_launcher", ROOT / "run.py")
            cls.launcher = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.launcher)

    def setUp(self):
        self.assertIsNotNone(self.launcher, "The native launcher must exist")

    def test_supported_python_range_rejects_other_versions(self):
        for version in [(3, 10), (3, 14), (2, 7)]:
            with self.assertRaisesRegex(self.launcher.LaunchError, "3.11"):
                self.launcher.check_python(version)
        for version in [(3, 11), (3, 12), (3, 13)]:
            self.launcher.check_python(version)

    def test_missing_frontend_explains_rebuild_or_bundle_recovery(self):
        with tempfile.TemporaryDirectory(prefix="weather bundle with spaces ") as folder:
            with self.assertRaisesRegex(self.launcher.LaunchError, "frontend/out/index.html"):
                self.launcher.check_bundle(Path(folder))

    def test_bundle_is_resolved_from_given_root_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix="weather bundle with spaces ") as folder:
            root = Path(folder)
            for relative in self.launcher.REQUIRED_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("bundled")
            self.launcher.check_bundle(root)
            self.assertEqual(self.launcher.venv_python(root, windows=True), root / ".venv" / "Scripts" / "python.exe")
            self.assertEqual(self.launcher.venv_python(root, windows=False), root / ".venv" / "bin" / "python")

    def test_busy_port_is_actionable_and_free_port_is_accepted(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            port = occupied.getsockname()[1]
            with self.assertRaisesRegex(self.launcher.LaunchError, "--port"):
                self.launcher.check_port(port)
        self.launcher.check_port(port)

    def test_automatic_port_selection_skips_an_actual_listener(self):
        with socket.socket() as occupied, socket.socket() as available:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            available.bind(("127.0.0.1", 0))
            busy_port = occupied.getsockname()[1]
            free_port = available.getsockname()[1]
            available.close()
            self.assertEqual(self.launcher.pick_free_port((busy_port, free_port)), free_port)

    def test_automatic_port_selection_exhaustion_is_actionable(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            with self.assertRaisesRegex(self.launcher.LaunchError, "--port"):
                self.launcher.pick_free_port((occupied.getsockname()[1],))

    @unittest.skipIf(os.name == "nt", "POSIX TCP restart behavior")
    def test_recently_closed_server_does_not_false_report_busy(self):
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port)) as client:
                accepted, _ = server.accept()
                accepted.close()  # Server-side active close creates TIME_WAIT.
                self.assertEqual(client.recv(1), b"")
        self.launcher.check_port(port)


if __name__ == "__main__":
    unittest.main()
