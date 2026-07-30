import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .commands import encode_string
from config import AUTH_USERS, DB_CHANNEL_ID, IS_PRIVATE


@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.incoming & ~filters.channel)
async def storefile(c, m):
    if IS_PRIVATE and m.from_user.id not in AUTH_USERS:
        return

    send_message = await m.reply_text("**Processing...**", quote=True)
    media = m.document or m.video or m.audio or m.photo

    text = ""
    if not m.photo:
        text = "--**🗃️ Fɪʟᴇ Dᴇᴛᴀɪʟs:**--\n\n"
        text += f"📂 ** Fɪʟᴇ ɴᴀᴍᴇ :** `{getattr(media, 'file_name', '')}`\n\n" if getattr(media, 'file_name', None) else ""
        text += f"🍃 **Mɪᴍᴇ Tʏᴘᴇ:** __{getattr(media, 'mime_type', '')}__\n\n" if getattr(media, 'mime_type', None) else ""
        text += f"📦 **Fɪʟᴇ ꜱɪᴢᴇ :** __{humanbytes(getattr(media, 'file_size', 0))}__\n\n" if getattr(media, 'file_size', None) else ""
        if not m.document:
            text += f"🎞 **Dᴜʀᴀᴛɪᴏɴ:** __{TimeFormatter(getattr(media, 'duration', 0) * 1000)}__\n\n" if getattr(media, 'duration', None) else ""
            if m.audio:
                text += f"🎵 **Tɪᴛʟᴇ:** __{getattr(media, 'title', '')}__\n\n" if getattr(media, 'title', None) else ""
                text += f"🎙 **Pᴇʀғᴏʀᴍᴇʀ:** __{getattr(media, 'performer', '')}__\n\n" if getattr(media, 'performer', None) else ""
    text += f"**✏ Cᴀᴘᴛɪᴏɴ:** __{m.caption}__\n\n" if m.caption else ""
    text += f"**🍁--Uᴘʟᴏᴀᴅᴇᴅ Bʏ :--** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n"

    msg = await m.copy(DB_CHANNEL_ID)
    await msg.reply(text)

    bot = await c.get_me()
    base64_string = await encode_string(f"{m.chat.id}_{msg.id}")
    url = f"https://t.me/{bot.username}?start={base64_string}"
    txt = urllib.parse.quote(text.replace('--', ''))
    share_url = f"tg://share?url={txt}File%20Link%20👉%20{url}"

    buttons = [[
        InlineKeyboardButton(text="Oᴘᴇɴ Uʀʟ 🔗", url=url),
        InlineKeyboardButton(text="Sʜᴀʀᴇ Lɪɴᴋ 👤", url=share_url)
    ], [
        InlineKeyboardButton(text="Dᴇʟᴇᴛᴇ Fɪʟᴇ🗑", callback_data=f"delete+{msg.id}")
    ]]

    await send_message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.incoming & filters.channel & ~filters.forwarded)
async def storefile_channel(c, m):
    if IS_PRIVATE and m.chat.id not in AUTH_USERS:
        return

    media = m.document or m.video or m.audio or m.photo

    text = ""
    if not m.photo:
        text = "--**🗃️ FɪʟES Dᴇᴛᴀɪʟs:**--\n\n"
        text += f"📂 ** Fɪʟᴇ ɴᴀᴍᴇ :** `{getattr(media, 'file_name', '')}`\n\n" if getattr(media, 'file_name', None) else ""
        text += f"🍃 **Mɪᴍᴇ Tʏᴘᴇ:** __{getattr(media, 'mime_type', '')}__\n\n" if getattr(media, 'mime_type', None) else ""
        text += f"📦 **Fɪʟᴇ ꜱɪᴢᴇ :** __{humanbytes(getattr(media, 'file_size', 0))}__\n\n" if getattr(media, 'file_size', None) else ""
        if not m.document:
            text += f"🎞 **Dᴜʀᴀᴛɪᴏɴ:** __{TimeFormatter(getattr(media, 'duration', 0) * 1000)}__\n\n" if getattr(media, 'duration', None) else ""
            if m.audio:
                text += f"🎵 **Tɪᴛʟᴇ:** __{getattr(media, 'title', '')}__\n\n" if getattr(media, 'title', None) else ""
                text += f"🎙 **Pᴇʀғᴏʀᴍᴇʀ:** __{getattr(media, 'performer', '')}__\n\n" if getattr(media, 'performer', None) else ""
    text += f"**✏ Cᴀᴘᴛɪᴏɴ:** __{m.caption}__\n\n" if m.caption else ""
    text += f"**🍁 Uᴘʟᴏᴀᴅᴇᴅ Bʏ :--** __{m.chat.title}__\n\n"
    text += f"**🗣 Usᴇʀ Nᴀᴍᴇ:** @{m.chat.username}\n\n" if m.chat.username else ""
    text += f"**👤 Cʜᴀɴɴᴇʟ Iᴅ:** __{m.chat.id}__\n\n"

    msg = await m.copy(DB_CHANNEL_ID)
    await msg.reply(text)

    bot = await c.get_me()
    base64_string = await encode_string(f"{m.chat.id}_{msg.id}")
    url = f"https://t.me/{bot.username}?start={base64_string}"
    txt = urllib.parse.quote(text.replace('--', ''))
    share_url = f"tg://share?url={txt}File%20Link%20👉%20{url}"

    buttons = [[
        InlineKeyboardButton(text="Oᴘᴇɴ Uʀʟ 🔗", url=url),
        InlineKeyboardButton(text="Sʜᴀʀᴇ Lɪɴᴋ 👤", url=share_url)
    ]]

    await m.edit_reply_markup(InlineKeyboardMarkup(buttons))


def humanbytes(size):
    if not size:
        return ""
    power = 2 ** 10
    n = 0
    dic_power_n = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + dic_power_n[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " days, ") if days else "") + \
        ((str(hours) + " hrs, ") if hours else "") + \
        ((str(minutes) + " min, ") if minutes else "") + \
        ((str(seconds) + " sec, ") if seconds else "") + \
        ((str(milliseconds) + " millisec, ") if milliseconds else "")
    return tmp[:-2]
