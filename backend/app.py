from flask import Flask, send_from_directory
import os
from flask_cors import CORS
from backend.config import Config
from backend.api.upload import register_upload_routes
from backend.api.download import register_download_routes
from backend.api.history import register_history_routes

def create_app():
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    uploads_dir = Config.UPLOAD_FOLDER

    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path='/static'
    )
    app.secret_key = Config.SECRET_KEY
    CORS(app)

    # 确保上传目录存在
    os.makedirs(uploads_dir, exist_ok=True)

    # 注册 API 路由
    from backend.api.upload import register_upload_routes
    from backend.api.download import register_download_routes
    from backend.api.history import register_history_routes

    register_upload_routes(app)
    register_download_routes(app)
    register_history_routes(app)

    @app.route('/')
    def index():
        return send_from_directory(frontend_dir, 'index.html')

    return app