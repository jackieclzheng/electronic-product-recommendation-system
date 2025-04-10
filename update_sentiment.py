from app import app
from models.models import db, UserReview
from data_seeder import generate_sentiment_analysis
import json

def get_default_emotions():
    """返回默认的情感维度数据"""
    return {
        'positive_emotion': 0.0,
        'negative_emotion': 0.0,
        'objectivity': 0.5,
        'length_factor': 0.0
    }

def update_reviews_sentiment():
    """更新所有评论的情感分析数据"""
    with app.app_context():
        reviews = UserReview.query.all()
        updated_count = 0
        
        print("开始更新评论情感分析...")
        
        for review in reviews:
            try:
                # 使用新的情感分析函数重新分析
                sentiment_score, emotion_dimensions = generate_sentiment_analysis(review.content)
                
                # 确保所有必要的情感维度都存在
                default_emotions = get_default_emotions()
                for key in default_emotions:
                    if key not in emotion_dimensions:
                        emotion_dimensions[key] = default_emotions[key]
                
                # 更新评论数据
                review.sentiment = sentiment_score
                review.sentiment_score = sentiment_score
                review.emotion_dimensions = json.dumps(emotion_dimensions)
                updated_count += 1
                
            except Exception as e:
                print(f"处理评论ID {review.id} 时出错: {str(e)}")
                # 使用默认值
                review.sentiment = 0.0
                review.sentiment_score = 0.0
                review.emotion_dimensions = json.dumps(get_default_emotions())
            
            # 每100条提交一次
            if updated_count % 100 == 0:
                db.session.commit()
                print(f"已更新 {updated_count} 条评论")
        
        # 提交剩余更改
        db.session.commit()
        print(f"完成更新！共更新了 {updated_count} 条评论的情感分析结果")

if __name__ == '__main__':
    update_reviews_sentiment()