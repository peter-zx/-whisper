import os
from pathlib import Path

# 项目根目录（基于当前文件路径）
BASE_DIR = Path(__file__).resolve().parent.parent

# 核心目录配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
HISTORY_FOLDER = os.path.join(BASE_DIR, "uploads")  # 对齐你的uploads目录
RESULT_FOLDER = HISTORY_FOLDER  # 补充缺失的变量
HISTORY_MAX_ITEMS = 7

# FFmpeg路径（Windows），Linux/Mac注释此行
FFMPEG_PATH = r"E:\ai_work\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

# Flask配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Whisper模型配置（默认改为tiny，最小模型）
DEFAULT_MODEL = "tiny"  # 核心修改：从turbo改为tiny
SUPPORTED_FORMATS = ["srt", "txt", "vtt", "json"]
SUPPORTED_AUDIO_EXT = [".mp3", ".wav", ".flac", ".m4a", ".mp4", ".avi", ".mov"]

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)