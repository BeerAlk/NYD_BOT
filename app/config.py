import os
from dotenv import load_dotenv

import os
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), ".env")
print(f"DEBUG: Путь к .env: {env_path}")
print(f"DEBUG: Файл .env существует: {os.path.isfile(env_path)}")

load_dotenv(dotenv_path=env_path)

API_TOKEN: str = os.getenv("API_TOKEN")
print(f"DEBUG: API_TOKEN = {API_TOKEN!r}")

MAIN_CHANNEL_ID: int = int(os.environ.get("MAIN_CHANNEL_ID", "-1000000000000"))
MAIN_CHANNEL_USERNAME: str = os.environ.get("MAIN_CHANNEL_USERNAME", "")
CLOSED_GROUP_CHAT: int = int(os.environ.get("CLOSED_GROUP_CHAT", "-1000000000000"))
CLOSED_CHANNEL_LINK: str = os.environ.get("CLOSED_CHANNEL_LINK", "")
ADMIN_ID: int = int(os.environ.get("ADMIN_ID", "0"))
ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "")

# MySQL Database URL (например, "mysql+aiomysql://user:password@host:port/dbname")
MYSQL_URL: str = os.environ.get("MYSQL_URL", "mysql+aiomysql://root:lKpKgFOmYyZploEFXowxwIntIHbAOsLp@switchback.proxy.rlwy.net:53604/railway")

# Web server
WEB_HOST: str = os.environ.get("WEB_HOST", "0.0.0.0")
WEB_PORT: int = int(os.environ.get("WEB_PORT", "8000"))
