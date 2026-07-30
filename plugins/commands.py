import asyncio
import base64

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import AUTH_USERS, DB_CHANNEL_ID, IS_PRIVATE, OWNER_ID, WEB_URL
from database.database import (
    get_data, get_downloads, get_settings, increment_downloads,
    set_user_lang, update_as_name, update_settings
)
from logger import logging
from .utils import (
    format_caption, format_minutes, is_rate_limited,
    safe_copy, schedule_auto_delete, tr
)

logger = logging.getLogger(__name__)

BATCH = []


@Client.on_message(filters.command('start') & filters.incoming & filters.private)
async def start(c, m, cb=False):
    if is_rate_limited(m.from_user.id):
        msg = await tr(m.from_user.id, "rate_limit")
        return await m.reply_text(msg, quote=True)

    if not cb:
        send_msg = await m.reply_text("**Pʀᴏᴄᴇssɪɴɢ...**", quote=True)

    owner_mention = f"[{OWNER_ID}](tg://user?id={OWNER_ID})"
    try:
        owner = await c.get_users(OWNER_ID)
        owner_username = owner.username if owner.username else 'SarveshhRathod'
        owner_mention = owner.mention
    except Exception:
        owner_username = 'SarveshhRathod'

    text = await tr(m.from_user.id, "start", mention=m.from_user.mention)

    buttons = [[
        InlineKeyboardButton('Hᴇʟᴘ 💡', callback_data="help"),
        InlineKeyboardButton('Aʙᴏᴜᴛ 👑', callback_data="about")], [
        InlineKeyboardButton('🌐 Lᴀɴɢᴜᴀɢᴇ', callback_data="setlang_menu"),
        InlineKeyboardButton('Mʏ Fᴀᴛʜᴇʀ 👨‍✈️', url=f"https://t.me/{owner_username}"),
    ]]

    if cb:
        return await m.message.edit(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    if len(m.command) > 1:
        param = m.command[1]
        try:
            decoded_param = await decode(param)
        except Exception:
            decoded_param = param

        # Password / PIN Check
        if "_pin" in decoded_param:
            raw_param, pin_code = decoded_param.split("_pin")
            try:
                ask_pin = await c.ask(
                    chat_id=m.from_user.id,
                    text=await tr(m.from_user.id, "pin_prompt"),
                    timeout=60
                )
                if ask_pin.text.strip() != pin_code:
                    return await ask_pin.reply_text(await tr(m.from_user.id, "pin_wrong"))
            except Exception:
                return await send_msg.edit("⌛ PIN Verification Timeout.")
            decoded_param = raw_param

        if 'batch_' in decoded_param:
            await send_msg.delete()
            try:
                cmd, chat_id, message = decoded_param.split('_')
                string = await c.get_messages(DB_CHANNEL_ID, int(message))

                if string.empty:
                    return await m.reply_text(
                        f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴅᴇʟᴇᴛᴇᴅ\n\nFᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ ᴄᴏɴᴛᴀᴄᴛ {owner_mention}"
                    )

                decoded_msg_ids = await decode(string.text)
                message_ids = decoded_msg_ids.split('-')

                delay = None
                for msg_id in message_ids:
                    msg = await c.get_messages(DB_CHANNEL_ID, int(msg_id))
                    if msg.empty:
                        continue

                    downloads = await increment_downloads(f"{chat_id}_{msg_id}")
                    sent = await safe_copy(msg, m.from_user.id)
                    delay = await schedule_auto_delete(sent)
                    await asyncio.sleep(0.3)

                if delay:
                    del_text = await tr(m.from_user.id, "auto_del_msg", time=format_minutes(delay))
                    await c.send_message(m.from_user.id, del_text)
                return
            except Exception as e:
                logger.error(f"Error handling batch: {e}")
                return await m.reply_text(f"🥴 Error retrieving batch files. Contact {owner_mention}")

        try:
            chat_id, msg_id = decoded_param.split('_')
            msg = await c.get_messages(DB_CHANNEL_ID, int(msg_id))

            if msg.empty:
                return await send_msg.edit(
                    f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴅᴇʟᴇᴛᴇᴅ\n\nFᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ ᴄᴏɴᴛᴀᴄᴛ {owner_mention}"
                )

            downloads = await increment_downloads(f"{chat_id}_{msg_id}")
            media = msg.document or msg.video or msg.audio or msg.photo
            media_name = getattr(media, "file_name", "File")
            media_size = humanbytes(getattr(media, "file_size", 0))

            uploader = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
            caption = await format_caption(media_name, media_size, uploader, downloads, msg.caption.markdown if msg.caption else "")

            await send_msg.delete()
            sent = await safe_copy(msg, m.from_user.id, caption=caption)
            delay = await schedule_auto_delete(sent)
            if delay:
                del_text = await tr(m.from_user.id, "auto_del_msg", time=format_minutes(delay))
                await m.reply_text(del_text)
        except Exception as e:
            logger.error(f"Error serving file: {e}")
            await send_msg.edit(f"🥴 Invalid or expired file link. Contact {owner_mention}")

    else:
        await send_msg.edit(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@Client.on_message(filters.command('lang') & filters.private & filters.incoming)
async def lang_cmd(c, m):
    buttons = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en")],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data="setlang_hi")],
        [InlineKeyboardButton("Hinglish 💬", callback_data="setlang_hn")]
    ]
    await m.reply_text("🌐 **Sᴇʟᴇᴄᴛ Yᴏᴜʀ Pʀᴇғᴇʀʀᴇᴅ Lᴀɴɢᴜᴀɢᴇ:**", reply_markup=InlineKeyboardMarkup(buttons), quote=True)


@Client.on_callback_query(filters.regex("^setlang_menu$"))
async def lang_menu_cb(c, m):
    await m.answer()
    buttons = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en")],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data="setlang_hi")],
        [InlineKeyboardButton("Hinglish 💬", callback_data="setlang_hn")]
    ]
    await m.message.edit("🌐 **Sᴇʟᴇᴄᴛ Yᴏᴜʀ Pʀᴇғᴇʀʀᴇᴅ Lᴀɴɢᴜᴀɢᴇ:**", reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command('me') & filters.incoming & filters.private)
async def me(c, m):
    user = m.from_user
    text = "--**Yᴏᴜʀ Dᴇᴛᴀɪʟs:**--\n\n\n"
    text += f"**🎨 Nᴀᴍᴇ:** [{user.first_name} {user.last_name or ''}](tg://user?id={user.id})\n\n"
    text += f"**👁 Usᴇʀ Nᴀᴍᴇ:** @{user.username}\n\n" if user.username else ""
    text += f"**✔ Is Vᴇʀɪғɪᴇᴅ Bʏ Tᴇʟᴇɢʀᴀᴍ:** __{user.is_verified}__\n\n" if user.is_verified else ""
    text += f"**👺 Is Fᴀᴋᴇ:** {user.is_fake}\n\n" if user.is_fake else ""
    text += f"**💨 Is Sᴄᴀᴍ:** {user.is_scam}\n\n" if user.is_scam else ""
    text += f"**📃 Lᴀɴɢᴜᴀɢᴇ Cᴏᴅᴇ:** __{user.language_code}__\n\n" if user.language_code else ""

    await m.reply_text(text, quote=True)


@Client.on_message(filters.command('batch') & filters.private & filters.incoming)
async def batch(c, m):
    if IS_PRIVATE and m.from_user.id not in AUTH_USERS:
        return

    BATCH.append(m.from_user.id)
    files = []
    i = 1

    while m.from_user.id in BATCH:
        if i == 1:
            try:
                media = await c.ask(
                    chat_id=m.from_user.id,
                    text='Sᴇɴᴅ ᴍᴇ sᴏᴍᴇ ғɪʟᴇs ᴏʀ ᴠɪᴅᴇᴏs ᴏʀ ᴘʜᴏᴛᴏs. Send /cancel to stop.',
                    timeout=300
                )
            except Exception:
                if m.from_user.id in BATCH:
                    BATCH.remove(m.from_user.id)
                return await m.reply_text('⌛ Bᴀᴛᴄʜ ᴛɪᴍᴇᴏᴜᴛ. Cᴀɴᴄᴇʟʟᴇᴅ.')

            if media.text == "/cancel":
                BATCH.remove(m.from_user.id)
                return await m.reply_text('Cᴀɴᴄᴇʟʟᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ ✌')
            files.append(media)
        else:
            try:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Dᴏɴᴇ ✅', callback_data='done')]])
                media = await c.ask(
                    chat_id=m.from_user.id,
                    text='Oᴋ 😉. Send more files or press Done to get shareable link. Send /cancel to stop.',
                    reply_markup=reply_markup,
                    timeout=300
                )
                if media.text == "/cancel":
                    if m.from_user.id in BATCH:
                        BATCH.remove(m.from_user.id)
                    return await m.reply_text('Cᴀɴᴄᴇʟʟᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ ✌')
                files.append(media)
            except Exception:
                break
        i += 1

    if m.from_user.id in BATCH:
        BATCH.remove(m.from_user.id)

    if not files:
        return await m.reply_text("Nᴏ ғɪʟᴇs ʀᴇᴄᴇɪᴠᴇᴅ!")

    message = await m.reply_text("Gᴇɴᴇʀᴀᴛɪɴɢ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ 🔗")
    string = ""
    for file in files:
        copy_message = await file.copy(DB_CHANNEL_ID)
        string += f"{copy_message.id}-"
        await asyncio.sleep(0.3)

    string_base64 = await encode_string(string[:-1])
    send = await c.send_message(DB_CHANNEL_ID, string_base64)
    base64_string = await encode_string(f"batch_{m.chat.id}_{send.id}")
    bot = await c.get_me()
    url = f"https://t.me/{bot.username}?start={base64_string}"

    await message.edit(text=f"🔗 **Bᴀᴛᴄʜ Sʜᴀʀᴇᴀʙʟᴇ Lɪɴᴋ:**\n{url}")


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
        text = "Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs ɪɴ Cᴀᴘᴛɪᴏɴ: **Dɪsᴀ┴ʟᴇᴅ ❌**"
    else:
        await update_as_name(usr, True)
        text = "Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs ɪɴ Cᴀᴘᴛɪᴏɴ: **Eɴᴀʙʟᴇᴅ ✔️**"
    await m.reply_text(text, quote=True)


# Multi-Admin Moderator Commands
@Client.on_message(filters.command('addmod') & filters.incoming & filters.private)
async def add_mod(c, m):
    if m.from_user.id != OWNER_ID:
        return await m.reply_text("🚫 Sɪʀғ Bᴏᴛ Oᴡɴᴇʀ ʜɪ Mᴏᴅᴇʀᴀᴛᴏʀ ᴀᴅᴅ ᴋᴀʀ sᴀᴋᴛᴀ ʜᴀɪ.")

    if len(m.command) < 2:
        return await m.reply_text("Usage: `/addmod <user_id>`")

    target_id = int(m.command[1])
    settings = await get_settings()
    mods = settings.get("moderators", [])
    if target_id not in mods:
        mods.append(target_id)
        await update_settings(moderators=mods)
        await m.reply_text(f"✅ User `{target_id}` is now a Moderator.")
    else:
        await m.reply_text("⚠️ User is already a Moderator.")


@Client.on_message(filters.command('rmmod') & filters.incoming & filters.private)
async def rm_mod(c, m):
    if m.from_user.id != OWNER_ID:
        return await m.reply_text("🚫 Sɪʀғ Bᴏᴛ Oᴡɴᴇʀ ʜɪ Mᴏᴅᴇʀᴀᴛᴏʀ remove ᴋᴀʀ sᴀᴋᴛᴀ ʜᴀɪ.")

    if len(m.command) < 2:
        return await m.reply_text("Usage: `/rmmod <user_id>`")

    target_id = int(m.command[1])
    settings = await get_settings()
    mods = settings.get("moderators", [])
    if target_id in mods:
        mods.remove(target_id)
        await update_settings(moderators=mods)
        await m.reply_text(f"✅ User `{target_id}` removed from Moderators.")
    else:
        await m.reply_text("⚠️ User is not a Moderator.")


def humanbytes(size):
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    dic_power_n = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + dic_power_n[n] + 'B'


async def decode(base64_string: str) -> str:
    base64_string = base64_string.strip()
    padding = '=' * (4 - len(base64_string) % 4) if len(base64_string) % 4 != 0 else ''
    base64_bytes = (base64_string + padding).replace('-', '+').replace('_', '/').encode("ascii")
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode("ascii")


async def encode_string(string: str) -> str:
    string_bytes = string.encode("ascii")
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode("ascii").replace('+', '-').replace('/', '_').rstrip('=')
