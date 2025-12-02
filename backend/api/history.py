# backend/api/history.py
import json
from pathlib import Path
from flask import Blueprint, jsonify
from backend.config import HISTORY_FOLDER

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
def get_history():
    history = []
    history_path = Path(HISTORY_FOLDER)
    if not history_path.exists():
        return jsonify([])

    for f in history_path.glob("*.json"):
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
                history.append(data)
        except Exception:
            continue

    history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return jsonify(history[:7])