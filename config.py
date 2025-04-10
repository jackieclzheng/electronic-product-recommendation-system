import os

class Config:
    # 获取项目根目录的绝对路径
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'product_recommendation.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask应用配置
    SECRET_KEY = os.urandom(24)
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大上传限制
    
    # 自定义配置
    STATIC_FOLDER = os.path.join(BASEDIR, 'static')
    TEMPLATES_FOLDER = os.path.join(BASEDIR, 'templates')
    
    # 确保必要的目录存在
    @staticmethod
    def init_app(app):
        os.makedirs(os.path.join(app.static_folder, 'images/emotion_charts'), exist_ok=True)
        os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)