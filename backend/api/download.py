from flask import request, session, send_file, jsonify
import os
from backend.config import Config

ALLOWED_FORMATS = {'srt', 'txt', 'vtt', 'json'}

def register_download_routes(app):
    @app.route('/download/<format_type>')
    def download(format_type):
        if format_type not in ALLOWED_FORMATS:
            return jsonify({"error": "不支持的格式"}), 400
        
        current_task_id = session.get('current_task_id')
        if not current_task_id:
            return jsonify({"error": "请先完成一次转录"}), 400

        filepath = os.path.join(Config.UPLOAD_FOLDER, f"{current_task_id}.{format_type}")
        if not os.path.exists(filepath):
            return jsonify({"error": "文件不存在或已过期"}), 404

        return send_file(filepath, as_attachment=True)