# app.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import whisper
import os
import tempfile

app = FastAPI(title="Whisper Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局模型缓存（避免重复加载）
models = {}

def get_model(model_name):
    if model_name not in models:
        print(f"正在加载模型: {model_name}")
        models[model_name] = whisper.load_model(model_name)
    return models[model_name]

@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    model: str = Form("base"),
    language: str = Form(None),
    task: str = Form("transcribe")
):
    if not audio.content_type.startswith("audio/") and not audio.content_type.startswith("video/"):
        return JSONResponse({"error": "请上传有效的音频或视频文件"}, status_code=400)

    try:
        # 保存临时文件
        suffix = os.path.splitext(audio.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        # 加载指定模型
        if model not in ["tiny", "base", "small", "medium", "large"]:
            return JSONResponse({"error": "不支持的模型"}, status_code=400)

        model_obj = get_model(model)

        # 转录
        result = model_obj.transcribe(
            tmp_path,
            language=language or None,
            task=task
        )

        os.unlink(tmp_path)

        return {
            "text": result["text"].strip(),
            "language": result.get("language", "auto"),
            "model": model,
            "task": task
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)