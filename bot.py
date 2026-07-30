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

    # ------------------ PERMANENT FIX FOR PYROMOD 3.x ------------------
    # Pyromod 3.x expects app.listeners[listener_type] to be a DICT with .items()
    if not hasattr(app, "listeners") or not isinstance(app.listeners, dict):
        app.listeners = defaultdict(dict)
    else:
        new_listeners = defaultdict(dict)
        for k, v in app.listeners.items():
            if isinstance(v, dict):
                new_listeners[k] = v
        app.listeners = new_listeners
    # -------------------------------------------------------------------

    logger.info("TituStoreBot is starting...")
    keep_alive()
    app.run()

if __name__ == "__main__":
    main()
