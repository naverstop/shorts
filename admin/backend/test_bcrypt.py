"""Test bcrypt functionality"""
from app.auth import get_password_hash, verify_password

print("Testing password hash...")
password = "test1234"
hash_value = get_password_hash(password)
print(f"Hash generated: {hash_value[:50]}...")
verified = verify_password(password, hash_value)
print(f"Verification result: {verified}")
print("Test completed successfully!" if verified else "Test failed!")
