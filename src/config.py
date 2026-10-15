from pathlib import Path
import tomllib
import json
import os

# twscrape 預設會送出匿名 telemetry (含機器指紋)，這是自架工具，預設關閉。
# 必須在 import twscrape 之前設定，所以放在 config 模組最上層。
os.environ.setdefault("TWS_TELEMETRY", "0")
# twscrape 的 loguru 等級；實際輸出由 src/services/twitter/utils.py 的橋接轉到本專案的 logging。
os.environ.setdefault("TWS_LOG_LEVEL", "INFO")

BASE_DIR = Path(__file__).parent.parent

DATA_DIR = Path(BASE_DIR / "data")
DATA_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path(BASE_DIR / "frontend" / "static")
STATIC_DIR.mkdir(exist_ok=True)

TEMPLATES_DIR = Path(BASE_DIR / "frontend" / "templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

# load config
with open(BASE_DIR / 'config.toml.example', 'r', encoding='utf-8') as f:
    default_config_toml_text = f.read().strip()

CONFIG_TOML = BASE_DIR / "config.toml"
if not CONFIG_TOML.exists():
    with open(CONFIG_TOML, "w", encoding="utf-8") as f:
        f.write(default_config_toml_text)

    print(f'已生成 config.toml，請填寫相關設定後再重新執行。 (檔案位於: "{CONFIG_TOML.resolve()}")')
    exit()

with open(CONFIG_TOML, "rb") as f:
    config = tomllib.load(f)

services_open = config.get('services_open', {})
x_config = config.get('twitter', {})
discord_config = config.get('discord', {})
fastapi_config = config.get('fastapi', {})
settings = config.get('settings', {})

# ---------- settings ----------
# load cookies
COOKIES_FILE = Path(settings.get('cookies_file', DATA_DIR / "cookies.json"))
if not COOKIES_FILE.exists():
    raise FileNotFoundError("Cookies file not found")

with open(COOKIES_FILE, "r", encoding="utf-8") as f:
    COOKIES = json.load(f)

if not COOKIES:
    raise ValueError("Cookies file is empty")
elif not isinstance(COOKIES, dict):
    raise ValueError("Cookies file must be a dictionary")

# twscrape 的 cookie 登入硬性要求這兩個值 (has_required_cookies)，
# 缺少任何一個，帳號池就永遠不會有 active 帳號，所以這裡先擋下來並說清楚原因。
missing_cookies = [k for k in ("auth_token", "ct0") if not COOKIES.get(k)]
if missing_cookies:
    raise ValueError(
        f"Cookies file is missing required keys: {', '.join(missing_cookies)} "
        f"(twscrape needs auth_token and ct0 to log in). File: {COOKIES_FILE}"
    )


# path setting
DOWNLOAD_DIR = Path(settings.get('download_path', DATA_DIR / "downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path(settings.get('log_path', BASE_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(settings.get('db_path', DATA_DIR / "database.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# twscrape 帳號池 (登入 session 存在這個 SQLite 裡) 與帳號在本機的識別名稱
ACCOUNTS_DB = Path(settings.get('accounts_db', DATA_DIR / "accounts.db"))
ACCOUNTS_DB.parent.mkdir(parents=True, exist_ok=True)
X_ACCOUNT_NAME = str(settings.get('account_name', 'xmd'))

# ---------- twitter ----------
X_USER_ID = x_config.get('user_id', '')
X_BOT_ID = x_config.get('bot_id', '')
X_ONLY_WATCH_USER = x_config.get('x_only_you', True)
# twscrape 的 search() limit 必須給，預設 -1 會無限翻頁
X_SEARCH_LIMIT = int(x_config.get('search_limit', 20))
# 所有帳號都被限流/鎖定時，最多等幾秒才放棄這一輪 (twscrape 預設是無限期等待)
X_WAIT_TIMEOUT = float(x_config.get('wait_timeout', 300))

# ---------- discord ----------
DISCORD_BOT_TOKEN = discord_config.get('bot_token', '')
DISCORD_USER_ID = discord_config.get('user_id', '').strip()
DISCORD_PREFIX = discord_config.get('discord_prefix', '=[')
DISCORD_ONLY_YOU = discord_config.get('discord_only_you', True)
DISCORD_I18N_JSON_DIR = BASE_DIR / 'src/services/discord/core/locales'

# ---------- fastapi ----------
FASTAPI_HOST = fastapi_config.get('host', '127.0.0.1')
try:
    FASTAPI_PORT = int(fastapi_config.get('port', 8000))
except:
    print('fastapi, port 被設置為非 int 的物件，請更改配置後重新嘗試。')
    exit(1)

# ---------- services_open ----------
FASTAPI_ENABLED = services_open.get('fastapi', True)
DISCORD_ENABLED = services_open.get('discord', True)
