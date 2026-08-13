import unittest

from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class PasswordTests(unittest.TestCase):
    def test_hash_and_verify_password(self):
        password_hash = hash_password("mat-khau-demo")
        self.assertNotEqual(password_hash, "mat-khau-demo")
        self.assertTrue(verify_password("mat-khau-demo", password_hash))
        self.assertFalse(verify_password("sai-mat-khau", password_hash))

    def test_access_token_round_trip(self):
        original_secret = settings.JWT_SECRET
        settings.JWT_SECRET = "unit-test-secret-at-least-32-bytes-long"
        try:
            token = create_access_token("42")
            self.assertEqual(decode_access_token(token)["sub"], "42")
        finally:
            settings.JWT_SECRET = original_secret


if __name__ == "__main__":
    unittest.main()
