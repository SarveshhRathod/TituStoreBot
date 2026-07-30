import os
import re
import queue
import asyncio
import base64
from flask import Flask, Response, request, render_template_string
from threading import Thread
from config import DB_CHANNEL_ID
from logger import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
pyro_client = None


def set_pyro_client(client):
    global pyro_client
    pyro_client = client


PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vidstream Fast - {{ title }}</title>
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: #0d0f12;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 15px;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            max-width: 900px;
            width: 100%;
        }
        .header h1 {
            font-size: 1.3rem;
            font-weight: 600;
            color: #4ade80;
            word-break: break-word;
            margin-bottom: 6px;
        }
        .header p {
            font-size: 0.85rem;
            color: #9ca3af;
        }
        .player-container {
            width: 100%;
            max-width: 900px;
            background: #16191e;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            border: 1px solid #2d323b;
        }
        video {
            width: 100%;
            max-height: 70vh;
            background: #000;
        }
        .actions {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-top: 20px;
            flex-wrap: wrap;
            max-width: 900px;
            width: 100%;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 8px;
            background: #2563eb;
            color: #fff;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: background 0.2s, transform 0.1s;
        }
        .btn:hover { background: #1d4ed8; transform: translateY(-1px); }
        .btn-vlc { background: #d97706; }
        .btn-vlc:hover { background: #b45309; }
        .footer {
            margin-top: 25px;
            font-size: 0.8rem;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 {{ title }}</h1>
        <p>📦 Size: {{ size }}</p>
    </div>

    <div class="player-container">
        <video id="player" controls playsinline crossorigin preload="auto">
            <source src="/watch/{{ file_id }}" type="{{ mime }}">
            Your browser does not support video playback.
        </video>
    </div>

    <div class="actions">
        <a href="/watch/{{ file_id }}" download="{{ title }}" class="btn">
            📥 Direct Fast Download
        </a>
        <a href="vlc://{{ stream_raw_url }}" class="btn btn-vlc">
            🍊 Play in VLC / MX Player
        </a>
    </div>

    <div class="footer">
        Powered by TituStoreBot Fast Vidstream Engine
    </div>

    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script>
        const player = new Plyr('#player', {
            controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'settings', 'pip', 'fullscreen'],
            settings: ['speed'],
            speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }
        });
    </script>
</body>
</html>
"""


def _decode_string(base64_string: str) -> str:
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


def _get_msg_safe(msg_id: int):
    res = pyro_client.get_messages(DB_CHANNEL_ID, msg_id)
    if asyncio.iscoroutine(res):
        return asyncio.run_coroutine_threadsafe(res, pyro_client.loop).result(timeout=10)
    return res


@app.get("/")
def home():
    return "TituStoreBot Ultra-Fast Vidstream Engine is Online!", 200


@app.get("/health")
def health():
    return "OK", 200


@app.get("/stream/<file_id>")
def stream_page(file_id):
    if not pyro_client:
        return "Bot client initializing... refresh in a few seconds.", 503

    try:
        decoded = _decode_string(file_id)
        chat_id, msg_id = decoded.split("_")

        msg = _get_msg_safe(int(msg_id))

        if not msg or msg.empty:
            return "File not found or deleted.", 404

        media = msg.document or msg.video or msg.audio
        title = getattr(media, "file_name", "Video_File")
        size = humanbytes(getattr(media, "file_size", 0))
        mime = getattr(media, "mime_type", "video/mp4") or "video/mp4"

        host_url = request.host_url.rstrip('/')
        stream_raw_url = f"{host_url}/watch/{file_id}"

        return render_template_string(
            PLAYER_TEMPLATE,
            title=title,
            size=size,
            mime=mime,
            file_id=file_id,
            stream_raw_url=stream_raw_url
        )
    except Exception as e:
        logger.error(f"Error rendering stream page: {e}")
        return f"Stream Error: {e}", 500


@app.get("/watch/<file_id>")
def watch_stream(file_id):
    if not pyro_client:
        return "Bot client offline.", 503

    try:
        decoded = _decode_string(file_id)
        chat_id, msg_id = decoded.split("_")

        msg = _get_msg_safe(int(msg_id))

        if not msg or msg.empty:
            return "File not found.", 404

        media = msg.document or msg.video or msg.audio
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "video/mp4") or "video/mp4"

        range_header = request.headers.get('Range', None)
        if not range_header:
            start = 0
            end = file_size - 1
            status_code = 200
        else:
            match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
            else:
                start = 0
                end = file_size - 1
            status_code = 206

        content_length = end - start + 1

        def fast_buffered_stream_generator():
            loop = pyro_client.loop
            chunk_queue = queue.Queue(maxsize=10)

            async def _fetch_chunks():
                try:
                    async for chunk in pyro_client.stream_media(msg, offset=start):
                        chunk_queue.put(chunk)
                    chunk_queue.put(None)
                except Exception as err:
                    logger.error(f"Async fetch chunk error: {err}")
                    chunk_queue.put(None)

            asyncio.run_coroutine_threadsafe(_fetch_chunks(), loop)

            while True:
                try:
                    chunk = chunk_queue.get(timeout=20)
                    if chunk is None:
                        break
                    yield chunk
                except Exception as e:
                    logger.error(f"Buffered queue read error: {e}")
                    break

        response = Response(
            fast_buffered_stream_generator(),
            status=status_code,
            mimetype=mime_type,
            direct_passthrough=True
        )
        response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        response.headers.add('Accept-Ranges', 'bytes')
        response.headers.add('Content-Length', str(content_length))
        response.headers.add('Cache-Control', 'public, max-age=31536000')
        return response

    except Exception as e:
        logger.error(f"Video watch error: {e}")
        return f"Streaming Exception: {e}", 500


def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    Thread(target=run, daemon=True).start()
