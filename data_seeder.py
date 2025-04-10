# 数据填充脚本
import sys
import os
import json
import random
from datetime import datetime, timedelta
from textblob import TextBlob
import jieba

# 确保可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.models import db, User, Product, ProductCategory, UserReview, ProductSale, PlatformDiscount
from werkzeug.security import generate_password_hash


def generate_sentiment_analysis(review_content):
    """
    中文情感分析函数
    """
    # 正面词汇
    positive_words = ['好', '棒', '优秀', '喜欢', '不错', '高端', '性价比', '推荐']
    # 负面词汇
    negative_words = ['差', '不好', '一般', '失望', '问题', '坏', '不推荐']
    
    # 分词
    words = jieba.lcut(review_content)
    
    # 计算情感得分
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    # 情感得分计算
    total_count = positive_count + negative_count + 1
    sentiment_score = (positive_count - negative_count) / total_count
    sentiment_score = max(-1, min(1, sentiment_score))
    
    emotion_dimensions = {
        'positive_emotion': max(0, sentiment_score),
        'negative_emotion': max(0, -sentiment_score),
        'objectivity': 1 - abs(sentiment_score),
        'length_factor': min(1, len(review_content) / 50)
    }
    
    return sentiment_score, emotion_dimensions


def seed_reviews():
    """
    为已存在的产品和用户生成测试评价
    """
    with app.app_context():
        # 获取所有产品和用户
        products = Product.query.all()
        users = User.query.all()

        # 评价模板
        review_templates = [
            "这个产品真的很{adj}，{detail}",
            "总的来说{sentiment}，{reason}",
            "{usage}使用体验{evaluation}",
            "性价比{value_comment}，{recommend}"
        ]

        # 形容词和评价词
        adjectives = ['好', '不错', '优秀', '一般', '一般般']
        sentiments = ['还不错', '有点失望', '很满意', '还行']

        # 生成评价
        reviews_to_add = []
        for product in products:
            # 每个产品生成 5-10 条评价
            review_count = random.randint(5, 10)

            for _ in range(review_count):
                # 随机选择用户
                user = random.choice(users)

                # 生成评价内容
                adj = random.choice(adjectives)
                sentiment = random.choice(sentiments)
                detail = f"使用了{random.randint(1, 12)}个月"
                reason = f"主要用于{['工作', '娱乐', '学习', '游戏'][random.randint(0, 3)]}"
                usage = "我" if random.random() > 0.5 else "朋友"
                evaluation = "相当不错" if random.random() > 0.5 else "一般"
                value_comment = "确实很高" if random.random() > 0.5 else "一般"
                recommend = "强烈推荐" if random.random() > 0.5 else "一般般"

                # 随机选择模板
                content = random.choice(review_templates).format(
                    adj=adj,
                    sentiment=sentiment,
                    detail=detail,
                    reason=reason,
                    usage=usage,
                    evaluation=evaluation,
                    value_comment=value_comment,
                    recommend=recommend
                )

                # 随机评分
                rating = random.randint(3, 5) if random.random() > 0.3 else random.randint(1, 2)

                # 情感分析
                sentiment_score, emotion_dimensions = generate_sentiment_analysis(content)

                # 创建评价
                review = UserReview(
                    user_id=user.id,
                    product_id=product.id,
                    content=content,
                    rating=rating,
                    sentiment=sentiment_score,
                    sentiment_score=sentiment_score,
                    emotion_dimensions=json.dumps(emotion_dimensions),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 180))
                )

                reviews_to_add.append(review)

        # 批量添加
        db.session.add_all(reviews_to_add)
        db.session.commit()

        print(f"成功生成 {len(reviews_to_add)} 条产品评价")


def seed_incremental_data():
    """增量添加测试数据，不清空现有数据"""
    print("开始添加增量测试数据...")
    
    # 获取现有数据的ID范围
    max_user_id = db.session.query(db.func.max(User.id)).scalar() or 0
    max_product_id = db.session.query(db.func.max(Product.id)).scalar() or 0
    
    # 从现有最大ID开始创建新数据
    new_users = []
    for i in range(max_user_id + 1, max_user_id + 11):  # 添加10个新用户
        user = User(
            username=f'new_user{i}',
            email=f'new_user{i}@example.com',
            password_hash=generate_password_hash(f'password{i}'),
            register_time=datetime.now()
        )
        db.session.add(user)
        new_users.append(user)
    
    db.session.commit()
    print(f"已添加 {len(new_users)} 个新用户")

    # 获取所有现有产品
    existing_products = Product.query.all()
    
    # 为新用户添加评论和行为数据
    total_new_reviews = 0
    for user in new_users:
        # 为每个新用户随机选择5-10个产品评论
        review_products = random.sample(existing_products, 
                                     min(random.randint(5, 10), len(existing_products)))
        
        for product in review_products:
            # 创建新的评论
            review = UserReview(
                user_id=user.id,
                product_id=product.id,
                rating=random.randint(1, 5),
                content=f"新用户评价内容 - {user.username}",
                created_at=datetime.now()
            )
            db.session.add(review)
            total_new_reviews += 1
            
    db.session.commit()
    print(f"已添加 {total_new_reviews} 条新评论")
    
    print("增量数据添加完成！")


def seed_data(app):
    """填充增量数据"""
    with app.app_context():
        seed_incremental_data()


if __name__ == '__main__':
    from app import app
    seed_data(app)