# backend/models/whisper_engine.py
import whisper

class WhisperEngine:
    def __init__(self, model_name="tiny"):
        if model_name == "turbo":
            model_name = "large-v3"
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_path, language=None, task="transcribe"):
        result = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False
        )
        return result