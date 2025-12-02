import os
import time
import json
from datetime import datetime
from threading import Lock
from backend.models.whisper_engine import WhisperEngine
from backend.services.file_manager import FileManager
from backend.config import Config

HISTORY = []
HISTORY_LOCK = Lock()

def generate_subtitle_content(segments, fmt: str) -> str:
    if fmt == 'txt':
        return "\n".join([s['text'] for s in segments])
    elif fmt == 'json':
        return json.dumps(segments, ensure_ascii=False, indent=2)
    elif fmt == 'srt':
        lines = []
        for i, s in enumerate(segments, 1):
            def fmt_time(t):
                h, m = int(t // 3600), int((t % 3600) // 60)
                sec = t % 60
                ms = int((sec - int(sec)) * 1000)
                return f"{h:02}:{m:02}:{int(sec):02},{ms:03}"
            lines.extend([str(i), f"{fmt_time(s['start'])} --> {fmt_time(s['end'])}", s['text'], ""])
        return "\n".join(lines)
    elif fmt == 'vtt':
        lines = ["WEBVTT", ""]
        for s in segments:
            def fmt_time(t):
                h, m = int(t // 3600), int((t % 3600) // 60)
                sec = t % 60
                ms = int((sec - int(sec)) * 1000)
                return f"{h:02}:{m:02}:{int(sec):02}.{ms:03}"
            lines.extend([f"{fmt_time(s['start'])} --> {fmt_time(s['end'])}", s['text'], ""])
        return "\n".join(lines)
    else:
        raise ValueError("Unsupported format")

def transcribe_task(file, model_name: str, language: str):
    global HISTORY
    fm = FileManager()
    fm.cleanup_old_files()

    original_path = fm.save_uploaded_file(file)
    wav_path = fm.convert_to_wav(original_path)

    try:
        engine = WhisperEngine(model_name)
        segments = engine.transcribe(wav_path, language)

        base_name = os.path.splitext(file.filename)[0]
        task_id = f"{base_name}_{int(time.time())}"
        formats = {}
        for fmt in ['srt', 'txt', 'vtt', 'json']:
            content = generate_subtitle_content(segments, fmt)
            filepath = os.path.join(Config.UPLOAD_FOLDER, f"{task_id}.{fmt}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            formats[fmt] = filepath

        item = {
            "id": task_id,
            "filename": file.filename,
            "model": model_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "segments": segments
        }

        with HISTORY_LOCK:
            HISTORY.insert(0, item)
            if len(HISTORY) > Config.HISTORY_MAX_ITEMS:
                oldest = HISTORY.pop()
                for ext in ['srt','txt','vtt','json']:
                    fp = os.path.join(Config.UPLOAD_FOLDER, f"{oldest['id']}.{ext}")
                    if os.path.exists(fp):
                        os.remove(fp)

        return {"success": True, "task_id": task_id, "segments": segments}
    finally:
        try:
            os.remove(original_path)
            os.remove(wav_path)
        except:
            pass