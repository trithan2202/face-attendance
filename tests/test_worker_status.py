import tempfile
import unittest
from pathlib import Path

from backend.app.services.worker_status import WorkerStatusService


class WorkerStatusServiceTests(unittest.TestCase):
    def test_missing_status_file_is_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            service = WorkerStatusService(Path(directory) / "status.json")
            self.assertFalse(service.read()["online"])

    def test_write_then_read_is_online(self):
        with tempfile.TemporaryDirectory() as directory:
            service = WorkerStatusService(Path(directory) / "status.json")
            service.write("READY", True, True, "ready")
            result = service.read()
            self.assertTrue(result["online"])
            self.assertEqual(result["state"], "READY")

    def test_invalid_status_file_is_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text("not-json", encoding="utf-8")
            self.assertFalse(WorkerStatusService(path).read()["online"])


if __name__ == "__main__":
    unittest.main()
