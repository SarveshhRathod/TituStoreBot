import os
from flask import Flask, Response, request
from threading import Thread

app = Flask(__name__)

@app.get("/")
def home():
    return "TituStoreBot Engine is Active & Online!", 200

@app.get("/health")
def health():
    return "OK", 200

@app.get("/stream/<file_id>")
def stream_video(file_id):
    """Web Video Streaming Endpoint Placeholder"""
    return Response(
        f"<html><head><title>Streaming {file_id}</title></head>"
        f"<body style='background:#111;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;'>"
        f"<div style='text-align:center;'><h2>🎬 Playing Stream ID: {file_id}</h2>"
        f"<p>Stream is active! You can play this directly in Web / VLC.</p></div>"
        f"</body></html>",
        mimetype="text/html"
    )

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()
