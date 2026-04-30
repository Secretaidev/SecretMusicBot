"""MongoDB database layer — advanced edition.

Supports: sudo users, auth users, group settings, user favourites,
play history, playlists, blocked users, and global stats.
Gracefully falls back to in-memory storage when MongoDB is unavailable.
"""

from typing import List, Optional, Dict
from utils.logger import get_logger

log = get_logger("Database")

_motor_available = True
try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    _motor_available = False
    log.warning("motor not installed — using in-memory fallback")

import config


class Database:
    def __init__(self):
        self._connected = False
        self._memory = {
            "sudoers": list(config.SUDO_USERS),
            "auth_users": {},
            "groups": {},
            "favourites": {},
            "playlists": {},
            "history": {},
            "blocked": [],
            "stats": {"total_plays": 0, "total_users": 0},
            "settings": {},
        }

        if _motor_available and config.MONGO_DB_URI:
            try:
                self.client = AsyncIOMotorClient(config.MONGO_DB_URI)
                self.db = self.client["SecretMusicBot"]
                self.sudoers_col = self.db["sudoers"]
                self.auth_col = self.db["auth_users"]
                self.groups_col = self.db["groups"]
                self.favourites_col = self.db["favourites"]
                self.playlists_col = self.db["playlists"]
                self.history_col = self.db["play_history"]
                self.blocked_col = self.db["blocked_users"]
                self.stats_col = self.db["global_stats"]
                self.settings_col = self.db["chat_settings"]
                self._connected = True
                log.info("MongoDB connected successfully.")
            except Exception as e:
                log.error(f"MongoDB connection failed: {e}")
                self._connected = False
        else:
            self._connected = False
            log.info("Running with in-memory database.")

    # ─── Sudo Users ──────────────────────────────────────────
    async def get_sudoers(self) -> List[int]:
        if not self._connected:
            return self._memory["sudoers"]
        doc = await self.sudoers_col.find_one({"_id": "sudoers"})
        if not doc:
            return list(config.SUDO_USERS)
        return doc.get("users", list(config.SUDO_USERS))

    async def add_sudo(self, user_id: int):
        if not self._connected:
            if user_id not in self._memory["sudoers"]:
                self._memory["sudoers"].append(user_id)
            return
        sudoers = await self.get_sudoers()
        if user_id not in sudoers:
            sudoers.append(user_id)
            await self.sudoers_col.update_one(
                {"_id": "sudoers"}, {"$set": {"users": sudoers}}, upsert=True
            )

    async def remove_sudo(self, user_id: int):
        if not self._connected:
            if user_id in self._memory["sudoers"]:
                self._memory["sudoers"].remove(user_id)
            return
        sudoers = await self.get_sudoers()
        if user_id in sudoers:
            sudoers.remove(user_id)
            await self.sudoers_col.update_one(
                {"_id": "sudoers"}, {"$set": {"users": sudoers}}, upsert=True
            )

    # ─── Auth Users (Group specific) ─────────────────────────
    async def is_auth_user(self, chat_id: int, user_id: int) -> bool:
        if not self._connected:
            key = f"{chat_id}:{user_id}"
            return key in self._memory["auth_users"]
        doc = await self.auth_col.find_one({"chat_id": chat_id, "user_id": user_id})
        return bool(doc)

    async def add_auth_user(self, chat_id: int, user_id: int):
        if not self._connected:
            self._memory["auth_users"][f"{chat_id}:{user_id}"] = True
            return
        await self.auth_col.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"chat_id": chat_id, "user_id": user_id}},
            upsert=True,
        )

    async def remove_auth_user(self, chat_id: int, user_id: int):
        if not self._connected:
            self._memory["auth_users"].pop(f"{chat_id}:{user_id}", None)
            return
        await self.auth_col.delete_one({"chat_id": chat_id, "user_id": user_id})

    async def get_auth_users(self, chat_id: int) -> List[int]:
        if not self._connected:
            return [
                int(k.split(":")[1])
                for k in self._memory["auth_users"]
                if k.startswith(f"{chat_id}:")
            ]
        docs = self.auth_col.find({"chat_id": chat_id})
        return [doc["user_id"] async for doc in docs]

    # ─── User Favourites ─────────────────────────────────────
    async def add_favourite(self, user_id: int, track_data: dict):
        if not self._connected:
            if user_id not in self._memory["favourites"]:
                self._memory["favourites"][user_id] = []
            # Prevent duplicates
            for t in self._memory["favourites"][user_id]:
                if t.get("id") == track_data.get("id"):
                    return
            self._memory["favourites"][user_id].append(track_data)
            return
        await self.favourites_col.update_one(
            {"user_id": user_id, "track_id": track_data.get("id")},
            {"$set": {"user_id": user_id, "track_id": track_data.get("id"), "data": track_data}},
            upsert=True,
        )

    async def remove_favourite(self, user_id: int, track_id: str):
        if not self._connected:
            if user_id in self._memory["favourites"]:
                self._memory["favourites"][user_id] = [
                    t for t in self._memory["favourites"][user_id] if t.get("id") != track_id
                ]
            return
        await self.favourites_col.delete_one({"user_id": user_id, "track_id": track_id})

    async def get_favourites(self, user_id: int) -> List[dict]:
        if not self._connected:
            return self._memory["favourites"].get(user_id, [])
        docs = self.favourites_col.find({"user_id": user_id}).sort("_id", -1).limit(50)
        return [doc["data"] async for doc in docs]

    # ─── Playlists ────────────────────────────────────────────
    async def create_playlist(self, user_id: int, name: str) -> bool:
        if not self._connected:
            key = f"{user_id}:{name}"
            if key in self._memory["playlists"]:
                return False
            self._memory["playlists"][key] = {"name": name, "tracks": []}
            return True
        existing = await self.playlists_col.find_one({"user_id": user_id, "name": name})
        if existing:
            return False
        await self.playlists_col.insert_one({"user_id": user_id, "name": name, "tracks": []})
        return True

    async def delete_playlist(self, user_id: int, name: str) -> bool:
        if not self._connected:
            key = f"{user_id}:{name}"
            if key in self._memory["playlists"]:
                del self._memory["playlists"][key]
                return True
            return False
        result = await self.playlists_col.delete_one({"user_id": user_id, "name": name})
        return result.deleted_count > 0

    async def add_to_playlist(self, user_id: int, name: str, track_data: dict) -> bool:
        if not self._connected:
            key = f"{user_id}:{name}"
            if key not in self._memory["playlists"]:
                return False
            self._memory["playlists"][key]["tracks"].append(track_data)
            return True
        result = await self.playlists_col.update_one(
            {"user_id": user_id, "name": name},
            {"$push": {"tracks": track_data}},
        )
        return result.modified_count > 0

    async def get_playlist(self, user_id: int, name: str) -> Optional[dict]:
        if not self._connected:
            return self._memory["playlists"].get(f"{user_id}:{name}")
        return await self.playlists_col.find_one({"user_id": user_id, "name": name})

    async def get_playlists(self, user_id: int) -> List[dict]:
        if not self._connected:
            return [
                v for k, v in self._memory["playlists"].items()
                if k.startswith(f"{user_id}:")
            ]
        docs = self.playlists_col.find({"user_id": user_id})
        return [doc async for doc in docs]

    # ─── Play History ─────────────────────────────────────────
    async def add_to_history(self, user_id: int, chat_id: int, track_data: dict):
        if not self._connected:
            key = f"{user_id}"
            if key not in self._memory["history"]:
                self._memory["history"][key] = []
            self._memory["history"][key].append(track_data)
            if len(self._memory["history"][key]) > 50:
                self._memory["history"][key] = self._memory["history"][key][-50:]
            return
        import time
        await self.history_col.insert_one({
            "user_id": user_id,
            "chat_id": chat_id,
            "data": track_data,
            "timestamp": time.time(),
        })

    async def get_history(self, user_id: int, limit: int = 20) -> List[dict]:
        if not self._connected:
            return self._memory["history"].get(str(user_id), [])[-limit:]
        docs = self.history_col.find({"user_id": user_id}).sort("_id", -1).limit(limit)
        return [doc["data"] async for doc in docs]

    # ─── Blocked Users ────────────────────────────────────────
    async def is_blocked(self, user_id: int) -> bool:
        if not self._connected:
            return user_id in self._memory["blocked"]
        doc = await self.blocked_col.find_one({"user_id": user_id})
        return bool(doc)

    async def block_user(self, user_id: int):
        if not self._connected:
            if user_id not in self._memory["blocked"]:
                self._memory["blocked"].append(user_id)
            return
        await self.blocked_col.update_one(
            {"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
        )

    async def unblock_user(self, user_id: int):
        if not self._connected:
            if user_id in self._memory["blocked"]:
                self._memory["blocked"].remove(user_id)
            return
        await self.blocked_col.delete_one({"user_id": user_id})

    # ─── Chat Settings ────────────────────────────────────────
    async def get_chat_settings(self, chat_id: int) -> dict:
        defaults = {
            "quality": config.DEFAULT_QUALITY,
            "autoplay": False,
            "vote_skip": False,
            "vote_skip_threshold": 3,
            "auto_leave": True,
            "announcements": True,
            "language": "en",
        }
        if not self._connected:
            return self._memory["settings"].get(chat_id, defaults)
        doc = await self.settings_col.find_one({"chat_id": chat_id})
        if doc:
            defaults.update({k: v for k, v in doc.items() if k != "_id" and k != "chat_id"})
        return defaults

    async def update_chat_settings(self, chat_id: int, **kwargs):
        if not self._connected:
            if chat_id not in self._memory["settings"]:
                self._memory["settings"][chat_id] = {}
            self._memory["settings"][chat_id].update(kwargs)
            return
        await self.settings_col.update_one(
            {"chat_id": chat_id},
            {"$set": {**kwargs, "chat_id": chat_id}},
            upsert=True,
        )

    # ─── Groups ───────────────────────────────────────────────
    async def add_group(self, chat_id: int):
        if not self._connected:
            self._memory["groups"][chat_id] = True
            return
        await self.groups_col.update_one(
            {"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True
        )

    async def get_group_count(self) -> int:
        if not self._connected:
            return len(self._memory["groups"])
        return await self.groups_col.count_documents({})

    # ─── Global Stats ─────────────────────────────────────────
    async def increment_plays(self):
        if not self._connected:
            self._memory["stats"]["total_plays"] += 1
            return
        await self.stats_col.update_one(
            {"_id": "global"},
            {"$inc": {"total_plays": 1}},
            upsert=True,
        )

    async def get_global_stats(self) -> dict:
        if not self._connected:
            return self._memory["stats"]
        doc = await self.stats_col.find_one({"_id": "global"})
        return doc if doc else {"total_plays": 0}


db = Database()
