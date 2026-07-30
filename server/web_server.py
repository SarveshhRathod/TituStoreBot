import math
import mimetypes
import urllib.parse
import jinja2
from aiohttp import web
from pyrogram.file_id import FileId
from config import Server, DB_CHANNEL_ID
from database.database import get_downloads, increment_downloads
from server.byte_streamer import ByteStreamer, multi_clients, work_loads
from logger import logging

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()
class_cache = {}


def decode_id(base64_string: str) -> str:
    import base64
    base64_string = base64_string.strip()
    padding = '=' * (4 - len(base64_string) % 4) if len(base64_string) % 4 != 0 else ''
    base64_bytes = (base64_string + padding).replace('-', '+').replace('_', '/').encode("ascii")
    string_bytes = base64.b64decode(base64_bytes)
    return string_bytes.decode("ascii")


def humanbytes(size):
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    dic_power_n = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + dic_power_n[n] + 'B'


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response({
        "status": "running",
        "engine": "TituStoreBot Ultra-Fast aiohttp ByteStreamer",
        "url": Server.URL
    })


@routes.get("/stream/{path}", allow_head=True)
async def stream_page_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        decoded = decode_id(path)
        chat_id, msg_id = decoded.split("_")

        primary_client = multi_clients.get(0)
        msg = await primary_client.get_messages(DB_CHANNEL_ID, int(msg_id))
        if not msg or msg.empty:
            return web.HTTPNotFound(text="File not found")

        media = msg.document or msg.video or msg.audio
        file_name = getattr(media, "file_name", "Video_File")
        file_size = humanbytes(getattr(media, "file_size", 0))

        src = urllib.parse.urljoin(Server.URL, f'dl/{path}')

        with open("templates/play.html") as f:
            template = jinja2.Template(f.read())

        html_out = template.render(
            file_name=file_name,
            file_url=src,
            file_size=file_size
        )
        return web.Response(text=html_out, content_type='text/html')
    except Exception as e:
        logger.error(f"Stream Page Error: {e}")
        return web.HTTPInternalServerError(text=str(e))


@routes.get("/dl/{path}", allow_head=True)
async def media_streamer_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        decoded = decode_id(path)
        chat_id, msg_id = decoded.split("_")

        index = min(work_loads, key=work_loads.get) if work_loads else 0
        client = multi_clients.get(index, multi_clients.get(0))

        msg = await client.get_messages(DB_CHANNEL_ID, int(msg_id))
        if not msg or msg.empty:
            return web.HTTPNotFound(text="File not found")

        media = msg.document or msg.video or msg.audio
        file_size = getattr(media, "file_size", 0)
        file_name = getattr(media, "file_name", "Video.mp4")
        mime_type = getattr(media, "mime_type", "video/mp4") or "video/mp4"

        file_id_str = getattr(media, "file_id", "")
        file_id = FileId.decode(file_id_str)

        range_header = request.headers.get("Range", 0)
        if range_header:
            from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
            from_bytes = int(from_bytes)
            until_bytes = int(until_bytes) if until_bytes else file_size - 1
        else:
            from_bytes = request.http_range.start or 0
            until_bytes = (request.http_range.stop or file_size) - 1

        if (until_bytes >= file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
            return web.Response(
                status=416,
                body="416: Range not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"},
            )

        chunk_size = 1024 * 1024
        until_bytes = min(until_bytes, file_size - 1)

        offset = from_bytes - (from_bytes % chunk_size)
        first_part_cut = from_bytes - offset
        last_part_cut = until_bytes % chunk_size + 1

        req_length = until_bytes - from_bytes + 1
        part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)

        if client not in class_cache:
            class_cache[client] = ByteStreamer(client)
        tg_connect = class_cache[client]

        body = tg_connect.yield_file(
            file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
        )

        return web.Response(
            status=206 if range_header else 200,
            body=body,
            headers={
                "Content-Type": mime_type,
                "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
                "Content-Length": str(req_length),
                "Content-Disposition": f'inline; filename="{file_name}"',
                "Accept-Ranges": "bytes",
            },
        )
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        return web.HTTPInternalServerError(text=str(e))


def build_web_app():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
