# backend/api/upload.py
import os
import tempfile
from flask import Blueprint, request, jsonify
from backend.services.transcription import TranscriptionService
from backend.services.file_manager import FileManager
import threading

# ========== 核心修复：先定义Blueprint，再使用装饰器 ==========
upload_bp = Blueprint('upload', __name__)
transcription_service = TranscriptionService()

# 创建临时目录（确保存在）
TEMP_DIR = os.path.join(os.path.dirname(__file__), '../../temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# ========== 装饰器必须在Blueprint定义之后 ==========
@upload_bp.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "未选择文件"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "文件名不能为空"}), 400

        # 验证文件格式
        if not FileManager.validate_file(file.filename):
            supported = ','.join(FileManager.SUPPORTED_FORMATS)
            return jsonify({"error": f"不支持的文件格式！支持格式：{supported}"}), 400

        # 保存临时文件
        temp_file_path = os.path.join(TEMP_DIR, file.filename)
        file.save(temp_file_path)

        # 获取参数
        model = request.form.get("model", "tiny")
        language = request.form.get("language", "zh")
        task = request.form.get("task", "transcribe")
        device = request.form.get("device", "cpu")

        # 同步执行转录（确保task_id一致）
        trans_result = transcription_service.run_transcription_by_path(
            temp_file_path, 
            file.filename, 
            language, 
            task, 
            device
        )

        # 返回真实的task_id
        return jsonify({
            "task_id": trans_result["task_id"],
            "status": trans_result["status"]
        }), 200

    except Exception as e:
        print(f"上传接口错误：{str(e)}")
        return jsonify({"error": str(e)}), 500

@upload_bp.route("/api/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    try:
        from backend.models.whisper_engine import WhisperEngine
        whisper = WhisperEngine()
        progress_data = whisper.get_progress(task_id)
        return jsonify({
            "task_id": task_id,
            "progress": progress_data["progress"],
            "status": progress_data["status"]
        })
    except Exception as e:
        return jsonify({"progress": 0, "status": "failed", "error": str(e)}), 500

@upload_bp.route("/api/history", methods=["GET"])
def get_history():
    try:
        history = transcription_service.get_history()
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"history": [], "error": str(e)}), 500

@upload_bp.route("/api/download/<task_id>/<format_type>", methods=["GET"])
def download_file(task_id, format_type):
    try:
        content = transcription_service.get_task_result(task_id, format_type)
        if content is None:
            return jsonify({"error": "文件不存在"}), 404
        
        # 返回文件内容
        from flask import make_response
        response = make_response(content)
        # 设置响应头
        if format_type == "json":
            response.headers["Content-Type"] = "application/json; charset=utf-8"
            response.headers["Content-Disposition"] = f"attachment; filename={task_id}.json"
        else:
            response.headers["Content-Type"] = "text/plain; charset=utf-8"
            response.headers["Content-Disposition"] = f"attachment; filename={task_id}.{format_type}"
        
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500