import os
import time
from pydub import AudioSegment
from backend.config import Config

class FileManager:
    def __init__(self):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    def save_uploaded_file(self, file) -> str:
        path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
        file.save(path)
        return path

    def convert_to_wav(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0] + '.wav'
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return output_path

    def cleanup_old_files(self):
        now = time.time()
        for f in os.listdir(Config.UPLOAD_FOLDER):
            path = os.path.join(Config.UPLOAD_FOLDER, f)
            if os.path.isfile(path) and now - os.path.getmtime(path) > Config.TEMP_FILE_EXPIRE_HOURS * 3600:
                try:
                    os.remove(path)
                except:
                    pass