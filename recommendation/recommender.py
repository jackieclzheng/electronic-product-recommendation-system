# 产品推荐系统
# filename: recommendation/recommender.py

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from sqlalchemy import func, or_
from typing import List, Dict, Any, Tuple, Optional
import json
import os
from datetime import datetime, timedelta

# 导入数据库模型
from models.models import db, Product, UserBehavior, UserReview, ProductSale, PlatformDiscount

class ProductRecommender:
    """产品推荐系统，提供多种推荐算法"""
    
    def __init__(self):
        """初始化推荐系统"""
        self.user_item_matrix = None
        self.item_similarity_matrix = None
        self.item_features_matrix = None
        self.item_ids = []
        self.user_ids = []
    
    def train_model(self):
        """训练推荐模型，构建用户-物品矩阵和物品相似度矩阵"""
        # 获取所有用户行为数据
        behaviors = UserBehavior.query.all()
        
        # 如果没有足够的数据，则不训练模型
        if len(behaviors) < 10:
            print("数据不足，无法训练模型")
            return
        
        # 构建用户-物品矩阵
        user_ids = sorted(list(set([b.user_id for b in behaviors])))
        item_ids = sorted(list(set([b.product_id for b in behaviors])))
        
        # 保存ID映射
        self.user_ids = user_ids
        self.item_ids = item_ids
        
        # 创建用户-物品交互矩阵
        user_item_data = []
        for b in behaviors:
            # 根据行为类型赋予不同权重
            weight = 1.0
            if b.behavior_type == '浏览':
                weight = 1.0
            elif b.behavior_type == '收藏':
                weight = 2.0
            elif b.behavior_type == '加购':
                weight = 3.0
            elif b.behavior_type == '购买':
                weight = 5.0
            
            user_idx = user_ids.index(b.user_id)
            item_idx = item_ids.index(b.product_id)
            user_item_data.append((user_idx, item_idx, weight))
        
        # 创建稀疏矩阵
        rows, cols, data = zip(*user_item_data) if user_item_data else ([], [], [])
        self.user_item_matrix = csr_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))
        
        # 计算物品相似度矩阵
        if len(item_ids) > 1:
            self.item_similarity_matrix = cosine_similarity(self.user_item_matrix.T)
        
        # 构建物品特征矩阵
        self._build_item_features_matrix()
        
        print(f"模型训练完成: {len(user_ids)}个用户, {len(item_ids)}个物品")
    
    def _build_item_features_matrix(self):
        """构建物品特征矩阵，用于基于内容的推荐"""
        if not self.item_ids:
            return
        
        # 获取所有产品信息
        products = Product.query.filter(Product.id.in_(self.item_ids)).all()
        
        # 提取产品特征
        features = []
        for product_id in self.item_ids:
            product = next((p for p in products if p.id == product_id), None)
            if not product:
                # 如果找不到产品，使用零向量
                features.append(np.zeros(10))
                continue
            
            # 提取产品特征
            feature_vector = []
            
            # 类别特征 (one-hot编码)
            category_id = product.category_id or 0
            category_feature = [0, 0, 0]  # 假设有3个类别
            if 1 <= category_id <= 3:
                category_feature[category_id - 1] = 1
            feature_vector.extend(category_feature)
            
            # 价格特征 (归一化)
            max_price = max([p.price for p in products if p.price is not None] or [1])
            price_feature = product.price / max_price if product.price else 0
            feature_vector.append(price_feature)
            
            # 平台特征 (one-hot编码)
            platforms = list(set([p.platform for p in products if p.platform]))
            platform_feature = [0] * len(platforms)
            if product.platform in platforms:
                platform_feature[platforms.index(product.platform)] = 1
            feature_vector.extend(platform_feature)
            
            # 规格特征
            specs = product.specifications
            # 提取一些通用特征，如内存、存储等
            memory = specs.get('内存', 0)
            if isinstance(memory, str):
                memory = float(''.join(filter(str.isdigit, memory))) if any(c.isdigit() for c in memory) else 0
            feature_vector.append(memory / 16)  # 假设最大16GB
            
            storage = specs.get('存储', 0)
            if isinstance(storage, str):
                storage = float(''.join(filter(str.isdigit, storage))) if any(c.isdigit() for c in storage) else 0
            feature_vector.append(storage / 1024)  # 假设最大1TB
            
            # 确保特征向量长度一致
            while len(feature_vector) < 10:
                feature_vector.append(0)
            
            features.append(feature_vector[:10])  # 截断或填充到10维
        
        # 转换为numpy数组
        self.item_features_matrix = np.array(features)
        
        # 计算基于内容的物品相似度
        if len(self.item_ids) > 1:
            self.content_similarity_matrix = cosine_similarity(self.item_features_matrix)
    
    def get_user_recommendations(self, user_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """基于协同过滤为用户推荐产品
        
        Args:
            user_id: 用户ID
            n: 推荐数量
            
        Returns:
            推荐产品列表
        """
        # 如果模型未训练，返回热门产品
        if self.user_item_matrix is None or user_id not in self.user_ids:
            return self.get_popular_products(n)
        
        # 获取用户索引
        user_idx = self.user_ids.index(user_id)
        
        # 获取用户已交互的物品
        user_interactions = self.user_item_matrix[user_idx].toarray().flatten()
        interacted_items = set(np.where(user_interactions > 0)[0])
        
        # 计算推荐分数
        scores = np.zeros(len(self.item_ids))
        
        # 对于用户交互过的每个物品
        for item_idx in interacted_items:
            # 获取相似物品
            similar_items = self.item_similarity_matrix[item_idx]
            # 加权计算推荐分数
            scores += similar_items * user_interactions[item_idx]
        
        # 将已交互的物品分数设为0
        scores[list(interacted_items)] = 0
        
        # 获取分数最高的n个物品
        recommended_item_indices = np.argsort(scores)[-n:][::-1]
        recommended_item_ids = [self.item_ids[idx] for idx in recommended_item_indices]
        
        # 获取推荐产品详情
        recommended_products = []
        for product_id in recommended_item_ids:
            product = Product.query.get(product_id)
            if product:
                recommended_products.append({
                    'id': product.id,
                    'name': product.name,
                    'brand': product.brand,
                    'price': product.price,
                    'platform': product.platform,
                    'image_url': product.image_url,
                    'recommendation_type': '个性化推荐'
                })
        
        # 如果推荐数量不足，补充热门产品
        if len(recommended_products) < n:
            popular_products = self.get_popular_products(n - len(recommended_products))
            recommended_products.extend(popular_products)
        
        return recommended_products
    
    def get_similar_products(self, product_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """获取与指定产品相似的产品
        
        Args:
            product_id: 产品ID
            n: 推荐数量
            
        Returns:
            相似产品列表
        """
        # 如果模型未训练或产品不在模型中，使用基于内容的推荐
        if self.item_similarity_matrix is None or product_id not in self.item_ids:
            return self._get_content_based_recommendations(product_id, n)
        
        # 获取产品索引
        item_idx = self.item_ids.index(product_id)
        
        # 获取相似产品
        similar_scores = self.item_similarity_matrix[item_idx]
        
        # 排除自身
        similar_scores[item_idx] = 0
        
        # 获取分数最高的n个物品
        similar_item_indices = np.argsort(similar_scores)[-n:][::-1]
        similar_item_ids = [self.item_ids[idx] for idx in similar_item_indices]
        
        # 获取相似产品详情
        similar_products = []
        for similar_id in similar_item_ids:
            product = Product.query.get(similar_id)
            if product:
                similar_products.append({
                    'id': product.id,
                    'name': product.name,
                    'brand': product.brand,
                    'price': product.price,
                    'platform': product.platform,
                    'image_url': product.image_url,
                    'recommendation_type': '相似产品'
                })
        
        # 如果相似产品数量不足，补充基于内容的推荐
        if len(similar_products) < n:
            content_recommendations = self._get_content_based_recommendations(product_id, n - len(similar_products))
            similar_products.extend(content_recommendations)
        
        return similar_products
    
    def _get_content_based_recommendations(self, product_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """基于内容为产品推荐相似产品
        
        Args:
            product_id: 产品ID
            n: 推荐数量
            
        Returns:
            相似产品列表
        """
        # 获取产品信息
        product = Product.query.get(product_id)
        if not product:
            return []
        
        # 获取同类别的产品
        similar_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product_id
        ).all()
        
        # 如果没有足够的同类别产品，返回热门产品
        if len(similar_products) < n:
            return self.get_popular_products(n)
        
        # 计算相似度分数
        scores = []
        for p in similar_products:
            # 基于品牌、价格等计算相似度
            score = 0
            
            # 品牌相似度
            if p.brand == product.brand:
                score += 3
            
            # 价格相似度 (归一化差异)
            if p.price and product.price:
                price_diff = abs(p.price - product.price) / max(p.price, product.price)
                score += (1 - price_diff) * 2
            
            # 平台相似度
            if p.platform == product.platform:
                score += 1
            
            # 规格相似度
            p_specs = p.specifications
            product_specs = product.specifications
            
            common_keys = set(p_specs.keys()) & set(product_specs.keys())
            if common_keys:
                for key in common_keys:
                    if p_specs[key] == product_specs[key]:
                        score += 0.5
            
            scores.append((p, score))
        
        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 获取前n个产品
        recommended_products = []
        for p, score in scores[:n]:
            recommended_products.append({
                'id': p.id,
                'name': p.name,
                'brand': p.brand,
                'price': p.price,
                'platform': p.platform,
                'image_url': p.image_url,
                'recommendation_type': '相似产品'
            })
        
        return recommended_products
    
    def get_popular_products(self, n: int = 5) -> List[Dict[str, Any]]:
        """获取热门产品
        
        Args:
            n: 推荐数量
            
        Returns:
            热门产品列表
        """
        # 基于评价数量和评分获取热门产品
        popular_products = db.session.query(
            Product, func.count(UserReview.id).label('review_count'),
            func.avg(UserReview.rating).label('avg_rating')
        ).outerjoin(UserReview).group_by(Product.id).order_by(
            func.avg(UserReview.rating).desc(),
            func.count(UserReview.id).desc()
        ).limit(n*2).all()
        
        # 如果没有足够的评价数据，基于销量获取热门产品
        if len(popular_products) < n:
            sales_products = db.session.query(
                Product, func.sum(ProductSale.sales_volume).label('total_sales')
            ).outerjoin(ProductSale).group_by(Product.id).order_by(
                func.sum(ProductSale.sales_volume).desc()
            ).limit(n*2).all()
            
            # 合并两个列表
            all_products = list(popular_products)
            for p, sales in sales_products:
                if p not in [x[0] for x in all_products]:
                    all_products.append((p, 0, 0))
            
            popular_products = all_products
        
        # 格式化结果
        result = []
        for product, review_count, avg_rating in popular_products[:n]:
            result.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'price': product.price,
                'platform': product.platform,
                'image_url': product.image_url,
                'review_count': review_count,
                'avg_rating': float(avg_rating) if avg_rating else 0,
                'recommendation_type': '热门产品'
            })
        
        return result
    
    def get_discount_recommendations(self, n: int = 5) -> List[Dict[str, Any]]:
        """获取优惠力度最大的产品推荐
        
        Args:
            n: 推荐数量
            
        Returns:
            优惠产品列表
        """
        # 获取有优惠的产品
        products_with_discounts = db.session.query(
            Product, PlatformDiscount
        ).join(PlatformDiscount).all()
        
        # 计算优惠力度
        discount_products = []
        for product, discount in products_with_discounts:
            # 计算优惠金额
            discount_amount = 0
            if discount.discount_type == '满减' and product.price >= discount.min_purchase:
                discount_amount = discount.discount_value
            elif discount.discount_type == '折扣':
                discount_amount = product.price * (1 - discount.discount_value / 10)
            elif discount.discount_type == '消费券':
                discount_amount = discount.discount_value
            
            # 计算优惠比例
            discount_percentage = discount_amount / product.price * 100 if product.price > 0 else 0
            
            discount_products.append({
                'product': product,
                'discount': discount,
                'discount_amount': discount_amount,
                'discount_percentage': discount_percentage
            })
        
        # 按优惠比例排序
        discount_products.sort(key=lambda x: x['discount_percentage'], reverse=True)
        
        # 获取前n个产品
        result = []
        for item in discount_products[:n]:
            product = item['product']
            discount = item['discount']
            
            # 格式化优惠描述
            discount_desc = ''
            if discount.discount_type == '满减':
                discount_desc = f'满{discount.min_purchase}减{discount.discount_value}'
            elif discount.discount_type == '折扣':
                discount_desc = f'{discount.discount_value}折'
            elif discount.discount_type == '消费券':
                discount_desc = f'减{discount.discount_value}元'
            
            result.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'price': product.price,
                'platform': product.platform,
                'image_url': product.image_url,
                'discount_amount': item['discount_amount'],
                'discount_percentage': item['discount_percentage'],
                'discount_desc': discount_desc,
                'recommendation_type': '特惠产品'
            })
        
        # 如果优惠产品不足，补充热门产品
        if len(result) < n:
            popular_products = self.get_popular_products(n - len(result))
            result.extend(popular_products)
        
        return result
