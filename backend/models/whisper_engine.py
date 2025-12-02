import whisper
import threading
import time

class WhisperEngine:
    _instance = None
    _lock = threading.Lock()
    progress = 0  # 转录进度
    current_task = None  # 当前任务ID
    current_model = "tiny"  # 默认最小模型
    task_status = {}  # 任务状态映射 {task_id: "completed/processing/failed"}
    task_progress = {}  # 单独存储进度 {task_id: 100}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.model = whisper.load_model(cls.current_model)
        return cls._instance

    def load_model(self, model_name):
        if self.current_model != model_name:
            with self._lock:
                print(f"正在加载{model_name}模型...")
                self.model = whisper.load_model(model_name)
                self.current_model = model_name
                print(f"{model_name}模型加载完成！")

    def transcribe(self, audio_path, task_id, language="zh", task="transcribe", device="cpu"):
        """核心修复：确保任务状态和进度正确更新"""
        # 初始化任务状态
        self.task_status[task_id] = "processing"
        self.task_progress[task_id] = 0
        self.current_task = task_id

        try:
            # 转录配置
            kwargs = {
                "task": task,
                "verbose": True,
                "language": language,
                "fp16": True if device == "gpu" else False
            }
            if self.current_model in ["medium", "large"]:
                kwargs["beam_size"] = 3

            # 执行转录
            result = self.model.transcribe(audio_path,** kwargs)
            
            # ========== 核心修复1：强制更新任务状态 ==========
            self.task_status[task_id] = "completed"
            self.task_progress[task_id] = 100
            self.current_task = None

            # 确保结果格式完整
            if "text" not in result:
                result["text"] = ""
            if "segments" not in result:
                result["segments"] = []
                
            return result
        except Exception as e:
            print(f"转录异常：{e}")
            self.task_status[task_id] = "failed"
            self.task_progress[task_id] = 0
            self.current_task = None
            return {"text": "", "segments": [], "error": str(e)}

    def get_progress(self, task_id):
        """核心修复2：返回正确的任务状态和进度"""
        return {
            "progress": self.task_progress.get(task_id, 0),
            "status": self.task_status.get(task_id, "pending")
        }