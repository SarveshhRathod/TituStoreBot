"""
Shared helpers used when delivering a stored file to a user, so every
delivery point (single file, batch, force-sub refresh) respects the
Admin Panel settings (Auto-Delete, Protect Content) the same way.
"""

import asyncio

from database.database import get_settings
from logger import logging

logger = logging.getLogger(__name__)


async def safe_copy(message, chat_id, caption=None):
    """Copy a message to `chat_id`, applying Protect Content if the admin
    turned it on. Falls back gracefully if the installed Pyrogram version
    doesn't support the `protect_content` parameter."""
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
    """If Auto-Delete is enabled in the Admin Panel, delete `sent_message`
    after the configured number of seconds. Returns the delay in seconds
    (so callers can tell the user), or None if the feature is off."""
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
