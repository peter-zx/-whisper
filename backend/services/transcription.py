# backend/services/transcription.py
import os
import json
import time
from pathlib import Path

try:
    from opencc import OpenCC
    cc = OpenCC('t2s')
except Exception:
    cc = None

def save_history(result, original_filename):
    from backend.config import HISTORY_FOLDER
    timestamp = str(int(time.time()))
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(original_filename).stem)
    base_name = os.path.join(HISTORY_FOLDER, f"{safe_name}_{timestamp}")
    return base_name

def generate_subtitle_formats(result, base_name):
    from backend.config import HISTORY_FOLDER
    os.makedirs(HISTORY_FOLDER, exist_ok=True)

    # 繁转简
    if cc:
        result["text"] = cc.convert(result["text"])
        for seg in result.get("segments", []):
            seg["text"] = cc.convert(seg["text"])

    text = result["text"]
    segments = result.get("segments", [])

    # TXT
    with open(f"{base_name}.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # SRT
    with open(f"{base_name}.srt", "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = _format_srt_timestamp(seg["start"])
            end = _format_srt_timestamp(seg["end"])
            f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

    # VTT
    with open(f"{base_name}.vtt", "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = _format_vtt_timestamp(seg["start"])
            end = _format_vtt_timestamp(seg["end"])
            f.write(f"{start} --> {end}\n{seg['text'].strip()}\n\n")

    # JSON (用于历史记录)
    meta = {
        "text": text,
        "segments": segments,
        "timestamp": int(time.time()),
        "filename": os.path.basename(base_name)
    }
    with open(f"{base_name}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return ["txt", "srt", "vtt", "json"]

def _format_srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def _format_vtt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"