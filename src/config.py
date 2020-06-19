import os



class Config:
    DB_CONNECTION = os.getenv('DB_CONNECTION', 'db.sqlite')
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret').encode()
    JSON_SORT_KEYS = False

