from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import DB_CHANNEL_ID, OWNER_ID, UPDATE_CHANNEL
from database.database import get_data
from logger import logging
from .utils import format_minutes, safe_copy, schedule_auto_delete

logger = logging.getLogger(__name__)


@Client.on_message(filters.private & filters.incoming)
async def forcesub(c, m):
    if not UPDATE_CHANNEL:
        await m.continue_propagation()
        return

    owner = await c.get_users(OWNER_ID)
    try:
        user = await c.get_chat_member(UPDATE_CHANNEL, m.from_user.id)
        if user.status == "kicked":
            await m.reply_text("**Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ɪɴ Oᴜʀ ᴄʜᴀɴɴᴇʟ Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ 😜**", quote=True)
            return
    except UserNotParticipant:
        buttons = [[InlineKeyboardButton(text='Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ 🔖', url=f"https://t.me/{UPDATE_CHANNEL}")]]
        if m.text and len(m.text.split(' ')) > 1 and 'start' in m.text:
            chat_id, msg_id = m.text.split(' ')[1].split('_')
            buttons.append([InlineKeyboardButton('🔄 Rᴇғʀᴇsʜ', callback_data=f'refresh+{chat_id}+{msg_id}')])
        await m.reply_text(
            f"Hey {m.from_user.mention(style='md')} ʏᴏᴜ ɴᴇᴇᴅ ᴊᴏɪɴ Mʏ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ɪɴ ᴏʀᴅᴇʀ ᴛᴏ ᴜsᴇ ᴍᴇ 😉\n\n"
            "__Pʀᴇss ᴛʜᴇ Fᴏʟʟᴏᴡɪɴɢ Bᴜᴛᴛᴏɴ ᴛᴏ ᴊᴏɪɴ Nᴏᴡ 👇__",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
        return
    except Exception as e:
        logger.error(f"Forcesub check failed: {e}")
        await m.reply_text(f"Sᴏᴍᴇᴛʜɪɴɢ Wʀᴏɴɢ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ {owner.mention(style='md')}", quote=True)
        return

    await m.continue_propagation()


@Client.on_callback_query(filters.regex('^refresh'))
async def refresh_cb(c, m):
    owner = await c.get_users(OWNER_ID)
    if UPDATE_CHANNEL:
        try:
            user = await c.get_chat_member(UPDATE_CHANNEL, m.from_user.id)
            if user.status == "kicked":
                try:
                    await m.message.edit("**Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ɪɴ Oᴜʀ ᴄʜᴀɴɴᴇʟ Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ 😜**")
                except Exception:
                    pass
                return
        except UserNotParticipant:
            await m.answer('Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ʏᴇᴛ ᴊᴏɪɴᴇᴅ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ. \nFɪʀsᴛ ᴊᴏɪɴ ᴀɴᴅ ᴛʜᴇɴ ᴘʀᴇss ʀᴇғʀᴇsʜ ʙᴜᴛᴛᴏɴ 🤤', show_alert=True)
            return
        except Exception as e:
            logger.error(f"Refresh check failed: {e}")
            await m.message.edit(f"Sᴏᴍᴇᴛʜɪɴɢ Wʀᴏɴɢ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ{owner.mention(style='md')}")
            return

    cmd, chat_id, msg_id = m.data.split("+")
    msg = await c.get_messages(DB_CHANNEL_ID, int(msg_id))
    if msg.empty:
        return await m.reply_text(f"🥴 Sᴏʀʀʏ ʙʀᴏ ʏᴏᴜʀ ғɪʟᴇ ᴡᴀs ᴍɪssɪɴɢ\n\nPʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ 👉 {owner.mention(style='md')}")

    caption = msg.caption.markdown if msg.caption else ""
    as_uploadername = (await get_data(chat_id)).up_name
    if as_uploadername:
        if chat_id.startswith('-100'):  # file from channel
            channel = await c.get_chat(int(chat_id))
            caption += "\n\n\n**--Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs:--**\n\n"
            caption += f"**📢 Cʜᴀɴɴᴇʟ Nᴀᴍᴇ:** __{channel.title}__\n\n"
            caption += f"**🗣 Usᴇʀ Nᴀᴍᴇ:** @{channel.username}\n\n" if channel.username else ""
            caption += f"**👤 Cʜᴀɴɴᴇʟ Iᴅ:** __{channel.id}__\n\n"
        else:  # file not from channel
            user = await c.get_users(int(chat_id))
            caption += "\n\n\n**--Uᴘʟᴏᴀᴅᴇʀ Dᴇᴛᴀɪʟs:--**\n\n"
            caption += f"**🍁 Nᴀᴍᴇ:** [{user.first_name}](tg://user?id={user.id})\n\n"
            caption += f"**🖋 Usᴇʀ Nᴀᴍᴇ:** @{user.username}\n\n" if user.username else ""

    sent = await safe_copy(msg, m.from_user.id, caption=caption)
    await m.message.delete()

    delay = await schedule_auto_delete(sent)
    if delay:
        await c.send_message(m.from_user.id, f"⏳ Yʜ Fɪʟᴇ **{format_minutes(delay)}** ᴍᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏ ᴊᴀʏᴇɢɪ.")
