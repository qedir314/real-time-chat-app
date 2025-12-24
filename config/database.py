import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "realtime_chat")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
messages_collection = db["messages"]
users_collection = db["users"]
rooms_collection = db["rooms"]

# Create index for efficient queries
messages_collection.create_index([("room_id", 1), ("timestamp", -1)])
users_collection.create_index([("email", 1)], unique=True)
users_collection.create_index([("username", 1)], unique=True)
rooms_collection.create_index([("room_id", 1)], unique=True)
rooms_collection.create_index([("invite_code", 1)], unique=True)
