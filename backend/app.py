# backend/app.py
from flask import Flask, send_from_directory
import os

def create_app():
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # 注册路由
    @app.route('/')
    def index():
        return send_from_directory('../static', 'index.html')

    # 导入蓝图（顺序无关，但必须能成功导入）
    from backend.api.upload import upload_bp
    from backend.api.download import download_bp
    from backend.api.history import history_bp

    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(download_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')

    return app