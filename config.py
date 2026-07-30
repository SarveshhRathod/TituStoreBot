import os

# ---------------- Telegram Core ----------------
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

DB_CHANNEL_ID = os.environ.get("DB_CHANNEL_ID", "0")
if not DB_CHANNEL_ID or DB_CHANNEL_ID == "0":
    raise ValueError("DB_CHANNEL_ID is required. Add your database channel ID in environment variables.")
DB_CHANNEL_ID = int(DB_CHANNEL_ID)

OWNER_ID = int(os.environ.get("OWNER_ID", 0))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "").replace("@", "").strip()

# Strict boolean parsing
IS_PRIVATE = os.environ.get("IS_PRIVATE", "False").strip().lower() in ("true", "1", "yes")

AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "").split() if i.strip().isdigit()]
if OWNER_ID and OWNER_ID not in AUTH_USERS:
    AUTH_USERS.append(OWNER_ID)

# ---------------- Unlimited Multi-Database MongoDB ----------------
DB_NAME = os.environ.get("DB_NAME", "TituStoreBot")
MAX_DB_SIZE_MB = int(os.environ.get("MAX_DB_SIZE_MB", 470))


def _load_mongo_uris():
    uris = []
    first = os.environ.get("MONGO_URI")
    if first:
        uris.append(first.strip())

    index = 2
    while True:
        uri = os.environ.get(f"MONGO_URI{index}")
        if not uri:
            break
        uris.append(uri.strip())
        index += 1

    return uris


MONGO_URIS = _load_mongo_uris()
if not MONGO_URIS:
    raise ValueError(
        "No MongoDB URI found! Set at least MONGO_URI in your environment "
        "(add MONGO_URI2, MONGO_URI3, ... for unlimited extra storage)."
    )
