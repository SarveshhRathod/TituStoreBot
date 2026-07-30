import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.get("/")
def home():
    return "TituStoreBot is running smoothly!", 200

@app.get("/health")
def health():
    return "OK", 200

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()
