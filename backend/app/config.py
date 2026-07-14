import os

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "你的密码")
DB_NAME = os.getenv("DB_NAME", "weibo_system")

MODEL_PATH = r"D:\\CODE\\weibo-sentiment-system\\checkpoint-669"
BATCH_SIZE = 32

JWT_SECRET = os.getenv("JWT_SECRET", "replace-with-strong-secret")
JWT_ALG = "HS256"
ACCESS_TOKEN_MINUTES = 30

EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")