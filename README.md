<h1 align="center">XMD (X Media Downloader)</h1>

<p align="center">
A Python-based <strong>X (Twitter) media downloader</strong> integrating a Discord bot and a Web interface.
</p>

<div align="center">

![Stars](https://img.shields.io/github/stars/NotKeKe/XMD?style=social)

[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE) <br>
[![Docs](https://img.shields.io/badge/Docs-繁體中文-blue.svg)](docs/README_zh-tw.md)
[![Docs](https://img.shields.io/badge/Docs-English-blue.svg)](README.md)

</div>

## 🖥️ Demo

- Discord Bot
<img src="docs/demo_discord.png" style="border-radius: 5px;">

- Web Interface
<img src="docs/demo_web_1.png" style="border-radius: 5px;">
<img src="docs/demo_web_2.png" style="border-radius: 5px;">

## 🌟 Features

- **Dual Modes: Automatic and Manual**
    - **Auto Download**: Set a Discord channel as a "Tweet Download Channel" via `/set_channel`. Any X links detected will be downloaded immediately.
    - **Manual Download**: Use the `/download` command to preview tweet content and choose specific media (or all) to download.
- **Multi-language Support (i18n)**
    - Discord commands support **Traditional Chinese**, **Simplified Chinese**, and **English**.
- **Web Frontend Management**
    - Built-in FastAPI-driven web service for easy searching and viewing of download history.

## 🛠️ Tech Stack

- Python 3.12
- FastAPI (Web interface)
- TypeScript (Web interface)
- Tailwind CSS (Web interface)
- SQLite3 (Database)
- The project's frontend is located in `frontend/`. Services for FastAPI and Discord are modularized in `src/services/`, with `main.py` inheriting from `src/abc.py`'s **ServicesABC**.

## 🚀 Usage

### 1. Prerequisites

- Python 3.12 or higher.
- Node.js installed.
- Recommended to use [uv](https://github.com/astral-sh/uv).

### 2. Download Project

```bash
git clone https://github.com/NotKeKe/XMD.git
cd XMD
```

### 3. Frontend Build

To save download time, the project does not provide pre-built frontend files. 
Please build the frontend yourself following these instructions:
1. Enter the `frontend` directory: `cd frontend`
2. Install dependencies: `npm install`
3. Execute build:
   - TypeScript: `npm run build`
   - CSS (Tailwind): `npm run build:css`

### 4. Configuration

- Modify your `config.toml`: [config.toml Introduction](#configtoml-description).
- Create a `data/` folder.
- Create `data/cookies.json`
    - Log in to X (Twitter) in your browser.
    - Get cookies (I use the [Cookie Editor](https://chromewebstore.google.com/detail/hlkenndednhfkekhgcdicdfddnkalmdm) extension in Chrome, but any method works).
    - Paste your **X (Twitter) Cookies** into `data/cookies.json`.
    - The format should look like this:
    ```json
    {
    	"auth_token": "",
    	"ct0": ""
        ... // Other cookie key-value pairs
    }
    ```

### 5. Run

- **Using uv (Recommended)**
    - Sync virtual environment: `uv sync`
    - Run program: `uv run main.py`

- **Using pip**
    - Install dependencies: `pip install -r requirements.txt`
    - Run program: `python main.py`

## 📜 Discord Command Description

- `/set_channel`: Toggle auto-download for the current channel.
- `/download <url>`: Parse and download media from a specific tweet URL.
- `/my_id`: Query your Discord User ID.
- `/help`: Show full command help message.

<div id="configtoml-description"></div>

## 📝 config.toml Explanation

- **First Start**
    - After the first run, a `config.toml` will be generated in the current directory, and the program will exit automatically.
- **services_open**
    - Pay attention to `services_open`. It includes options for `discord` and `fastapi`. At least one must be set to `true` for the project to run.
    - If you enable `discord`, make sure to fill in your **bot_token** in the `discord` configuration.
        - If you don't know how to create a Discord Bot, refer to [this guide](https://github.com/NotKeKe/TuneZ-Discord-Bot/blob/main/assets/docs/Register_Discord_Bot/Register_Discord_Bot.md).
- <strong>*_only_you</strong> (Crucial option, please read!!!):
    - (`*_only_you`, e.g., `x_only_you`, `discord_only_you`)
    - If you want the X or Discord bot to reply to everyone, set `*_only_you` to `false`.
    - **Risk**: Enabling replies for everyone carries a risk. Since media is downloaded directly to the local machine, it could be used for **malicious attacks** (e.g., multiple calls causing disk space depletion). If possible, **set *_only_you back to true immediately after setting your user_id**.
- **user_id**:
    - Both `twitter` and `discord` sections have a `user_id` field. The project defaults to only replying to "YOUR_USER_ID". Make sure to replace it with your own ID.
        - (You can find your Discord ID by right-clicking your avatar in Discord and selecting "Copy User ID", or by using the `/my_id` command after the bot is running.)

## Conclusion

**❗Please do not use this project for any purposes that infringe on others' copyrights or violate laws. I am not responsible for any misuse.❗**
- **If you find this project helpful, remember to give me a Star 🌟!**
- **If you use this tool in your project or redistribute it, please remember to credit the source or Tag me. Thanks for your support!**
- For bugs or suggestions, feel free to submit an [Issue](https://github.com/NotKeKe/XMD/issues).
