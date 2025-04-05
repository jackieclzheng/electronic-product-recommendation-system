# 数据填充脚本
import sys
import os
import json
import random
from datetime import datetime, timedelta

# 确保可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.models import db, User, Product, ProductCategory, UserReview


def generate_sentiment_analysis(review_content):
    """
    简单的情感分析模拟函数
    根据关键词和长度模拟情感分数和维度
    """
    # 正面词汇
    positive_words = ['好', '棒', '优秀', '喜欢', '不错', '高端', '性价比', '推荐']
    # 负面词汇
    negative_words = ['差', '不好', '一般', '失望', '问题', '坏', '不推荐']

    # 计算情感得分
    positive_count = sum(1 for word in positive_words if word in review_content)
    negative_count = sum(1 for word in negative_words if word in review_content)

    # 情感得分计算
    sentiment_score = (positive_count - negative_count) / (positive_count + negative_count + 1)
    sentiment_score = max(-1, min(1, sentiment_score))  # 限制在-1到1之间

    # 情感维度（模拟）
    emotion_dimensions = {
        'positive_emotion': max(0, sentiment_score),
        'negative_emotion': max(0, -sentiment_score),
        'length_factor': min(1, len(review_content) / 50),
        'objectivity': 1 - abs(sentiment_score)
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


if __name__ == '__main__':
    seed_reviews()