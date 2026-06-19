import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com")
DATABASE_PATH = os.getenv("DATABASE_PATH", "zooboom.db")
