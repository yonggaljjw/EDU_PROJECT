# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("MYSQL_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")  # ✅ 반드시 추가!!
