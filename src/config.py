from pathlib import Path
import tomllib
import json

BASE_DIR = Path(__file__).parent.parent

DATA_DIR = Path(BASE_DIR / "data")
DATA_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path(BASE_DIR / "frontend" / "static")
STATIC_DIR.mkdir(exist_ok=True)

TEMPLATES_DIR = Path(BASE_DIR / "frontend" / "templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

# load config
default_config_toml_text = '''
[services_open]
# 組件開關
# TODO: 實作 true/false 的邏輯
fastapi = true
discord = true

[twitter]
# ----- 基礎配置 -----
user_id = "YOUR_USER_ID"
bot_id = "YOUR_BOT_ID"

# ----- services setting -----
# 是否只看 user_id 標記 bot_id 的推文，如果為 false，則會看所有標記 bot_id 的推文。 (true/false)
x_only_you = true

[discord]
# ----- 基礎配置 -----
bot_token = "YOUR_DISCORD_BOT_TOKEN"
user_id = "YOUR_DISCORD_USER_ID"

# ----- services setting -----
discord = true
discord_prefix = "=["
# 是否只接收來自 discord.user_id 的訊息
discord_only_you = true

[fastapi]
host = "127.0.0.1"
port = 8000

[settings]
cookies_file = "./data/cookies.json"
# 圖片、影片儲存路徑
download_path = "./data/downloads"
# 日誌儲存路徑
log_path = "./logs"
# 資料庫儲存路徑
db_path = "./data/database.db"
'''.strip()

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
    
# path setting
DOWNLOAD_DIR = Path(settings.get('download_path', DATA_DIR / "downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path(settings.get('log_path', BASE_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(settings.get('db_path', DATA_DIR / "database.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------- twitter ----------
X_USER_ID = x_config.get('user_id', '')
X_BOT_ID = x_config.get('bot_id', '')
X_ONLY_WATCH_USER = x_config.get('x_only_you', True)

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
