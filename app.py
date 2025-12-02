import os
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
import whisper
import opencc
from pydub import AudioSegment

# 初始化
app = Flask(__name__)
app.secret_key = 'whisper_subtitle_secret_2025'  # 用于 session
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局历史记录（内存中，最多7条）
HISTORY = []
HISTORY_LOCK = threading.Lock()

# 缓存清理：每10分钟清理一次 >1小时的文件
CLEANUP_INTERVAL = 600  # 秒
LAST_CLEANUP = time.time()

def cleanup_old_files():
    global LAST_CLEANUP
    now = time.time()
    if now - LAST_CLEANUP > CLEANUP_INTERVAL:
        LAST_CLEANUP = now
        for f in os.listdir(UPLOAD_FOLDER):
            path = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(path) and now - os.path.getmtime(path) > 3600:  # 1小时
                try:
                    os.remove(path)
                except:
                    pass

def convert_to_wav(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")
    return output_path

def generate_srt(segments):
    lines = []
    for i, seg in enumerate(segments, 1):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        def fmt(s): 
            h, m = int(s // 3600), int((s % 3600) // 60)
            s_sec = s % 60
            ms = int((s_sec - int(s_sec)) * 1000)
            return f"{h:02}:{m:02}:{int(s_sec):02},{ms:03}"
        lines.extend([str(i), f"{fmt(start)} --> {fmt(end)}", text, ""])
    return "\n".join(lines)

def generate_vtt(segments):
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        def fmt(s):
            h, m = int(s // 3600), int((s % 3600) // 60)
            s_sec = s % 60
            ms = int((s_sec - int(s_sec)) * 1000)
            return f"{h:02}:{m:02}:{int(s_sec):02}.{ms:03}"
        lines.extend([f"{fmt(start)} --> {fmt(end)}", text, ""])
    return "\n".join(lines)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    global HISTORY
    cleanup_old_files()  # 每次请求都尝试清理

    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400

    file = request.files['file']
    model_name = request.form.get('model', 'base')
    language = request.form.get('language', 'zh')
    device = request.form.get('device', 'auto')  # cpu/gpu/auto

    if model_name not in ["base", "small", "medium", "large-v3"]:
        return jsonify({"error": "不支持的模型"}), 400

    # 限制文件大小（可选）
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > 100:  # 100MB
        return jsonify({"error": "文件过大，请上传小于100MB的音视频"}), 400

    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)

    try:
        wav_path = os.path.join(UPLOAD_FOLDER, f"{os.path.splitext(file.filename)[0]}.wav")
        convert_to_wav(original_path, wav_path)

        # 加载模型（Whisper 自动使用 GPU 如果可用）
        model = whisper.load_model(model_name)

        if language == 'zh':
            result = model.transcribe(wav_path, language='zh', verbose=False)
        else:
            result = model.transcribe(wav_path, verbose=False)

        cc = opencc.OpenCC('t2s')
        simplified_segments = []
        for segment in result['segments']:
            simplified_text = cc.convert(segment['text'])
            simplified_segments.append({
                'start': round(segment['start'], 2),
                'end': round(segment['end'], 2),
                'text': simplified_text
            })

        # 生成所有格式并保存到 uploads/
        base_name = os.path.splitext(file.filename)[0]
        timestamp = str(int(time.time()))
        task_id = f"{base_name}_{timestamp}"

        formats = {}
        for fmt in ['srt', 'txt', 'vtt', 'json']:
            content = ""
            if fmt == 'srt':
                content = generate_srt(simplified_segments)
            elif fmt == 'txt':
                content = "\n".join([seg['text'] for seg in simplified_segments])
            elif fmt == 'vtt':
                content = generate_vtt(simplified_segments)
            elif fmt == 'json':
                content = json.dumps(simplified_segments, ensure_ascii=False, indent=2)

            filepath = os.path.join(UPLOAD_FOLDER, f"{task_id}.{fmt}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            formats[fmt] = filepath

        # 构建历史项
        history_item = {
            "id": task_id,
            "filename": file.filename,
            "model": model_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "segments": simplified_segments,
            "formats": {k: v for k, v in formats.items()}
        }

        # 更新历史（最多7条）
        with HISTORY_LOCK:
            HISTORY.insert(0, history_item)
            if len(HISTORY) > 7:
                oldest = HISTORY.pop()
                # 删除旧文件
                for fp in oldest['formats'].values():
                    if os.path.exists(fp):
                        os.remove(fp)
            current_history = HISTORY.copy()

        # 存入 session（用于下载）
        session['current_task'] = task_id
        session['current_formats'] = {k: v for k, v in formats.items()}

        return jsonify({
            "success": True,
            "task_id": task_id,
            "segments": simplified_segments,
            "history": current_history
        })

    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500
    finally:
        try:
            os.remove(original_path)
            os.remove(wav_path)
        except:
            pass

@app.route('/download/<format_type>', methods=['GET'])
def download_subtitle(format_type):
    allowed_formats = {'srt', 'txt', 'vtt', 'json'}
    if format_type not in allowed_formats:
        return jsonify({"error": "不支持的格式"}), 400

    current_formats = session.get('current_formats', {})
    file_path = current_formats.get(format_type)
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "文件不存在或已过期"}), 404

    return send_file(file_path, as_attachment=True)

@app.route('/history')
def get_history():
    with HISTORY_LOCK:
        return jsonify(HISTORY[:7])

@app.route('/')
def index():
    return send_file('static/index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)