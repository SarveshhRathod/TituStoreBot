from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .commands import BATCH, start
from config import DB_CHANNEL_ID


@Client.on_callback_query(filters.regex('^help$'))
async def help_cb(c, m):
    await m.answer()

    help_text = """**Yᴏᴜ ɴᴇᴇᴅ Hᴇʟᴘ?? 🧐**

★ Jᴜsᴛ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ғɪʟᴇs I ᴡɪʟʟ sᴛᴏʀᴇ ғɪʟᴇ ᴀɴᴅ ɢɪᴠᴇ ʏᴏᴜ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ.

**Yᴏᴜ ᴄᴀɴ ᴜsᴇ ᴍᴇ ɪɴ ᴄʜᴀɴɴᴇʟ ᴛᴏᴏ 😉**

★ Mᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴡɪᴛʜ ᴇᴅɪᴛ ᴘᴇʀᴍɪssɪᴏɴ. Tʜᴀᴛ's ᴇɴᴏᴜɢʜ, ɴᴏᴡ ᴄᴏɴᴛɪɴᴜᴇ ᴜᴘʟᴏᴀᴅɪɴɢ ғɪʟᴇs ɪɴ ᴄʜᴀɴɴᴇʟ and I ᴡɪʟʟ ᴇᴅɪᴛ ᴀʟʟ ᴘᴏsᴛs ᴀɴᴅ ᴀᴅᴅ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ URL ʙᴜᴛᴛᴏɴs.

**Hᴏᴡ ᴛᴏ ᴇɴᴀʙʟᴇ ᴜᴘʟᴏᴀᴅᴇʀ ᴅᴇᴛᴀɪʟs ɪɴ ᴄᴀᴘᴛɪᴏɴ**

★ Usᴇ /mode ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴄʜᴀɴɢᴇ ᴀɴᴅ ᴀʟsᴏ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ `/mode channel_id` ᴛᴏ ᴄᴏɴᴛʀᴏʟ ᴄᴀᴘᴛɪᴏɴ ғᴏʀ ᴄʜᴀɴɴᴇʟ ᴍsɢ."""

    buttons = [[
        InlineKeyboardButton('Hᴏᴍᴇ 🏕', callback_data='home'),
        InlineKeyboardButton('Aʙᴏᴜᴛ 📕', callback_data='about')], [
        InlineKeyboardButton('Cʟᴏsᴇ 🔐', callback_data='close')
    ]]

    await m.message.edit(
        text=help_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex('^close$'))
async def close_cb(c, m):
    await m.message.delete()
    if m.message.reply_to_message:
        try:
            await m.message.reply_to_message.delete()
        except Exception:
            pass


@Client.on_callback_query(filters.regex('^about$'))
async def about_cb(c, m):
    await m.answer()

    about_text = """--**🍺 Mʏ Dᴇᴛᴀɪʟs:**--

╭───[ **🔅 TɪᴛᴜꜱᴛᴏʀᴇBᴏᴛ 🔅** ]───⍟
│
├**🔸Vᴇʀꜱɪᴏɴ :** `4.5.0`
│
├**🔹Sᴏᴜʀᴄᴇ :** [Cʟɪᴄᴋ Hᴇʀᴇ 🥰](https://github.com/SarveshhRathod/TituStoreBot)
│
├**🔸GitHub :** [Fᴏʟʟᴏᴡ](https://GitHub.com/SarveshhRathod)
│
├**🔹Dᴇᴠᴇʟᴏᴘᴇʀ :** [Sᴀʀᴠᴇsʜʜ Rᴀᴛʜᴏᴅ (Tɪᴛᴜ)](https://telegram.me/SarveshhRathod)
│
╰─────────[ 😎 ]────────⍟
"""

    buttons = [[
        InlineKeyboardButton('Hᴏᴍᴇ 🏕', callback_data='home'),
        InlineKeyboardButton('Hᴇʟᴘ 💡', callback_data='help')], [
        InlineKeyboardButton('Cʟᴏsᴇ 🔐', callback_data='close')
    ]]

    await m.message.edit(
        text=about_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex('^home$'))
async def home_cb(c, m):
    await m.answer()
    await start(c, m, cb=True)


@Client.on_callback_query(filters.regex('^done$'))
async def done_cb(c, m):
    if m.from_user.id in BATCH:
        BATCH.remove(m.from_user.id)
    if hasattr(c, "stop_listening"):
        c.stop_listening(chat_id=m.from_user.id)
    elif hasattr(c, "cancel_listener"):
        c.cancel_listener(m.from_user.id)
    await m.message.delete()


@Client.on_callback_query(filters.regex('^delete'))
async def delete_cb(c, m):
    await m.answer()
    data_parts = m.data.split("+")
    if len(data_parts) > 1:
        msg_id = data_parts[1]
        try:
            message = await c.get_messages(DB_CHANNEL_ID, int(msg_id))
            await message.delete()
            await m.message.edit("Dᴇʟᴇᴛᴇᴅ ғɪʟᴇs sᴜᴄᴄᴇssғᴜʟʟʏ Fʀᴏᴍ Dᴀᴛᴀʙᴀsᴇ👨‍✈️")
        except Exception as e:
            await m.message.edit(f"Fᴀɪʟᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ғɪʟᴇ: {e}")
