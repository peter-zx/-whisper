# backend/services/file_manager.py
import os
import subprocess
from pathlib import Path

class FileManager:
    @staticmethod
    def is_wav(file_path):
        return file_path.lower().endswith('.wav')

    @staticmethod
    def convert_to_wav(input_path, output_path=None):
        if output_path is None:
            stem = Path(input_path).stem
            output_path = os.path.join(os.path.dirname(input_path), f"{stem}.wav")

        try:
            subprocess.run([
                'ffmpeg', '-i', input_path,
                '-ar', '16000',
                '-ac', '1',
                '-f', 'wav',
                '-y',
                output_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未安装或不在 PATH 中")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg 转换失败: {e}")

        return output_path