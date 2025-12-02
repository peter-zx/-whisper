from flask import Blueprint, send_file, jsonify
from backend.services.transcription import TranscriptionService
import os

download_bp = Blueprint("download", __name__)
transcription_service = TranscriptionService()

@download_bp.route("/api/download/<task_id>/<format>", methods=["GET"])
def download_subtitle(task_id, format):
    """下载指定格式的字幕文件"""
    # 验证格式
    if format not in ["srt", "txt", "vtt", "json"]:
        return jsonify({"error": "不支持的格式"}), 400

    # 获取文件路径
    task_data = transcription_service.task_map.get(task_id)
    if not task_data or task_data["status"] != "completed":
        # 从历史文件中查找
        history_file = os.path.join(transcription_service.HISTORY_FOLDER, f"{task_id}.json")
        if os.path.exists(history_file):
            import json
            with open(history_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)
        else:
            return jsonify({"error": "任务未完成或不存在"}), 404

    # 构建文件路径（适配你的uploads目录结构）
    filename = task_data["filename"]
    base_name = os.path.splitext(filename)[0]
    file_path = os.path.join(transcription_service.HISTORY_FOLDER, f"{base_name}.{format}")

    if not os.path.exists(file_path):
        return jsonify({"error": "文件不存在"}), 404

    # 发送文件
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{base_name}.{format}"
    )