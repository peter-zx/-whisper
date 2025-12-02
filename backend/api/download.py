# backend/api/download.py
import os
from flask import Blueprint, send_file, abort
from backend.config import HISTORY_FOLDER

download_bp = Blueprint('download', __name__)

@download_bp.route('/download/<filename_base>/<fmt>')
def download(filename_base, fmt):
    if fmt not in ["txt", "srt", "vtt", "json"]:
        abort(400)
    filepath = os.path.join(HISTORY_FOLDER, f"{filename_base}.{fmt}")
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, as_attachment=True)