import asyncio
import motor.motor_asyncio
from config import DB_NAME, MAX_DB_SIZE_MB, MONGO_URIS
from logger import logging

logger = logging.getLogger(__name__)

_clients = [motor.motor_asyncio.AsyncIOMotorClient(uri) for uri in MONGO_URIS]
_dbs = [client[DB_NAME] for client in _clients]

logger.info(f"Connected to {len(_dbs)} MongoDB database(s).")

_active_index = 0
_switch_lock = asyncio.Lock()


async def _size_mb(db) -> float:
    try:
        stats = await db.command("dbstats")
        return stats.get("dataSize", 0) / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not fetch dbstats: {e}")
        return 0.0


async def get_active_db():
    global _active_index

    if len(_dbs) == 1:
        return _dbs[0]

    async with _switch_lock:
        if _active_index < len(_dbs) - 1:
            size = await _size_mb(_dbs[_active_index])
            if size >= MAX_DB_SIZE_MB:
                _active_index += 1
                logger.info(
                    f"Database #{_active_index} is full ({size:.1f}MB) -> "
                    f"switching to database #{_active_index + 1}."
                )
        return _dbs[_active_index]


async def get_db_status():
    status = []
    for i, db in enumerate(_dbs, start=1):
        size = await _size_mb(db)
        status.append({
            "index": i,
            "active": (i - 1) == _active_index,
            "size_mb": round(size, 2),
            "limit_mb": MAX_DB_SIZE_MB,
        })
    return status


async def update_as_name(id_val, mode: bool):
    id_str = str(id_val)
    for db in _dbs:
        existing = await db.settings.find_one({"_id": id_str}, {"_id": 1})
        if existing:
            await db.settings.update_one({"_id": id_str}, {"$set": {"up_name": mode}})
            return

    db = await get_active_db()
    await db.settings.update_one({"_id": id_str}, {"$set": {"up_name": mode}}, upsert=True)


async def get_data(id_val):
    id_str = str(id_val)
    for db in _dbs:
        doc = await db.settings.find_one({"_id": id_str})
        if doc:
            return _Row(doc.get("up_name", False))

    db = await get_active_db()
    await db.settings.insert_one({"_id": id_str, "up_name": False})
    return _Row(False)


class _Row:
    __slots__ = ("up_name",)

    def __init__(self, up_name):
        self.up_name = up_name


# ---------------- Global bot settings ----------------
_SETTINGS_ID = "global"
DEFAULT_SETTINGS = {
    "_id": _SETTINGS_ID,
    "auto_delete": False,
    "auto_delete_seconds": 600,
    "protect_content": False,
}


async def get_settings() -> dict:
    for db in _dbs:
        doc = await db.bot_config.find_one({"_id": _SETTINGS_ID})
        if doc:
            return {**DEFAULT_SETTINGS, **doc}

    db = await get_active_db()
    await db.bot_config.insert_one(DEFAULT_SETTINGS.copy())
    return DEFAULT_SETTINGS.copy()


async def update_settings(**kwargs) -> None:
    for db in _dbs:
        existing = await db.bot_config.find_one({"_id": _SETTINGS_ID}, {"_id": 1})
        if existing:
            await db.bot_config.update_one({"_id": _SETTINGS_ID}, {"$set": kwargs})
            return

    db = await get_active_db()
    doc = DEFAULT_SETTINGS.copy()
    doc.update(kwargs)
    await db.bot_config.update_one({"_id": _SETTINGS_ID}, {"$set": doc}, upsert=True)
