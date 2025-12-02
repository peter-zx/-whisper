import os
os.environ["PATH"] += os.pathsep + r"E:\ai_work\ffmpeg-master-latest-win64-gpl-shared\bin"

# test_whisper.py
import whisper

print("正在加载 base 模型...")
model = whisper.load_model("base")

# 测试音频（请替换成你的 .wav/.mp3 文件）
audio_file = "1017.mp4"  # 或 "test.mp3"

try:
    result = model.transcribe(audio_file, language="zh")
    print("识别结果：", result["text"])
except Exception as e:
    print("错误：", str(e))