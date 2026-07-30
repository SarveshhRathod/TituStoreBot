import pyromod  # MUST be imported before Client
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

    # Safe patch to prevent Pyromod KeyError
    if hasattr(app, "listeners") and isinstance(app.listeners, dict):
        try:
            from pyromod.listen.listen import ListenerTypes
            for l_type in ListenerTypes:
                if l_type not in app.listeners:
                    app.listeners[l_type] = []
        except Exception:
            pass

    logger.info("TituStoreBot is starting...")
    keep_alive()
    app.run()

if __name__ == "__main__":
    main()
