import os
import asyncio
from aiohttp import web
from pyrogram import Client, idle
from pyrogram.errors import FloodWait
from config import API_HASH, API_ID, BOT_TOKEN, Server
from server.web_server import build_web_app
from server.byte_streamer import multi_clients, work_loads
from logger import logging

logger = logging.getLogger(__name__)


async def start_client_safe(client: Client, name: str = "Client"):
    while True:
        try:
            await client.start()
            bot_info = await client.get_me()
            logger.info(f"✅ {name} Live: @{bot_info.username}")
            return bot_info
        except FloodWait as e:
            logger.warning(f"⚠️ {name} got Telegram FloodWait of {e.value}s (~{max(1, e.value // 60)} min). Waiting before retrying...")
            await asyncio.sleep(e.value + 3)
        except Exception as e:
            logger.error(f"❌ Failed starting {name}: {e}")
            raise e


async def start_services():
    logger.info("Initializing Main Pyrogram Client...")
    main_client = Client(
        "TituStoreBot",
        bot_token=BOT_TOKEN,
        api_id=API_ID,
        api_hash=API_HASH,
        plugins=dict(root="plugins"),
        workers=100,
        sleep_threshold=15,
    )

    await start_client_safe(main_client, "Main Bot")

    multi_clients[0] = main_client
    work_loads[0] = 0

    index = 1
    while True:
        token = os.environ.get(f"MULTI_TOKEN{index}")
        if not token:
            break
        try:
            extra_client = Client(
                name=f"multi_{index}",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token.strip(),
                sleep_threshold=15,
                no_updates=True,
                in_memory=True,
            )
            await start_client_safe(extra_client, f"Multi-Client #{index}")
            multi_clients[index] = extra_client
            work_loads[index] = 0
        except Exception as e:
            logger.error(f"Skipping Multi-Client #{index}: {e}")
        index += 1

    logger.info(f"Starting aiohttp Web Server on {Server.BIND_ADDRESS}:{Server.PORT}...")
    app_runner = web.AppRunner(build_web_app())
    await app_runner.setup()
    await web.TCPSite(app_runner, Server.BIND_ADDRESS, Server.PORT).start()

    logger.info(f"🚀 TituStoreBot Fully Live at: {Server.URL}")
    await idle()
    await app_runner.cleanup()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
