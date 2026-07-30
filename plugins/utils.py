import asyncio
from database.database import get_settings
from logger import logging

logger = logging.getLogger(__name__)


async def safe_copy(message, chat_id, caption=None):
    settings = await get_settings()
    protect = settings.get("protect_content", False)
    kwargs = {}
    if caption is not None:
        kwargs["caption"] = caption

    try:
        return await message.copy(chat_id, protect_content=protect, **kwargs)
    except TypeError:
        return await message.copy(chat_id, **kwargs)


async def schedule_auto_delete(sent_message):
    settings = await get_settings()
    if not settings.get("auto_delete", False):
        return None

    seconds = settings.get("auto_delete_seconds", 600)
    asyncio.create_task(_delete_later(sent_message, seconds))
    return seconds


async def _delete_later(message, seconds):
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Auto-delete failed for message {message.id}: {e}")


def format_minutes(seconds: int) -> str:
    minutes = max(1, seconds // 60)
    return f"{minutes} minute" + ("s" if minutes != 1 else "")
