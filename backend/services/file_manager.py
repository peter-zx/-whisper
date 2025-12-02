# backend/services/file_manager.py
import os
import subprocess

class FileManager:
    """文件管理工具类（确保能被TranscriptionService正确导入）"""
    SUPPORTED_FORMATS = [
        # 音频
        '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma',
        # 视频
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg'
    ]

    @staticmethod
    def validate_file(filename):
        """验证文件格式"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in FileManager.SUPPORTED_FORMATS

    @staticmethod
    def convert_to_wav(input_path, output_path):
        """转换为WAV（兼容Windows）"""
        try:
            # Windows下ffmpeg路径兼容
            ffmpeg_path = "ffmpeg"  # 如果配置了环境变量，直接用
            # 备选：指定ffmpeg完整路径（根据你的实际安装路径修改）
            # ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
            
            cmd = [
                ffmpeg_path,
                "-i", input_path,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                output_path
            ]
            # 执行转换（隐藏窗口）
            startupinfo = None
            if os.name == 'nt':  # Windows系统
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return os.path.exists(output_path)
        except Exception as e:
            print(f"转换WAV失败：{e}")
            # 降级：直接复制文件（如果已经是WAV）
            if input_path.lower().endswith(".wav"):
                import shutil
                shutil.copy(input_path, output_path)
                return True
            return False

    @staticmethod
    def get_file_info(file_path):
        """获取文件信息"""
        if not os.path.exists(file_path):
            return None
        return {
            "name": os.path.basename(file_path),
            "size_mb": round(os.path.getsize(file_path) / 1024 / 1024, 2),
            "path": file_path
        }