# database.py
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient, AgnosticCollection, AgnosticDatabase
from emelia.config import mangodb  # Import mangodb from config

class Database:
    def __init__(self, uri=mangodb):
        # Synchronous MongoDB client (pymongo)
        self.client = MongoClient(uri)
        self.db = self.client["anime_bot"]
        self.users = self.db["users"]
        self.watchlist = self.db["watchlist"]
        self.notifications = self.db["notifications"]

        # Asynchronous MongoDB client (motor)
        self._mgclient: AgnosticClient = AsyncIOMotorClient(uri)
        self._database: AgnosticDatabase = self._mgclient["Emilia"]

    # Synchronous methods (pymongo)
    def add_user(self, user_id, username):
        """Add a new user to the database."""
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "username": username, "favorite_genres": ""}},
            upsert=True
        )

    def update_genres(self, user_id, genres):
        """Update user's favorite genres."""
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"favorite_genres": genres}}
        )

    def get_user(self, user_id):
        """Retrieve user data by user_id."""
        return self.users.find_one({"user_id": user_id})

    def add_to_watchlist(self, user_id, title, url, media_type):
        """Add an anime or manga to the user's watchlist."""
        self.watchlist.update_one(
            {"user_id": user_id, "title": title, "type": media_type},
            {"$set": {"user_id": user_id, "title": title, "url": url, "type": media_type}},
            upsert=True
        )

    def get_watchlist(self, user_id, media_type=None):
        """Retrieve user's watchlist (optionally filter by anime or manga)."""
        query = {"user_id": user_id}
        if media_type:
            query["type"] = media_type
        return list(self.watchlist.find(query, {"title": 1, "url": 1, "type": 1, "_id": 0}))

    def remove_from_watchlist(self, user_id, title, media_type):
        """Remove an anime or manga from the user's watchlist."""
        self.watchlist.delete_one({"user_id": user_id, "title": title, "type": media_type})

    def set_notification(self, user_id, enabled):
        """Enable or disable episode notifications for a user."""
        self.notifications.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "enabled": enabled}},
            upsert=True
        )

    def get_notification(self, user_id):
        """Check if notifications are enabled for a user."""
        notification = self.notifications.find_one({"user_id": user_id})
        return notification["enabled"] if notification else False

    def get_users_with_notifications(self):
        """Get all users with notifications enabled."""
        return list(self.notifications.find({"enabled": True}, {"user_id": 1, "_id": 0}))

    # Asynchronous method (motor)
    async def get_collection(self, name: str) -> AgnosticCollection:
        """Create or get collection from Emilia database (async)."""
        return self._database[name]

# Export for compatibility
__all__ = ["Database", "get_collection"]
