import os
import asyncio
from aiohttp import web
from pyrogram import Client, idle
from config import API_HASH, API_ID, BOT_TOKEN, Server
from server.web_server import build_web_app
from server.byte_streamer import multi_clients, work_loads
from logger import logging

logger = logging.getLogger(__name__)

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

    await main_client.start()
    bot_info = await main_client.get_me()
    logger.info(f"Main Bot Live: @{bot_info.username}")

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
            await extra_client.start()
            multi_clients[index] = extra_client
            work_loads[index] = 0
            logger.info(f"Multi-Client #{index} Active!")
        except Exception as e:
            logger.error(f"Failed starting Multi-Client #{index}: {e}")
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
