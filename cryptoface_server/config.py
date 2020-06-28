import os


class Config:
    ALLOWED_EXTENSIONS = ["jpg", "png"]
    DB_PATH = os.environ.get("DB_PATH", "./server/")
