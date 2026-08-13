import unittest

import backend.app.models  # noqa: F401
from backend.app.core.database import Base


class ModelMetadataTests(unittest.TestCase):
    def test_expected_tables_are_registered(self):
        expected = {
            "admin_users",
            "attendance_daily",
            "attendance_adjustments",
            "attendance_events",
            "employees",
            "face_embeddings",
            "shifts",
        }
        self.assertEqual(set(Base.metadata.tables), expected)


if __name__ == "__main__":
    unittest.main()
