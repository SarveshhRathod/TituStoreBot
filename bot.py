from logger import logging

from pyromod import listen
from pyrogram import Client

from config import API_HASH, API_ID, BOT_TOKEN

logger = logging.getLogger(__name__)


def main():
    plugins = dict(root="plugins")
    app = Client(
        "TituStoreBot",
        bot_token=BOT_TOKEN,
        api_id=API_ID,
        api_hash=API_HASH,
        plugins=plugins,
        workers=200,
        sleep_threshold=15,
    )

    logger.info("TituStoreBot is starting...")
    app.run()


if __name__ == "__main__":
    main()
