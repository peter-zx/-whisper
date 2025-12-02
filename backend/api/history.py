from flask import jsonify
from backend.services.transcription import HISTORY

def register_history_routes(app):
    @app.route('/history')
    def get_history():
        return jsonify(HISTORY[:7])