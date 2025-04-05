#!/usr/bin/env python3
# run.py - 应用启动脚本

from app import app

if __name__ == '__main__':
    # 训练推荐模型
    # from recommendation.recommender import ProductRecommender
    # recommender = ProductRecommender()
    # recommender.train_model()

    with app.app_context():
        from recommendation.recommender import ProductRecommender
        recommender = ProductRecommender()
        recommender.train_model()
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)
