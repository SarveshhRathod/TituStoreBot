import asyncio
import base64

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import AUTH_USERS, DB_CHANNEL_ID, IS_PRIVATE, OWNER_ID
from database.database import get_data, update_as_name
from logger import logging
from .utils import format_minutes, safe_copy, schedule_auto_delete

logger = logging.getLogger(__name__)

BATCH = []


@Client.on_message(filters.command('start') & filters.incoming & filters.private)
async def start(c, m, cb=False):
    if not cb:
        send_msg = await m.reply_text("**Pʀᴏᴄᴇssɪɴɢ...**", quote=True)

    owner = await c.get_users(OWNER_ID)
    owner_username = owner.username if owner.username else 'SarveshhRathod'

    text = f"""**Hᴇʏ!** {m.from_user.mention(style='md')}

🤗 **I'm TituStoreBot **

‣ Yᴏᴜ ᴄᴀɴ sᴛᴏʀᴇ ʏᴏᴜʀ Tᴇʟᴇɢʀᴀᴍ Mᴇᴅɪᴀ ғᴏʀ ᴘᴇʀᴍᴀɴᴇɴᴛ Lɪɴᴋ! ᴀɴᴅ Sʜᴀʀᴇ Aɴʏᴡʜᴇʀᴇ

‣ Cʟɪᴄᴋ ᴏɴ Hᴇʟᴘ ᴀɴᴅ Kɴᴏᴡ Mᴏʀᴇ Aʙᴏᴜᴛ Usɪɴɢ ᴍᴇ

__🚸 Pᴏʀɴ Cᴏɴᴛᴇɴᴛ Nᴏᴛ Aʟʟᴏᴡᴇᴅ Oɴ Tʜᴇ Bᴏᴛ__

**💞 Mᴀɪɴᴛᴀɪɴᴇᴅ Bʏ:** {owner.mention(style='md')}
"""

    buttons = [[
        InlineKeyboardButton('Hᴇʟᴘ 💡', callback_data="help"),
        InlineKeyboardButton('Aʙᴏᴜᴛ 👑', callback_data="about")], [
        InlineKeyboardButton('Mʏ Fᴀᴛʜᴇʀ 👨‍✈️', url=f"https://t.me/{owner_username}"),
    ]]

    if cb:
        return await m.message.edit(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    if len(m.command) > 1:  # sending the stored file
        try:
            m.command[1] = await decode(m.command[1])
        except Exception:
            pass

        if 'batch_' in m.command[1]:
            await send_msg.delete()
            cmd, chat_id, message = m.command[1].split('_')
            string = await c.get_messages(DB_CHANNEL_ID, int(message))

            if string.empty:
                return await m.reply_text(
                    f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴅᴇʟᴇᴛᴇᴅ ʙʏ ғɪʟᴇ ᴏᴡɴᴇʀ ᴏʀ ʙᴏᴛ ᴏᴡɴᴇʀ\n\n"
                    f"Fᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ👉 {owner.mention(style='md')}"
                )
            message_ids = (await decode(string.text)).split('-')
            for msg_id in message_ids:
                msg = await c.get_messages(DB_CHANNEL_ID, int(msg_id))

                if msg.empty:
                    return await m.reply_text(
                        f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴅᴇʟᴇᴛᴇᴅ ʙʏ ғɪʟᴇ ᴏᴡɴᴇʀ ᴏʀ ʙᴏᴛ ᴏᴡɴᴇʀ\n\n"
                        f"Fᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ👉 {owner.mention(style='md')}"
                    )

                sent = await safe_copy(msg, m.from_user.id)
                delay = await schedule_auto_delete(sent)
                await asyncio.sleep(0.3)

            if delay:
                await c.send_message(
                    m.from_user.id,
                    f"⏳ Yʜ Fɪʟᴇs **{format_minutes(delay)}** ᴍᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏ ᴊᴀʏᴇɴɢɪ."
                )
            return

        chat_id, msg_id = m.command[1].split('_')
        msg = await c.get_messages(DB_CHANNEL_ID, int(msg_id))

        if msg.empty:
            return await send_msg.edit(
                f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴅᴇʟᴇᴛᴇᴅ ʙʏ ғɪʟᴇ ᴏᴡɴᴇʀ ᴏʀ ʙᴏᴛ ᴏᴡɴᴇʀ\n\n"
                f"Fᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ 👉 {owner.mention(style='md')}"
            )

        caption = f"{msg.caption.markdown}\n\n\n" if msg.caption else ""
        as_uploadername = (await get_data(chat_id)).up_name

        if as_uploadername:
            if chat_id.startswith('-100'):
                channel = await c.get_chat(int(chat_id))
                caption += "\n\n\n**--Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs:--**\n\n"
                caption += f"**📢 Cʜᴀɴɴᴇʟ Nᴀᴍᴇ:** __{channel.title}__\n\n"
                caption += f"**🗣 Usᴇʀ Nᴀᴍᴇ:** @{channel.username}\n\n" if channel.username else ""
                caption += f"**👤 Cʜᴀɴɴᴇʟ Iᴅ:** __{channel.id}__\n\n"
            else:
                user = await c.get_users(int(chat_id))
                caption += "\n\n\n**--Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs:--**\n\n"
                caption += f"**🍁 Nᴀᴍᴇ:** [{user.first_name}](tg://user?id={user.id})\n\n"
                caption += f"**🖋 Usᴇʀ Nᴀᴍᴇ:** @{user.username}\n\n" if user.username else ""

        await send_msg.delete()
        sent = await safe_copy(msg, m.from_user.id, caption=caption)
        delay = await schedule_auto_delete(sent)
        if delay:
            await m.reply_text(f"⏳ Yʜ Fɪʟᴇ **{format_minutes(delay)}** ᴍᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏ ᴊᴀʏᴇɢɪ.")

    else:  # sending start message
        await send_msg.edit(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@Client.on_message(filters.command('me') & filters.incoming & filters.private)
async def me(c, m):
    """ Tʜɪs ᴡɪʟʟ ʙᴇ sᴇɴᴛ ᴡʜᴇɴ /me ᴄᴏᴍᴍᴀɴᴅ ᴡᴀs ᴜsᴇᴅ"""

    me = await c.get_users(m.from_user.id)
    text = "--**Yᴏᴜʀ Dᴇᴛᴀɪʟs:**--\n\n\n"
    text += f"**🎨 Nᴀᴍᴇ:** [{me.first_name} {me.last_name or ''}](tg://user?id={me.id})\n\n"
    text += f"**👁 Usᴇʀ Nᴀᴍᴇ:** @{me.username}\n\n" if me.username else ""
    text += f"**✔ Is Vᴇʀɪғɪᴇᴅ Bʏ Tᴇʟᴇɢʀᴀᴍ:** __{me.is_verified}__\n\n" if me.is_verified else ""
    text += f"**👺 Is Fᴀᴋᴇ:** {me.is_fake}\n\n" if me.is_fake else ""
    text += f"**💨 Is Sᴄᴀᴍ:** {me.is_scam}\n\n" if me.is_scam else ""
    text += f"**📃 Lᴀɴɢᴜᴀɢᴇ Cᴏᴅᴇ:** __{me.language_code}__\n\n" if me.language_code else ""

    await m.reply_text(text, quote=True)


@Client.on_message(filters.command('batch') & filters.private & filters.incoming)
async def batch(c, m):
    """ Tʜɪs ɪs ғᴏʀ ʙᴀᴛᴄʜ ᴄᴏᴍᴍᴀɴᴅ"""
    if IS_PRIVATE and m.from_user.id not in AUTH_USERS:
        return

    BATCH.append(m.from_user.id)
    files = []
    i = 1

    while m.from_user.id in BATCH:
        if i == 1:
            media = await c.ask(chat_id=m.from_user.id, text='Sᴇɴᴅ ᴍᴇ sᴏᴍᴇ ғɪʟᴇs ᴏʀ ᴠɪᴅᴇᴏs ᴏʀ ᴘʜᴏᴛᴏs ᴏʀ ᴛᴇxᴛ ᴏʀ ᴀᴜᴅɪᴏ. Iғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇss sᴇɴᴅ /cancel')
            if media.text == "/cancel":
                return await m.reply_text('Cᴀɴᴄᴇʟʟᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ ✌')
            files.append(media)
        else:
            try:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Dᴏɴᴇ ✅', callback_data='done')]])
                media = await c.ask(chat_id=m.from_user.id, text='Oᴋ 😉. Nᴏᴡ sᴇɴᴅ ᴍᴇ sᴏᴍᴇ ᴍᴏʀᴇ ғɪʟᴇs Oʀ ᴘʀᴇss ᴅᴏɴᴇ ᴛᴏ ɢᴇᴛ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ. Iғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇss sᴇɴᴅ/cancel', reply_markup=reply_markup)
                if media.text == "/cancel":
                    return await m.reply_text('Cᴀɴᴄᴇʟʟᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ ✌')
                files.append(media)
            except Exception:
                pass
            except Exception as e:
                logger.error(f"Batch collection error: {e}")
                await m.reply_text(text="Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ. Tʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
        i += 1

    message = await m.reply_text("Gᴇɴᴇʀᴀᴛɪɴɢ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ 🔗")
    string = ""
    for file in files:
        copy_message = await file.copy(DB_CHANNEL_ID)
        string += f"{copy_message.message_id}-"
        await asyncio.sleep(0.3)

    string_base64 = await encode_string(string[:-1])
    send = await c.send_message(DB_CHANNEL_ID, string_base64)
    base64_string = await encode_string(f"batch_{m.chat.id}_{send.message_id}")
    bot = await c.get_me()
    url = f"https://t.me/{bot.username}?start={base64_string}"

    await message.edit(text=url)


@Client.on_message(filters.command('mode') & filters.incoming & filters.private)
async def set_mode(c, m):
    if IS_PRIVATE and m.from_user.id not in AUTH_USERS:
        return

    usr = m.from_user.id
    if len(m.command) > 1:
        usr = m.command[1]
    caption_mode = (await get_data(usr)).up_name
    if caption_mode:
        await update_as_name(usr, False)
        text = "Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs ɪɴ Cᴀᴘᴛɪᴏɴ: **Dɪsᴀʙʟᴇᴅ ❌**"
    else:
        await update_as_name(usr, True)
        text = "Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs ɪɴ Cᴀᴘᴛɪᴏɴ: **Eɴᴀʙʟᴇᴅ ✔️**"
    await m.reply_text(text, quote=True)


async def decode(base64_string):
    base64_bytes = base64_string.encode("ascii")
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode("ascii")


async def encode_string(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode("ascii")
