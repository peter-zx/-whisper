import os
import tempfile
import json
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import whisper
import opencc
from pydub import AudioSegment

# 初始化
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 上传目录
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OpenCC 转换器（繁体转简体）
cc = opencc.OpenCC('t2s')

# 支持模型
MODEL_OPTIONS = {
    "base": "base",
    "small": "small",
    "medium": "medium",
    "large-v3": "large-v3"
}

def convert_to_wav(input_path, output_path):
    """将任意音视频转换为 16kHz 单声道 WAV"""
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        raise ValueError(f"音频转换失败: {str(e)}")

def generate_srt(segments):
    lines = []
    for i, seg in enumerate(segments, 1):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()

        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        lines.append(str(i))
        lines.append(f"{format_time(start)} --> {format_time(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

def generate_vtt(segments):
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()

        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02}.{ms:03}"

        lines.append(f"{format_time(start)} --> {format_time(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400

    file = request.files['file']
    model_name = request.form.get('model', 'base')
    language = request.form.get('language', 'zh')  # zh 表示强制中文

    if model_name not in MODEL_OPTIONS:
        return jsonify({"error": "不支持的模型"}), 400

    # 保存文件
    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)

    try:
        # 转为 WAV
        wav_path = os.path.join(UPLOAD_FOLDER, f"{os.path.splitext(file.filename)[0]}.wav")
        convert_to_wav(original_path, wav_path)

        # 加载模型
        model = whisper.load_model(model_name)

        # 转录（强制中文）
        if language == 'zh':
            result = model.transcribe(wav_path, language='zh', verbose=False)
        else:
            result = model.transcribe(wav_path, verbose=False)

        # 繁体转简体
        simplified_segments = []
        for segment in result['segments']:
            simplified_text = cc.convert(segment['text'])
            simplified_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': simplified_text
            })

        # 创建临时目录存储下载文件
        base_name = os.path.splitext(file.filename)[0]
        temp_dir = tempfile.mkdtemp()

        # 写入各种格式
        with open(os.path.join(temp_dir, f"{base_name}.srt"), 'w', encoding='utf-8') as f:
            f.write(generate_srt(simplified_segments))
        with open(os.path.join(temp_dir, f"{base_name}.txt"), 'w', encoding='utf-8') as f:
            f.write("\n".join([seg['text'] for seg in simplified_segments]))
        with open(os.path.join(temp_dir, f"{base_name}.vtt"), 'w', encoding='utf-8') as f:
            f.write(generate_vtt(simplified_segments))
        with open(os.path.join(temp_dir, f"{base_name}.json"), 'w', encoding='utf-8') as f:
            json.dump(simplified_segments, f, ensure_ascii=False, indent=2)

        # 返回结果
        return jsonify({
            "segments": simplified_segments,
            "download_base": base_name,
            "temp_dir": temp_dir
        })

    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500
    finally:
        # 清理原始文件
        try:
            os.remove(original_path)
            os.remove(wav_path)
        except:
            pass

@app.route('/download/<format_type>', methods=['GET'])
def download_subtitle(format_type):
    temp_dir = request.args.get('temp_dir')
    base_name = request.args.get('base_name')
    if not temp_dir or not base_name:
        return jsonify({"error": "缺少参数"}), 400

    ext_map = {
        'srt': '.srt',
        'txt': '.txt',
        'vtt': '.vtt',
        'json': '.json'
    }
    if format_type not in ext_map:
        return jsonify({"error": "不支持的格式"}), 400

    file_path = os.path.join(temp_dir, base_name + ext_map[format_type])
    if not os.path.exists(file_path):
        return jsonify({"error": "文件不存在"}), 404

    return send_file(file_path, as_attachment=True)

@app.route('/')
def index():
    return send_file('static/index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)