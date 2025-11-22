"""
Validate environment and token generation
"""
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
print(f"✓ JWT_SECRET loaded: {JWT_SECRET[:20]}..." if JWT_SECRET else "✗ JWT_SECRET missing")

# Test token creation
try:
    payload = {
        "user_id": "test123",
        "email": "test@test.com",
        "is_admin": False,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    print(f"✓ Token created: {token[:50]}...")
    
    # Test token decode
    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    print(f"✓ Token decoded: {decoded}")
except Exception as e:
    print(f"✗ Token error: {e}")
