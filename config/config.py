import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

MYSQLHOST = str(os.getenv("HOST"))

MYSQLUSER = str(os.getenv("USER"))

MYSQLPASSWORD = str(os.getenv("PASSWORD"))

MYSQLDB = str(os.getenv("DB"))

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'

admins = [2040304896]
