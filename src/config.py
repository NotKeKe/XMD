from pathlib import Path
import tomllib
import json

BASE_DIR = Path(__file__).parent.parent

DATA_DIR = Path(BASE_DIR / "data")
DATA_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path(BASE_DIR / "static")
STATIC_DIR.mkdir(exist_ok=True)

TEMPLATES_DIR = Path(BASE_DIR / "templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

# load config
default_config_toml_text = '''
[twitter]
user_id = "YOUR_USER_ID"
bot_id = "YOUR_BOT_ID"

[discord]
bot_token = "YOUR_DISCORD_BOT_TOKEN"

[settings]
cookies_file = "./data/cookies.json"
# 圖片、影片儲存路徑
download_path = "./data/downloads"
# 日誌儲存路徑
log_path = "./logs"
# 資料庫儲存路徑
db_path = "./data/database.db"
# 是否只看 user_id 標記 bot_id 的推文，如果為 false，則會看所有標記 bot_id 的推文。 (true/false)
only_you = true

[components]
# TODO: 實作 true/false 的邏輯
fastapi = true
fastapi_host = "127.0.0.1"
fastapi_port = 8000
discord = true
'''.strip()

CONFIG_TOML = BASE_DIR / "config.toml"
if not CONFIG_TOML.exists():
    with open(CONFIG_TOML, "w", encoding="utf-8") as f:
        f.write(default_config_toml_text)

    print(f'已生成 config.toml，請填寫相關設定後再重新執行。 (檔案位於: "{CONFIG_TOML.resolve()}")')
    exit()

with open(CONFIG_TOML, "rb") as f:
    config = tomllib.load(f)

x_config = config.get('twitter', {})
settings = config.get('settings', {})
discord_config = config.get('discord', {})
components = config.get('components', {})

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
    
# path setting
DOWNLOAD_DIR = Path(settings.get('download_path', DATA_DIR / "downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path(settings.get('log_path', BASE_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(settings.get('db_path', DATA_DIR / "database.db"))
DB_PATH.mkdir(parents=True, exist_ok=True)

ONLY_WATCH_USER = settings.get('only_you', True)

# ---------- twitter ----------
X_USER_ID = x_config.get('user_id', '')
X_BOT_ID = x_config.get('bot_id', '')

# ---------- discord ----------
DISCORD_BOT_TOKEN = discord_config.get('bot_token', '')

# ---------- components ----------
FASTAPI_HOST = components.get('fastapi_host', '127.0.0.1')
FASTAPI_PORT = components.get('fastapi_port', 8000)
FASTAPI_ENABLED = components.get('fastapi', True)
DISCORD_ENABLED = components.get('discord', True)
