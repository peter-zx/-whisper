import whisper
import opencc

class WhisperEngine:
    def __init__(self, model_name: str):
        self.model = whisper.load_model(model_name)
        self.cc = opencc.OpenCC('t2s')

    def transcribe(self, audio_path: str, language: str = None):
        if language == 'zh':
            result = self.model.transcribe(audio_path, language='zh', verbose=False)
        else:
            result = self.model.transcribe(audio_path, verbose=False)
        
        segments = []
        for seg in result['segments']:
            simplified = self.cc.convert(seg['text'])
            segments.append({
                'start': round(seg['start'], 2),
                'end': round(seg['end'], 2),
                'text': simplified
            })
        return segments