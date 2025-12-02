import os  # 核心添加：导入os模块
from flask import Flask, send_from_directory
from backend.config import BASE_DIR
from backend.api.upload import upload_bp
from backend.api.download import download_bp
from backend.api.history import history_bp

# 初始化Flask应用
app = Flask(__name__, static_folder=None)

# 注册蓝图
app.register_blueprint(upload_bp)
app.register_blueprint(download_bp)
app.register_blueprint(history_bp)

# 前端入口路由（index.html在static根目录）
@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "index.html")

# 静态文件路由（适配static下的css/js/assets）
@app.route("/css/<path:path>")
def css_files(path):
    return send_from_directory(os.path.join(BASE_DIR, "static/css"), path)

@app.route("/js/<path:path>")
def js_files(path):
    return send_from_directory(os.path.join(BASE_DIR, "static/js"), path)

@app.route("/assets/<path:path>")
def assets_files(path):
    return send_from_directory(os.path.join(BASE_DIR, "static/assets"), path)

# 跨域支持
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response