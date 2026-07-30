from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import AUTH_USERS, OWNER_ID
from database.database import get_db_status, get_settings, update_settings
from logger import logging

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in AUTH_USERS


async def _panel_view():
    settings = await get_settings()
    auto_delete_on = settings.get("auto_delete", False)
    auto_delete_min = settings.get("auto_delete_seconds", 600) // 60
    protect_on = settings.get("protect_content", False)

    text = (
        "**⚙️ Aᴅᴍɪɴ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**\n\n"
        "Yᴀʜᴀɴ sᴇ ʙᴏᴛ ᴋᴇ ғᴇᴀᴛᴜʀᴇs ᴅɪʀᴇᴄᴛ ᴏɴ/ᴏғғ ᴋᴀʀᴏ 👇\n\n"
        f"🗑 **Auto-Delete:** {'✅ ON — ' + str(auto_delete_min) + ' min' if auto_delete_on else '❌ OFF'}\n"
        f"🔒 **Protect Content (No-Forward):** {'✅ ON' if protect_on else '❌ OFF'}\n"
    )

    buttons = [
        [InlineKeyboardButton(
            f"🗑 Auto-Delete: {'ON ✅' if auto_delete_on else 'OFF ❌'}",
            callback_data="adm_toggle_autodelete"
        )],
        [InlineKeyboardButton(
            f"🔒 Protect Content: {'ON ✅' if protect_on else 'OFF ❌'}",
            callback_data="adm_toggle_protect"
        )],
        [InlineKeyboardButton("📊 Dᴀᴛᴀʙᴀsᴇ Sᴛᴀᴛᴜs", callback_data="adm_dbstats")],
        [InlineKeyboardButton("Cʟᴏsᴇ 🔐", callback_data="adm_close")],
    ]
    return text, InlineKeyboardMarkup(buttons)


@Client.on_message(filters.command(["admin", "panel"]) & filters.private & filters.incoming)
async def admin_panel(c, m):
    if not is_admin(m.from_user.id):
        return await m.reply_text("🚫 Yʜ Cᴏᴍᴍᴀɴᴅ Sɪʀғ Bᴏᴛ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ Hᴀɪ.", quote=True)

    text, markup = await _panel_view()
    await m.reply_text(text, reply_markup=markup, quote=True)


@Client.on_callback_query(filters.regex("^adm_toggle_autodelete$"))
async def toggle_autodelete(c, m):
    if not is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    settings = await get_settings()

    if settings.get("auto_delete", False):
        await update_settings(auto_delete=False)
        await m.answer("❌ Auto-Delete OFF ᴋᴀʀ ᴅɪʏᴀ ɢᴀʏᴀ.", show_alert=True)
    else:
        await m.answer()
        try:
            ask_msg = await c.ask(
                chat_id=m.from_user.id,
                text="⏱ Kɪᴛɴᴇ **minutes** ʙᴀᴀᴅ ғɪʟᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏɴɪ ᴄʜᴀʜɪʏᴇ?\n__(sɪʀғ number ʙʜᴇᴊᴏ, ᴊᴀɪsᴇ__ `30` __)__",
                timeout=60
            )
        except Exception:
            return await c.send_message(m.from_user.id, "⌛ Tɪᴍᴇ Oᴜᴛ. Vᴀᴘᴀs `/admin` sᴇ ᴛʀʏ ᴋᴀʀᴏ.")

        try:
            minutes = int(ask_msg.text.strip())
            if minutes <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            return await ask_msg.reply_text("⚠️ Gᴀʟᴀᴛ Vᴀʟᴜᴇ. Vᴀᴘᴀs `/admin` sᴇ ᴛʀʏ ᴋᴀʀᴏ.")

        await update_settings(auto_delete=True, auto_delete_seconds=minutes * 60)
        await ask_msg.reply_text(f"✅ **Auto-Delete ON** — Fɪʟᴇs ᴀʙ **{minutes} minute(s)** ʙᴀᴀᴅ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ʜᴏɴɢɪ.")

    text, markup = await _panel_view()
    try:
        await m.message.edit(text, reply_markup=markup)
    except Exception:
        pass


@Client.on_callback_query(filters.regex("^adm_toggle_protect$"))
async def toggle_protect(c, m):
    if not is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    settings = await get_settings()
    new_state = not settings.get("protect_content", False)
    await update_settings(protect_content=new_state)
    await m.answer(f"🔒 Protect Content {'ON ✅' if new_state else 'OFF ❌'} ᴋᴀʀ ᴅɪʏᴀ ɢᴀʏᴀ.", show_alert=True)

    text, markup = await _panel_view()
    await m.message.edit(text, reply_markup=markup)


@Client.on_callback_query(filters.regex("^adm_dbstats$"))
async def adm_dbstats(c, m):
    if not is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    await m.answer()
    status = await get_db_status()
    text = "**🗄 Mᴜʟᴛɪ-Dᴀᴛᴀʙᴀsᴇ Sᴛᴀᴛᴜs:**\n\n"
    for s in status:
        marker = "🟢 ᴀᴄᴛɪᴠᴇ" if s["active"] else "⚪️ sᴛᴀɴᴅʙʏ"
        text += f"**DB #{s['index']}** — {s['size_mb']} / {s['limit_mb']} MB — {marker}\n"

    await m.message.reply_text(text)


@Client.on_callback_query(filters.regex("^adm_close$"))
async def adm_close(c, m):
    await m.message.delete()
