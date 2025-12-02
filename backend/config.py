import os

class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_FILE_SIZE_MB = 100
    MAX_DURATION_SEC = 180
    HISTORY_MAX_ITEMS = 7
    TEMP_FILE_EXPIRE_HOURS = 1
    SECRET_KEY = 'whisper_subtitle_secret_2025'