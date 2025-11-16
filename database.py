"""
MongoDB Database Connection
"""
from pymongo import MongoClient
from datetime import datetime
import os

# Try cloud MongoDB first, fallback to local
try:
    import certifi
    MONGO_URI = "mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000, tlsCAFile=certifi.where())
    client.server_info()  # Test connection
    print("✅ Connected to MongoDB Atlas")
except:
    # Fallback to local MongoDB
    MONGO_URI = "mongodb://localhost:27017/"
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    print("✅ Connected to local MongoDB")

DB_NAME = "astrology_ai"
db = client[DB_NAME]

users_collection = db["users"]
chats_collection = db["chats"]

# Create indexes on first use
def ensure_indexes():
    try:
        users_collection.create_index("email", unique=True)
        chats_collection.create_index("user_id")
    except:
        pass
