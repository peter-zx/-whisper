# backend/api/upload.py
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from backend.config import UPLOAD_FOLDER
from backend.services.file_manager import FileManager
from backend.services.transcription import generate_subtitle_formats, save_history
from backend.models.whisper_engine import WhisperEngine

upload_bp = Blueprint('upload', __name__)

# 全局引擎（启动时加载一次）
engine = WhisperEngine("tiny")

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # 转 WAV
    if not FileManager.is_wav(filepath):
        filepath = FileManager.convert_to_wav(filepath)

    # 转录（强制中文）
    result = engine.transcribe(filepath, language="zh")

    # 保存
    base_name = save_history(result, filename)
    formats = generate_subtitle_formats(result, base_name)

    return jsonify({
        "text": result["text"],
        "segments": result["segments"],
        "filename_base": os.path.basename(base_name),
        "available_formats": formats
    })