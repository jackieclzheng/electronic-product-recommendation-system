import os
from app import app
from models.models import db
import init_test_data
import data_seeder

def setup_database():
    """设置和填充数据库"""
    # 确保instance目录存在
    os.makedirs('instance', exist_ok=True)
    
    with app.app_context():
        # 删除现有数据库
        db.drop_all()
        # 创建新的数据库表
        db.create_all()
    
    print("数据库表创建完成")
    
    # 运行初始化数据脚本
    print("开始执行初始化数据脚本...")
    init_test_data.init_data(app)
    
    # 运行增量数据脚本
    print("开始执行增量数据脚本...")
    data_seeder.seed_data(app)
    
    print("所有数据填充完成！")

if __name__ == '__main__':
    setup_database()