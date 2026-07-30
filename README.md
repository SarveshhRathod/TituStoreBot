<h1 align="center">TituStoreBot</h1>
<p align="center">

  <p align="center">
    <i>A Telegram bot that stores your files and gives a Permanent Shareable Link — supports Private & Public use, with unlimited multi-database MongoDB storage.</i>
    <br />
   </strong></a>
    <br />
    <a href="https://github.com/SarveshhRathod/TituStoreBot/issues"><b>Report a Bug</b></a>
    |
    <a href="https://github.com/SarveshhRathod/TituStoreBot/issues"><b>Request Feature</b></a>
  </p>
</p>


<p align="center">
    <a href="https://github.com/SarveshhRathod/TituStoreBot">
        <img src="https://i.ibb.co/R2cswyL/folder.png" height="80" width="80" alt="TituStoreBot Logo">
    </a>
</p><b>



### 🍁 Features :

- In PM just forward or send any file — it gets saved and you receive a permanent shareable link.
- In a Channel: add the bot as Admin (with Edit rights). Any file/media posted there automatically gets a share link button.
- Optional Force-Subscribe to a channel before users can use the bot.
- Private mode, restricted to specific Auth Users / Channels.
- **Unlimited Multi-Database Storage** — add as many `MONGO_URI` values as you want. The bot automatically fills one MongoDB database and moves to the next once it's full, so you're never blocked by a single free-tier 512MB limit.
- Fully async database layer (MongoDB via `motor`) — no more blocking calls freezing the bot, meaning noticeably faster response times.
- **Admin Control Panel (`/admin`)** — button-based menu, auto-detects Owner/Auth Users (no extra config). Toggle features live, no restart needed:
  - 🗑 **Auto-Delete** — turn ON and the bot asks "kitne minutes baad delete karna hai?", then confirms with the exact time; delivered files auto-delete after that.
  - 🔒 **Protect Content** — one tap to stop delivered files from being forwarded/saved.
  - 📊 **Database Status** — live view of how full each connected MongoDB database is.
  - All settings persist in MongoDB, so they survive bot restarts.

<br>

## Heroku Deploy :
_Press the button, deploy to Heroku and fill in the config vars. 👇_

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)


## VPS Deploy :

```py
git clone https://github.com/SarveshhRathod/TituStoreBot
cd TituStoreBot
pip3 install -r requirements.txt
# <Create config.py appropriately, or set the environment variables below>
python3 bot.py
```
<br>

### Configs :

**This is a telegram bot that helps you store files and get a shareable permanent link.**

- `API_ID` & `API_HASH:` _Get these values from [my.telegram.org](https://my.telegram.org)._

- `BOT_TOKEN:` _Get the bot token from [Bot Father](https://telegram.dog/BotFather)_

- `DB_CHANNEL_ID:` _Your telegram channel id, e.g. `-100716464000` (required — the bot forwards files here)_

- `OWNER_ID:` _Get your user id from [MissRose](https://telegram.dog/MissRose_bot)_

- `MONGO_URI:` _Your MongoDB connection string (get a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas))_

- `MONGO_URI2`, `MONGO_URI3`, `MONGO_URI4` ... _(optional)_ _Add as many extra MongoDB URIs as you like. Once `MONGO_URI` gets close to full, the bot automatically starts writing new data to `MONGO_URI2`, then `MONGO_URI3`, and so on — giving you effectively **unlimited** storage by stacking free-tier clusters._

- `MAX_DB_SIZE_MB:` _(optional, default `470`)_ _Threshold at which the bot switches to the next database._

- `UPDATE_CHANNEL:` _Your updates channel username, without `@` (optional — leave empty to disable force-sub)_

- `IS_PRIVATE:` _Set to `True` to restrict bot usage to `AUTH_USERS` only_

- `AUTH_USERS:` _Space separated user/channel IDs (only used if `IS_PRIVATE` is `True`)_

<br>

 _👉🏻👉🏻 The bot must be added as **Admin** in the `DB_CHANNEL` (and in `UPDATE_CHANNEL` if you use force-sub)_

  <br>

### Commands :

```
start - Check Bot is Alive !
help - Get More Help About Bot
about - Know Something More About Bot
me - Get Information About Yourself
batch - Send media / files in batch mode
mode - Toggle uploader-details caption
admin - (Admin only) Open the Control Panel — toggle Auto-Delete, Protect Content, view DB status
```

<br>

### 💡 Ideas for the next upgrade

Some directions worth exploring for a future release:

- **Inline search** — `@YourBot query` to search previously stored files without opening the chat.
- **Broadcast & stats panel** — owner command to message every user, plus total users/files/storage-per-DB dashboard, all from `/admin`.
- **Multiple Force-Sub channels** — require joining 2–3 channels instead of just one, toggleable from `/admin`.
- **Token / shortlink verification** — optional monetization layer before a file link unlocks.
- **Custom rename before delivery** — let users rename a file before it's sent to them.
- **Scheduled backups** — periodic export of the settings DB so a database mix-up never loses data.
- **Webhook mode** — swap long-polling for webhooks on platforms that support it, for lower latency.
- **Per-file expiry / view limits** — auto-delete from the DB channel after X downloads or X days.

<br>
<h5 align='center'>© 2026 Sarveshh Rathod (Titu)</h5>
