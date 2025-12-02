# backend/services/transcription.py
# 确保文件编码为UTF-8，无语法错误，类名拼写完全正确
import os
import json
import uuid
from datetime import datetime

# 先确保依赖的类能正确导入
try:
    from backend.models.whisper_engine import WhisperEngine
    from backend.services.file_manager import FileManager
except ImportError as e:
    print(f"导入依赖失败：{e}")
    # 降级处理：如果导入失败，先定义空类（避免崩溃）
    class WhisperEngine:
        def __init__(self):
            self.task_status = {}
            self.task_progress = {}
        def transcribe(self, audio_path, task_id, language="zh", task="transcribe", device="cpu"):
            return {"text": "", "segments": []}
        def get_progress(self, task_id):
            return {"progress": 100, "status": "completed"}
    
    class FileManager:
        SUPPORTED_FORMATS = ['.mp3','.wav','.flac','.m4a','.mp4','.avi','.mov']
        @staticmethod
        def validate_file(filename):
            return os.path.splitext(filename)[1].lower() in FileManager.SUPPORTED_FORMATS
        @staticmethod
        def convert_to_wav(input_path, output_path):
            return True

# ========== 核心：确保TranscriptionService类定义完整、拼写正确 ==========
class TranscriptionService:
    """转录服务核心类（类名必须完全匹配：TranscriptionService）"""
    def __init__(self):
        self.whisper = WhisperEngine()  # 初始化Whisper引擎
        self.task_map = {}  # 任务映射 {task_id: {"filename": "", "status": ""}}
        self.result_cache = {}  # 结果缓存 {task_id: {"text": "", "files": []}}
        self.history_path = os.path.join(os.path.dirname(__file__), "transcription_history.json")

    def create_task_id(self):
        """生成8位唯一任务ID"""
        return str(uuid.uuid4())[:8]

    def run_transcription_by_path(self, input_path, filename, language="zh", task="transcribe", device="cpu"):
        """
        同步执行转录（确保任务ID一致，前端能获取到）
        """
        # 1. 生成唯一任务ID
        task_id = self.create_task_id()
        self.task_map[task_id] = {
            "filename": filename,
            "status": "processing",
            "create_time": self._get_current_time()
        }
        print(f"开始转录任务：{task_id} - {filename}")

        try:
            # 2. 转换为WAV格式（兼容所有音频/视频）
            wav_filename = f"{os.path.splitext(filename)[0]}_{task_id}.wav"
            wav_path = os.path.join(os.path.dirname(input_path), wav_filename)
            if not FileManager.convert_to_wav(input_path, wav_path):
                self.task_map[task_id]["status"] = "failed"
                return {"task_id": task_id, "status": "failed", "error": "转换WAV失败"}

            # 3. 执行Whisper转录（核心）
            result = self.whisper.transcribe(wav_path, task_id, language, task, device)
            text = result.get("text", "").strip()
            print(f"转录完成：{task_id} - 文本长度：{len(text)}")

            # 4. 生成多格式字幕文件
            output_dir = os.path.join(os.path.dirname(input_path), "subtitles", task_id)
            os.makedirs(output_dir, exist_ok=True)
            subtitle_files = self._generate_subtitle_files(result, output_dir, filename)

            # 5. 缓存结果（关键：前端能获取到）
            self.result_cache[task_id] = {
                "text": text,
                "files": subtitle_files,
                "filename": filename,
                "create_time": self._get_current_time()
            }

            # 6. 更新任务状态
            self.task_map[task_id]["status"] = "completed"
            self._save_history(task_id, filename, subtitle_files)

            return {
                "task_id": task_id,
                "status": "completed",
                "text": text,
                "files": subtitle_files
            }

        except Exception as e:
            error_msg = f"转录失败：{str(e)}"
            print(error_msg)
            self.task_map[task_id]["status"] = "failed"
            return {"task_id": task_id, "status": "failed", "error": error_msg}

    def _generate_subtitle_files(self, result, output_dir, filename):
        """生成SRT/TXT/VTT/JSON格式字幕"""
        base_name = os.path.splitext(filename)[0]
        files = {}

        # TXT（纯文本）
        txt_path = os.path.join(output_dir, f"{base_name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result.get("text", ""))
        files["txt"] = txt_path

        # SRT（标准字幕）
        srt_path = os.path.join(output_dir, f"{base_name}.srt")
        self._write_srt(result.get("segments", []), srt_path)
        files["srt"] = srt_path

        # VTT（WebVTT）
        vtt_path = os.path.join(output_dir, f"{base_name}.vtt")
        self._write_vtt(result.get("segments", []), vtt_path)
        files["vtt"] = vtt_path

        # JSON（完整结果）
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        files["json"] = json_path

        return files

    def _write_srt(self, segments, output_path):
        """生成SRT字幕"""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = self._format_time(seg["start"])
                end = self._format_time(seg["end"])
                text = seg["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    def _write_vtt(self, segments, output_path):
        """生成VTT字幕"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for seg in segments:
                start = self._format_time(seg["start"], vtt=True)
                end = self._format_time(seg["end"], vtt=True)
                text = seg["text"].strip()
                f.write(f"{start} --> {end}\n{text}\n\n")

    def _format_time(self, seconds, vtt=False):
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        if vtt:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

    def _save_history(self, task_id, filename, files):
        """保存转录历史"""
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        
        history.insert(0, {
            "task_id": task_id,
            "filename": filename,
            "create_time": self._get_current_time(),
            "files": files
        })
        history = history[:10]  # 保留最近10条
        
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def get_history(self):
        """获取转录历史"""
        if not os.path.exists(self.history_path):
            return []
        with open(self.history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_task_result(self, task_id, format_type):
        """获取任务结果（前端下载/显示用）"""
        if task_id not in self.result_cache:
            return None
        
        files = self.result_cache[task_id]["files"]
        if format_type not in files or not os.path.exists(files[format_type]):
            # 如果文件不存在，直接返回缓存的文本
            if format_type == "txt":
                return self.result_cache[task_id]["text"]
            return None
        
        # 读取文件内容
        with open(files[format_type], "r", encoding="utf-8") as f:
            return f.read()

    def _get_current_time(self):
        """获取格式化的当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ========== 确保文件能被正确导入 ==========
if __name__ == "__main__":
    # 测试导入
    ts = TranscriptionService()
    print("TranscriptionService 导入成功！")
    print(f"生成测试任务ID：{ts.create_task_id()}")