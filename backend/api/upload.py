from flask import request, jsonify, session
from backend.services.transcription import transcribe_task
from backend.config import Config

def register_upload_routes(app):
    @app.route('/transcribe', methods=['POST'])
    def transcribe():
        if 'file' not in request.files:
            return jsonify({"error": "未上传文件"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400

        file.seek(0, 2)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if size_mb > Config.MAX_FILE_SIZE_MB:
            return jsonify({"error": f"文件过大（>{Config.MAX_FILE_SIZE_MB}MB）"}), 400

        model = request.form.get('model', 'base')
        lang = request.form.get('language', 'zh')
        if model not in ['base', 'small', 'medium', 'large-v3']:
            return jsonify({"error": "模型不支持"}), 400

        try:
            result = transcribe_task(file, model, lang)
            session['current_task_id'] = result['task_id']
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": f"处理失败: {str(e)}"}), 500