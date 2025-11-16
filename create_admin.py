"""
Script to create initial admin user
"""
from database import users_collection, ensure_indexes
from auth import hash_password
from datetime import datetime

ensure_indexes()

admin_email = "admin@astrology.ai"
admin_password = "admin123"

try:
    existing = users_collection.find_one({"email": admin_email})
    if existing:
        print(f"Admin user already exists: {admin_email}")
    else:
        admin_user = {
            "email": admin_email,
            "password": hash_password(admin_password),
            "name": "Admin",
            "is_admin": True,
            "active": True,
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(admin_user)
        print(f"✅ Admin user created: {admin_email} / {admin_password}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Check your internet connection and MongoDB URI")
