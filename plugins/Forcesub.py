from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import DB_CHANNEL_ID, OWNER_ID, UPDATE_CHANNEL
from database.database import get_data
from logger import logging
from .utils import format_minutes, safe_copy, schedule_auto_delete

logger = logging.getLogger(__name__)


@Client.on_message(filters.private & filters.incoming, group=-1)
async def forcesub(c, m):
    if not UPDATE_CHANNEL:
        await m.continue_propagation()
        return

    try:
        user = await c.get_chat_member(UPDATE_CHANNEL, m.from_user.id)
        if user.status == "kicked":
            await m.reply_text("**Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ɪɴ Oᴜʀ ᴄʜᴀɴɴᴇʟ. Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ 😜**", quote=True)
            return
    except UserNotParticipant:
        buttons = [[InlineKeyboardButton(text='Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ 🔖', url=f"https://t.me/{UPDATE_CHANNEL}")]]
        if m.text and len(m.text.split(' ')) > 1 and 'start' in m.text:
            param = m.text.split(' ')[1]
            buttons.append([InlineKeyboardButton('🔄 Rᴇғʀᴇsʜ', callback_data=f'refresh+{param}')])
        await m.reply_text(
            f"Hey {m.from_user.mention} ʏᴏᴜ ɴᴇᴇᴅ to ᴊᴏɪɴ Mʏ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ɪɴ ᴏʀᴅᴇʀ ᴛᴏ ᴜsᴇ ᴍᴇ 😉\n\n"
            "__Pʀᴇss ᴛʜᴇ Fᴏʟʟᴏᴡɪɴɢ Bᴜᴛᴛᴏɴ ᴛᴏ ᴊᴏɪɴ Nᴏᴡ 👇__",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
        return
    except Exception as e:
        logger.error(f"Forcesub check failed: {e}")
        owner_mention = f"tg://user?id={OWNER_ID}"
        await m.reply_text(f"Sᴏᴍᴇᴛʜɪɴɢ Wʀᴏɴɢ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ [Owner]({owner_mention})", quote=True)
        return

    await m.continue_propagation()


@Client.on_callback_query(filters.regex('^refresh'))
async def refresh_cb(c, m):
    owner_mention = f"tg://user?id={OWNER_ID}"
    if UPDATE_CHANNEL:
        try:
            user = await c.get_chat_member(UPDATE_CHANNEL, m.from_user.id)
            if user.status == "kicked":
                try:
                    await m.message.edit("**Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ɪɴ Oᴜʀ ᴄʜᴀɴɴᴇʟ. Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ 😜**")
                except Exception:
                    pass
                return
        except UserNotParticipant:
            await m.answer('Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ʏᴇᴛ ᴊᴏɪɴᴇᴅ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ. \nFɪʀsᴛ ᴊᴏɪɴ ᴀɴᴅ ᴛʜᴇɴ ᴘʀᴇss ʀᴇғʀᴇsʜ ʙᴜᴛᴛᴏɴ 🤤', show_alert=True)
            return
        except Exception as e:
            logger.error(f"Refresh check failed: {e}")
            await m.message.edit(f"Sᴏᴍᴇᴛʜɪɴɢ Wʀᴏɴɢ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ [Owner]({owner_mention})")
            return

    data_parts = m.data.split("+")
    if len(data_parts) < 2:
        return await m.answer("Invalid Data!", show_alert=True)

    param = data_parts[1]
    from .commands import decode
    try:
        decoded = await decode(param)
        parts = decoded.split('_')
        chat_id = parts[0]
        msg_id = parts[1]
    except Exception:
        return await m.answer("Invalid file parameters!", show_alert=True)

    msg = await c.get_messages(DB_CHANNEL_ID, int(msg_id))
    if msg.empty:
        return await m.reply_text(f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴍɪssɪɴɢ\n\nPʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ 👉 [Owner]({owner_mention})")

    caption = msg.caption.markdown if msg.caption else ""
    as_uploadername = (await get_data(chat_id)).up_name
    if as_uploadername:
        if str(chat_id).startswith('-100'):
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

    sent = await safe_copy(msg, m.from_user.id, caption=caption)
    await m.message.delete()

    delay = await schedule_auto_delete(sent)
    if delay:
        await c.send_message(m.from_user.id, f"⏳ Yʜ Fɪʟᴇ **{format_minutes(delay)}** ᴍᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏ ᴊᴀʏᴇɢɪ.")
