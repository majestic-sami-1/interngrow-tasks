"""
Unit tests for FinPulse AI authentication and security layer.
"""

import unittest
import os
import sys

# Ensure root directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.auth import hash_password, verify_password, generate_salt, validate_registration_inputs

class TestAuthSecurity(unittest.TestCase):
    def test_salt_generation(self):
        salt1 = generate_salt()
        salt2 = generate_salt()
        self.assertNotEqual(salt1, salt2)
        self.assertEqual(len(salt1), 32)  # 16 bytes in hex = 32 chars

    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        salt = generate_salt()
        hashed = hash_password(password, salt)
        
        # Valid verification
        self.assertTrue(verify_password(password, salt, hashed))
        
        # Invalid verification
        self.assertFalse(verify_password("WrongPassword", salt, hashed))
        self.assertFalse(verify_password(password, generate_salt(), hashed))

    def test_input_validation(self):
        # Valid inputs
        valid, _ = validate_registration_inputs("johndoe", "john@example.com", "secretpass")
        self.assertTrue(valid)

        # Invalid username
        valid, msg = validate_registration_inputs("jo", "john@example.com", "secretpass")
        self.assertFalse(valid)
        self.assertIn("at least 3 characters", msg)

        # Invalid email
        valid, msg = validate_registration_inputs("johndoe", "not-an-email", "secretpass")
        self.assertFalse(valid)
        self.assertIn("valid email", msg)

        # Short password
        valid, msg = validate_registration_inputs("johndoe", "john@example.com", "123")
        self.assertFalse(valid)
        self.assertIn("at least 6 characters", msg)

if __name__ == "__main__":
    unittest.main()
