import pyromod  # Import pyromod before Client
from collections import defaultdict
from pyrogram import Client

from config import API_HASH, API_ID, BOT_TOKEN
from keep_alive import keep_alive
from logger import logging

logger = logging.getLogger(__name__)

def main():
    plugins = dict(root="plugins")
    app = Client(
        "TituStoreBot",
        bot_token=BOT_TOKEN,
        api_id=API_ID,
        api_hash=API_HASH,
        plugins=plugins,
        workers=100,
        sleep_threshold=15,
    )

    # ------------------ PERMANENT FIX FOR PYROMOD KEYERROR ------------------
    # Wrap app.listeners in a defaultdict so missing keys return [] instead of KeyError
    if not hasattr(app, "listeners") or app.listeners is None:
        app.listeners = defaultdict(list)
    elif isinstance(app.listeners, dict) and not isinstance(app.listeners, defaultdict):
        app.listeners = defaultdict(list, app.listeners)
    # -------------------------------------------------------------------------

    logger.info("TituStoreBot is starting...")
    keep_alive()
    app.run()

if __name__ == "__main__":
    main()
