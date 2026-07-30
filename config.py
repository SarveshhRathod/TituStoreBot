import os
from dotenv import load_dotenv

load_dotenv()

# Top-level environment variables
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

DB_CHANNEL_ID = os.environ.get("DB_CHANNEL_ID", "0")
if not DB_CHANNEL_ID or DB_CHANNEL_ID == "0":
    raise ValueError("DB_CHANNEL_ID is required. Add your database channel ID in environment variables.")
DB_CHANNEL_ID = int(DB_CHANNEL_ID)

OWNER_ID = int(os.environ.get("OWNER_ID", 0))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "").replace("@", "").strip()

IS_PRIVATE = os.environ.get("IS_PRIVATE", "False").strip().lower() in ("true", "1", "yes")

AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "").split() if i.strip().isdigit()]
if OWNER_ID and OWNER_ID not in AUTH_USERS:
    AUTH_USERS.append(OWNER_ID)

RATE_LIMIT_PER_MIN = int(os.environ.get("RATE_LIMIT_PER_MIN", 10))

DB_NAME = os.environ.get("DB_NAME", "TituStoreBot")
MAX_DB_SIZE_MB = int(os.environ.get("MAX_DB_SIZE_MB", 460))


def _load_mongo_uris():
    uris = []
    first = os.environ.get("MONGO_URI") or os.environ.get("DATABASE_URL")
    if first:
        uris.append(first.strip())

    index = 2
    while True:
        uri = os.environ.get(f"MONGO_URI{index}") or os.environ.get(f"DATABASE_URL_{index}")
        if not uri:
            break
        uris.append(uri.strip())
        index += 1

    return uris


MONGO_URIS = _load_mongo_uris()
if not MONGO_URIS:
    raise ValueError("No MongoDB URI found! Set MONGO_URI or DATABASE_URL in environment.")


class Telegram:
    API_ID = API_ID
    API_HASH = API_HASH
    BOT_TOKEN = BOT_TOKEN
    OWNER_ID = OWNER_ID
    DB_CHANNEL_ID = DB_CHANNEL_ID
    UPDATE_CHANNEL = UPDATE_CHANNEL
    IS_PRIVATE = IS_PRIVATE
    AUTH_USERS = AUTH_USERS


def _detect_fqdn():
    manual = os.environ.get("FQDN")
    if manual:
        return manual, True

    port = os.environ.get("PORT", "8080")
    codespace = os.environ.get("CODESPACE_NAME")
    platform_candidates = (
        os.environ.get("RENDER_EXTERNAL_HOSTNAME"),
        os.environ.get("KOYEB_PUBLIC_DOMAIN"),
        os.environ.get("RAILWAY_PUBLIC_DOMAIN"),
        (os.environ.get("FLY_APP_NAME") + ".fly.dev") if os.environ.get("FLY_APP_NAME") else None,
        (os.environ.get("HEROKU_APP_NAME") + ".herokuapp.com") if os.environ.get("HEROKU_APP_NAME") else None,
        (f"{codespace}-{port}.app.github.dev") if codespace else None,
    )
    for host in platform_candidates:
        if host:
            return host, True

    try:
        import requests
        resp = requests.get("https://api.ipify.org", timeout=5)
        if resp.ok and resp.text.strip():
            return resp.text.strip(), False
    except Exception:
        pass

    return str(os.environ.get("BIND_ADDRESS", "0.0.0.0")), False


class Server:
    PORT = int(os.environ.get("PORT", 8080))
    BIND_ADDRESS = str(os.environ.get("BIND_ADDRESS", "0.0.0.0"))
    FQDN, _IS_PLATFORM_DOMAIN = _detect_fqdn()

    _has_ssl_env = os.environ.get("HAS_SSL")
    HAS_SSL = (
        str(_has_ssl_env).lower() in ("1", "true", "t", "yes", "y")
        if _has_ssl_env is not None else _IS_PLATFORM_DOMAIN
    )
    _no_port_env = os.environ.get("NO_PORT")
    NO_PORT = (
        str(_no_port_env).lower() in ("1", "true", "t", "yes", "y")
        if _no_port_env is not None else _IS_PLATFORM_DOMAIN
    )

    URL = "http{}://{}{}/".format(
        "s" if HAS_SSL else "", FQDN, "" if NO_PORT else ":" + str(PORT)
    )
