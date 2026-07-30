from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import AUTH_USERS, OWNER_ID
from database.database import get_db_status, get_settings, update_settings
from logger import logging

logger = logging.getLogger(__name__)


async def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID or user_id in AUTH_USERS:
        return True
    settings = await get_settings()
    return user_id in settings.get("moderators", [])


async def _panel_view():
    settings = await get_settings()
    auto_delete_on = settings.get("auto_delete", False)
    auto_delete_min = settings.get("auto_delete_seconds", 600) // 60
    protect_on = settings.get("protect_content", False)
    caption_set = "Custom Set ✅" if settings.get("custom_caption") else "Default ❌"
    watermark = settings.get("watermark", "None")
    mods_count = len(settings.get("moderators", []))

    text = (
        "⚙️ **ADMIN & MODERATOR CONTROL PANEL**\n\n"
        f"🗑 **Auto-Delete:** {'✅ ON — ' + str(auto_delete_min) + ' min' if auto_delete_on else '❌ OFF'}\n"
        f"🔒 **Protect Content:** {'✅ ON' if protect_on else '❌ OFF'}\n"
        f"📝 **Custom Caption:** `{caption_set}`\n"
        f"🏷 **Watermark Text:** `{watermark}`\n"
        f"👥 **Moderators Count:** `{mods_count}`\n"
    )

    buttons = [
        [InlineKeyboardButton(
            f"🗑 Auto-Delete: {'ON (' + str(auto_delete_min) + 'm) ✅' if auto_delete_on else 'OFF ❌'}",
            callback_data="adm_autodel_menu"
        )],
        [InlineKeyboardButton(
            f"🔒 Protect Content: {'ON ✅' if protect_on else 'OFF ❌'}",
            callback_data="adm_toggle_protect"
        )],
        [InlineKeyboardButton("📝 Set Caption Template", callback_data="adm_info_caption")],
        [InlineKeyboardButton("🏷 Set Watermark Text", callback_data="adm_info_watermark")],
        [InlineKeyboardButton("📊 DATABASE STATUS", callback_data="adm_dbstats")],
        [InlineKeyboardButton("CLOSE 🔐", callback_data="adm_close")],
    ]
    return text, InlineKeyboardMarkup(buttons)


@Client.on_message(filters.command(["admin", "panel"]) & filters.private & filters.incoming)
async def admin_panel(c, m):
    if not await is_admin(m.from_user.id):
        return await m.reply_text("🚫 Yʜ Cᴏᴍᴍᴀɴᴅ Sɪʀғ Bᴏᴛ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ Hᴀɪ.", quote=True)

    text, markup = await _panel_view()
    await m.reply_text(text, reply_markup=markup, quote=True)


# Auto Delete Menu
@Client.on_callback_query(filters.regex("^adm_autodel_menu$"))
async def autodel_menu(c, m):
    if not await is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    await m.answer()
    buttons = [
        [
            InlineKeyboardButton("5 Min ⏱", callback_data="adm_set_autodel_300"),
            InlineKeyboardButton("10 Min ⏱", callback_data="adm_set_autodel_600"),
            InlineKeyboardButton("15 Min ⏱", callback_data="adm_set_autodel_900"),
        ],
        [
            InlineKeyboardButton("30 Min ⏱", callback_data="adm_set_autodel_1800"),
            InlineKeyboardButton("1 Hour ⏱", callback_data="adm_set_autodel_3600"),
            InlineKeyboardButton("2 Hours ⏱", callback_data="adm_set_autodel_7200"),
        ],
        [InlineKeyboardButton("Disable Auto-Delete ❌", callback_data="adm_set_autodel_0")],
        [InlineKeyboardButton("🔙 Back to Panel", callback_data="adm_back")]
    ]
    await m.message.edit(
        "⏱ **Select Auto-Delete Timer:**\n\nChoose how long files remain before being automatically deleted:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^adm_set_autodel_"))
async def set_autodel(c, m):
    if not await is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    seconds = int(m.data.split("_")[3])
    if seconds == 0:
        await update_settings(auto_delete=False)
        await m.answer("❌ Auto-Delete Disabled!", show_alert=True)
    else:
        minutes = seconds // 60
        await update_settings(auto_delete=True, auto_delete_seconds=seconds)
        await m.answer(f"✅ Auto-Delete set to {minutes} minutes!", show_alert=True)

    text, markup = await _panel_view()
    await m.message.edit(text, reply_markup=markup)


# Protect Content Toggle
@Client.on_callback_query(filters.regex("^adm_toggle_protect$"))
async def toggle_protect(c, m):
    if not await is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    settings = await get_settings()
    new_state = not settings.get("protect_content", False)
    await update_settings(protect_content=new_state)
    await m.answer(f"🔒 Protect Content {'ON ✅' if new_state else 'OFF ❌'}!", show_alert=True)

    text, markup = await _panel_view()
    await m.message.edit(text, reply_markup=markup)


# Caption Info
@Client.on_callback_query(filters.regex("^adm_info_caption$"))
async def info_caption(c, m):
    await m.answer()
    settings = await get_settings()
    curr = settings.get("custom_caption", "Default Caption (None)")

    buttons = [
        [InlineKeyboardButton("Reset Caption to Default 🔄", callback_data="adm_reset_caption")],
        [InlineKeyboardButton("🔙 Back to Panel", callback_data="adm_back")]
    ]
    msg_text = (
        "📝 **CUSTOM CAPTION CONFIGURATION**\n\n"
        f"**Current Template:**\n`{curr}`\n\n"
        "**How to set a custom caption?**\n"
        "Send command:\n`/setcaption Your Custom Template Here`\n\n"
        "**Available Placeholders:**\n"
        "`{file_name}` - File Name\n"
        "`{file_size}` - File Size\n"
        "`{uploader}` - Uploader Mention\n"
        "`{downloads}` - Download Count"
    )
    await m.message.edit(msg_text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^adm_reset_caption$"))
async def reset_caption_cb(c, m):
    if not await is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    await update_settings(custom_caption="")
    await m.answer("✅ Custom Caption reset to default!", show_alert=True)
    text, markup = await _panel_view()
    await m.message.edit(text, reply_markup=markup)


# Watermark Info
@Client.on_callback_query(filters.regex("^adm_info_watermark$"))
async def info_watermark(c, m):
    await m.answer()
    settings = await get_settings()
    curr = settings.get("watermark", "None")

    buttons = [
        [InlineKeyboardButton("Remove Watermark ❌", callback_data="adm_remove_watermark")],
        [InlineKeyboardButton("🔙 Back to Panel", callback_data="adm_back")]
    ]
    msg_text = (
        "🏷 **WATERMARK TEXT CONFIGURATION**\n\n"
        f"**Current Watermark:** `{curr}`\n\n"
        "**How to set a custom watermark?**\n"
        "Send command:\n`/setwatermark @YourChannelName`"
    )
    await m.message.edit(msg_text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^adm_remove_watermark$"))
async def remove_watermark_cb(c, m):
    if not await is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    await update_settings(watermark="")
    await m.answer("✅ Watermark Removed!", show_alert=True)
    text, markup = await _panel_view()
    await m.message.edit(text, reply_markup=markup)


@Client.on_callback_query(filters.regex("^adm_dbstats$"))
async def adm_dbstats(c, m):
    if not await is_admin(m.from_user.id):
        return await m.answer("🚫 Sɪʀғ Aᴅᴍɪɴ Kᴇ Lɪʏᴇ.", show_alert=True)

    await m.answer()
    status = await get_db_status()
    text = "**🗄 MULTI-DATABASE STATUS:**\n\n"
    for s in status:
        marker = "🟢 ACTIVE" if s["active"] else "⚪️ STANDBY"
        text += f"**DB #{s['index']}** — {s['size_mb']} / {s['limit_mb']} MB — {marker}\n"

    buttons = [[InlineKeyboardButton("🔙 Back to Panel", callback_data="adm_back")]]
    await m.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^adm_back$"))
async def adm_back(c, m):
    await m.answer()
    text, markup = await _panel_view()
    await m.message.edit(text, reply_markup=markup)


@Client.on_callback_query(filters.regex("^adm_close$"))
async def adm_close(c, m):
    await m.message.delete()
