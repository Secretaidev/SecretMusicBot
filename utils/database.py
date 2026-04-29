from motor.motor_asyncio import AsyncIOMotorClient
import config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(config.MONGO_DB_URI) if config.MONGO_DB_URI else None
        self.db = self.client["MusicBot"] if self.client else None
        self.sudoers = self.db["sudoers"] if self.db else None
        self.auth_users = self.db["auth_users"] if self.db else None
        self.groups = self.db["groups"] if self.db else None

    # --- Sudo Users ---
    async def get_sudoers(self) -> list:
        if not self.sudoers:
            return config.SUDO_USERS
        sudoers = await self.sudoers.find_one({"sudo": "sudoers"})
        if not sudoers:
            return config.SUDO_USERS
        return sudoers["users"]

    async def add_sudo(self, user_id: int):
        if not self.sudoers:
            return
        sudoers = await self.get_sudoers()
        if user_id not in sudoers:
            sudoers.append(user_id)
            await self.sudoers.update_one(
                {"sudo": "sudoers"}, {"$set": {"users": sudoers}}, upsert=True
            )

    async def remove_sudo(self, user_id: int):
        if not self.sudoers:
            return
        sudoers = await self.get_sudoers()
        if user_id in sudoers:
            sudoers.remove(user_id)
            await self.sudoers.update_one(
                {"sudo": "sudoers"}, {"$set": {"users": sudoers}}, upsert=True
            )

    # --- Auth Users (Group specific) ---
    async def is_auth_user(self, chat_id: int, user_id: int) -> bool:
        if not self.auth_users:
            return False
        user = await self.auth_users.find_one({"chat_id": chat_id, "user_id": user_id})
        return bool(user)

    async def add_auth_user(self, chat_id: int, user_id: int):
        if not self.auth_users:
            return
        await self.auth_users.update_one(
            {"chat_id": chat_id, "user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
        )

    async def remove_auth_user(self, chat_id: int, user_id: int):
        if not self.auth_users:
            return
        await self.auth_users.delete_one({"chat_id": chat_id, "user_id": user_id})

    # --- Group Settings ---
    async def add_group(self, chat_id: int):
        if not self.groups:
            return
        await self.groups.update_one(
            {"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True
        )

db = Database()
