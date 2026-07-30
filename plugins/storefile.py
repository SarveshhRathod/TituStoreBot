import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .commands import encode_string, humanbytes
from database.database import get_downloads, get_indexed_file, save_file_index
from config import AUTH_USERS, DB_CHANNEL_ID, IS_PRIVATE, WEB_URL
from .utils import is_playable


@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.incoming & ~filters.channel)
async def storefile(c, m):
    if IS_PRIVATE and m.from_user.id not in AUTH_USERS:
        return

    send_message = await m.reply_text("**Processing & Indexing...**", quote=True)
    media = m.document or m.video or m.audio or m.photo
    file_unique_id = getattr(media, "file_unique_id", None)

    # Deduplication Check
    indexed = await get_indexed_file(file_unique_id) if file_unique_id else None
    if indexed:
        msg_id = indexed["msg_id"]
    else:
        msg = await m.copy(DB_CHANNEL_ID)
        msg_id = msg.id
        if file_unique_id:
            await save_file_index(file_unique_id, msg_id, m.chat.id)

    media_name = getattr(media, 'file_name', 'File')
    media_size = humanbytes(getattr(media, 'file_size', 0))
    downloads = await get_downloads(f"{m.chat.id}_{msg_id}")

    text = "--**🗃️ Fɪʟᴇ Dᴇᴛᴀɪʟs:**--\n\n"
    text += f"📂 **Fɪʟᴇ Nᴀᴍᴇ:** `{media_name}`\n\n"
    text += f"📦 **Fɪʟᴇ Sɪᴢᴇ:** __{media_size}__\n\n"
    text += f"👁 **Dᴏᴡɴʟᴏᴀᴅs:** `{downloads}`\n\n"
    text += f"🍁 **UᴘʟᴏᴀᴅᴇD Bʏ:** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n"

    bot = await c.get_me()
    base64_string = await encode_string(f"{m.chat.id}_{msg_id}")
    url = f"https://t.me/{bot.username}?start={base64_string}"
    txt = urllib.parse.quote(text.replace('--', ''))
    share_url = f"tg://share?url={txt}File%20Link%20👉%20{url}"

    buttons = [
        [
            InlineKeyboardButton(text="Oᴘᴇɴ Uʀʟ 🔗", url=url),
            InlineKeyboardButton(text="Sʜᴀʀᴇ Lɪɴᴋ 👤", url=share_url)
        ]
    ]

    # Stream button ONLY if playable video/audio/doc and WEB_URL exists
    if WEB_URL and is_playable(media):
        stream_link = f"{WEB_URL}/stream/{base64_string}"
        buttons.append([InlineKeyboardButton(text="🎬 Watch Online / Stream", url=stream_link)])

    buttons.append([InlineKeyboardButton(text="Dᴇʟᴇᴛᴇ Fɪʟᴇ🗑", callback_data=f"delete+{msg_id}")])

    await send_message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.incoming & filters.channel & ~filters.forwarded)
async def storefile_channel(c, m):
    if IS_PRIVATE and m.chat.id not in AUTH_USERS:
        return

    media = m.document or m.video or m.audio or m.photo
    file_unique_id = getattr(media, "file_unique_id", None)

    indexed = await get_indexed_file(file_unique_id) if file_unique_id else None
    if indexed:
        msg_id = indexed["msg_id"]
    else:
        msg = await m.copy(DB_CHANNEL_ID)
        msg_id = msg.id
        if file_unique_id:
            await save_file_index(file_unique_id, msg_id, m.chat.id)

    bot = await c.get_me()
    base64_string = await encode_string(f"{m.chat.id}_{msg_id}")
    url = f"https://t.me/{bot.username}?start={base64_string}"

    buttons = [[
        InlineKeyboardButton(text="OᴘᴇN Uʀʟ 🔗", url=url)
    ]]

    if WEB_URL and is_playable(media):
        stream_link = f"{WEB_URL}/stream/{base64_string}"
        buttons[0].append(InlineKeyboardButton(text="🎬 Watch Online", url=stream_link))

    await m.edit_reply_markup(InlineKeyboardMarkup(buttons))
