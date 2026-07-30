import asyncio
import time
from database.database import get_settings, get_user_lang
from config import RATE_LIMIT_PER_MIN
from logger import logging

logger = logging.getLogger(__name__)

# Anti-Spam Rate Limiter (Sliding Window In-Memory)
_user_requests = {}


def is_rate_limited(user_id: int) -> bool:
    now = time.time()
    timestamps = _user_requests.get(user_id, [])
    # Filter requests older than 60s
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= RATE_LIMIT_PER_MIN:
        _user_requests[user_id] = timestamps
        return True
    timestamps.append(now)
    _user_requests[user_id] = timestamps
    return False


# Multi-Language Strings
STRINGS = {
    "en": {
        "start": "Hᴇʏ! {mention}\n\n🤗 **I'm TituStoreBot**\n\n‣ Yᴏᴜ ᴄᴀɴ sᴛᴏʀᴇ ʏᴏᴜʀ Tᴇʟᴇɢʀᴀᴍ Mᴇᴅɪᴀ ғᴏʀ ᴘᴇʀᴍᴀɴᴇɴᴛ Lɪɴᴋ!",
        "rate_limit": "⚠️ **Rᴀᴛᴇ Lɪᴍɪᴛ Exᴄᴇᴇᴅᴇᴅ!** Pʟᴇᴀsᴇ ᴡᴀɪᴛ A Fᴇᴡ Sᴇᴄᴏɴᴅs Bᴇғᴏʀᴇ Nᴇxᴛ Rᴇǫᴜᴇsᴛ.",
        "pin_prompt": "🔐 **Tʜɪs ғɪʟᴇ ɪs Pɪɴ/Pᴀssᴡᴏʀᴅ Pʀᴏᴛᴇᴄᴛᴇᴅ.**\n\nEntᴇʀ Tʜᴇ 4-Dɪɢɪᴛ PIN Tᴏ Aᴄᴄᴇss:",
        "pin_wrong": "❌ **Iɴᴄᴏʀʀᴇᴄᴛ PIN!** Aᴄᴄᴇss Dᴇɴɪᴇᴅ.",
        "auto_del_msg": "⏳ Yʜ Fɪʟᴇ **{time}** ᴍᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏ ᴊᴀʏᴇɢɪ.",
    },
    "hi": {
        "start": "नमस्ते {mention}!\n\n🤗 **मैं TituStoreBot हूँ**\n\n‣ आप यहाँ अपनी फाइलें हमेशा के लिए शेयर कर सकते हैं!",
        "rate_limit": "⚠️ **स्पीड लिमिट!** कृपया अगली फ़ाइल माँगने से पहले कुछ सेकंड प्रतीक्षा करें।",
        "pin_prompt": "🔐 **यह फ़ाइल पासवर्ड द्वारा सुरक्षित है।**\n\nएक्सेस करने के लिए 4 अंकों का PIN दर्ज करें:",
        "pin_wrong": "❌ **गलत PIN!** पहुँच अस्वीकृत।",
        "auto_del_msg": "⏳ यह फ़ाइल **{time}** में ऑटो-डिलीट हो जाएगी।",
    },
    "hn": {
        "start": "Hey {mention}!\n\n🤗 **Main TituStoreBot hoon**\n\n‣ Yahan apni files store karo permanently!",
        "rate_limit": "⚠️ **Thoda ruk ke request karo bhai!** Spam mat karo.",
        "pin_prompt": "🔐 **Yeh file Password Protected hai.**\n\n4-digit PIN enter karo unlock karne ke liye:",
        "pin_wrong": "❌ **Galat PIN!** Access nahi milega.",
        "auto_del_msg": "⏳ Yeh File **{time}** me auto-delete ho jayegi.",
    }
}


async def tr(user_id: int, key: str, **kwargs) -> str:
    lang = await get_user_lang(user_id)
    text = STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, ""))
    return text.format(**kwargs) if kwargs else text


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


async def format_caption(media_name: str, media_size: str, uploader: str, downloads: int, raw_caption: str = "") -> str:
    settings = await get_settings()
    template = settings.get("custom_caption", "").strip()
    watermark = settings.get("watermark", "").strip()

    if template:
        caption = template.replace("{file_name}", media_name)\
                          .replace("{file_size}", media_size)\
                          .replace("{uploader}", uploader)\
                          .replace("{downloads}", str(downloads))
    else:
        caption = f"📂 **Fɪʟᴇ Nᴀᴍᴇ:** `{media_name}`\n📦 **Fɪʟᴇ Sɪᴢᴇ:** `{media_size}`\n👁 **Dᴏᴡɴʟᴏᴀᴅs:** `{downloads}`\n🍁 **Uᴘʟᴏᴀᴅᴇʀ:** {uploader}"
        if raw_caption:
            caption += f"\n\n✏️ **Cᴀᴘᴛɪᴏɴ:** {raw_caption}"

    if watermark:
        caption += f"\n\n🔰 **Pᴏᴡᴇʀᴇᴅ Bʏ:** {watermark}"

    return caption
