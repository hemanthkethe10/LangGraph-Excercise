import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_CHAT_HISTORY = os.getenv("MONGO_CHAT_HISTORY", "chat_history")
MONGO_SUBSCRIPTIONS = os.getenv("MONGO_SUBSCRIPTIONS", "subscriptions")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set in environment variables.")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
chat_history_collection = db[MONGO_CHAT_HISTORY]
subscriptions_collection = db[MONGO_SUBSCRIPTIONS]

def save_chat_message(user_id, role, content):
    chat_history_collection.update_one(
        {"user_id": user_id},
        {"$push": {"history": {"role": role, "content": content, "timestamp": datetime.utcnow()}}},
        upsert=True
    )

def serialize_history(history):
    for msg in history:
        if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
            msg['timestamp'] = msg['timestamp'].isoformat()
    return history

def load_chat_history(user_id):
    doc = chat_history_collection.find_one({"user_id": user_id})
    history = doc["history"] if doc and "history" in doc else []
    return serialize_history(history)

def save_state(user_id: str, state: dict):
    subscriptions_collection.update_one({"user_id": user_id}, {"$set": {"state": state}}, upsert=True)

def load_state(user_id: str) -> dict:
    doc = subscriptions_collection.find_one({"user_id": user_id})
    return doc["state"] if doc and "state" in doc else {}
