from pyrogram import Client
from config import API_HASH, API_ID, BOT_TOKEN
from keep_alive import keep_alive, set_pyro_client
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

    logger.info("TituStoreBot is starting...")
    set_pyro_client(app)
    keep_alive()
    app.run()

if __name__ == "__main__":
    main()
