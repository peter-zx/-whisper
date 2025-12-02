from flask import Blueprint, jsonify
from backend.services.transcription import TranscriptionService

history_bp = Blueprint("history", __name__)
transcription_service = TranscriptionService()

@history_bp.route("/api/history", methods=["GET"])
def get_history():
    """获取所有历史记录"""
    history = transcription_service.get_history()
    return jsonify({"history": history})