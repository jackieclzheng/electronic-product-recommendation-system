# 数据分析与可视化模块
# filename: analysis/data_analysis.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import func
import json
from typing import List, Dict, Any, Tuple, Optional
import os
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端

# 导入数据库模型
from models.models import db, Product, ProductSale, UserReview, PlatformDiscount, ShopInfo

class DataAnalysis:
    """数据分析类，提供各种数据分析和可视化功能"""
    
    def __init__(self, static_folder='static'):
        """初始化数据分析类
        
        Args:
            static_folder: 静态文件夹路径，用于保存生成的图表
        """
        self.static_folder = static_folder
        self.charts_folder = os.path.join(static_folder, 'images', 'charts')
        os.makedirs(self.charts_folder, exist_ok=True)
    
    def get_price_trend(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """获取产品价格趋势数据
        
        Args:
            product_id: 产品ID
            days: 天数，默认30天
            
        Returns:
            包含日期和价格数据的字典
        """
        # 计算开始日期
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 查询价格数据
        sales_data = ProductSale.query.filter(
            ProductSale.product_id == product_id,
            ProductSale.date >= start_date,
            ProductSale.date <= end_date
        ).order_by(ProductSale.date).all()
        
        # 整理数据
        dates = [sale.date.strftime('%Y-%m-%d') for sale in sales_data]
        prices = [sale.price for sale in sales_data]
        discount_prices = [sale.discount_price for sale in sales_data]
        
        # 生成图表
        plt.figure(figsize=(10, 6))
        plt.plot(dates, prices, 'b-', label='原价')
        plt.plot(dates, discount_prices, 'r-', label='优惠价')
        plt.xlabel('日期')
        plt.ylabel('价格 (元)')
        plt.title('产品价格趋势')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()
        
        # 保存图表
        chart_filename = f'price_trend_{product_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'dates': dates,
            'prices': prices,
            'discount_prices': discount_prices,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
    
    def compare_platform_prices(self, product_name: str) -> Dict[str, Any]:
        """比较不同平台的产品价格
        
        Args:
            product_name: 产品名称
            
        Returns:
            包含平台和价格数据的字典
        """
        # 查询不同平台的产品价格
        products = Product.query.filter(
            Product.name.like(f'%{product_name}%')
        ).all()
        
        # 按平台分组
        platforms = {}
        for product in products:
            if product.platform not in platforms:
                platforms[product.platform] = []
            platforms[product.platform].append(product.price)
        
        # 计算每个平台的平均价格
        platform_names = list(platforms.keys())
        avg_prices = [sum(prices) / len(prices) for prices in platforms.values()]
        
        # 生成图表
        plt.figure(figsize=(10, 6))
        bars = plt.bar(platform_names, avg_prices, color=['#3498db', '#e74c3c', '#2ecc71'])
        plt.xlabel('平台')
        plt.ylabel('平均价格 (元)')
        plt.title(f'{product_name} 各平台价格对比')
        
        # 在柱状图上添加价格标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 50,
                    f'¥{height:.2f}',
                    ha='center', va='bottom')
        
        # 保存图表
        chart_filename = f'platform_compare_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'platforms': platform_names,
            'prices': avg_prices,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
    
    def analyze_discount_effect(self) -> Dict[str, Any]:
        """分析优惠券效果
        
        Returns:
            包含优惠类型和销量数据的字典
        """
        # 获取所有产品的销量和优惠信息
        products = Product.query.all()
        
        # 按优惠类型分组
        discount_types = {
            '无优惠': {'count': 0, 'sales': 0},
            '满减': {'count': 0, 'sales': 0},
            '折扣': {'count': 0, 'sales': 0},
            '消费券': {'count': 0, 'sales': 0},
            '多重优惠': {'count': 0, 'sales': 0}
        }
        
        for product in products:
            # 获取产品的优惠信息
            discounts = PlatformDiscount.query.filter_by(product_id=product.id).all()
            
            # 获取产品的总销量
            sales = db.session.query(func.sum(ProductSale.sales_volume)).filter(
                ProductSale.product_id == product.id
            ).scalar() or 0
            
            # 根据优惠类型分类
            if not discounts:
                discount_types['无优惠']['count'] += 1
                discount_types['无优惠']['sales'] += sales
            elif len(discounts) > 1:
                discount_types['多重优惠']['count'] += 1
                discount_types['多重优惠']['sales'] += sales
            else:
                discount_type = discounts[0].discount_type
                if discount_type in discount_types:
                    discount_types[discount_type]['count'] += 1
                    discount_types[discount_type]['sales'] += sales
                else:
                    discount_types['其他']['count'] += 1
                    discount_types['其他']['sales'] += sales
        
        # 计算每种优惠类型的平均销量
        for discount_type in discount_types:
            if discount_types[discount_type]['count'] > 0:
                discount_types[discount_type]['avg_sales'] = discount_types[discount_type]['sales'] / discount_types[discount_type]['count']
            else:
                discount_types[discount_type]['avg_sales'] = 0
        
        # 准备图表数据
        types = list(discount_types.keys())
        avg_sales = [discount_types[t]['avg_sales'] for t in types]
        
        # 生成图表
        plt.figure(figsize=(12, 7))
        bars = plt.bar(types, avg_sales, color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'])
        plt.xlabel('优惠类型')
        plt.ylabel('平均销量')
        plt.title('不同优惠类型对销量的影响')
        
        # 在柱状图上添加销量标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{height:.0f}',
                    ha='center', va='bottom')
        
        # 保存图表
        chart_filename = f'discount_effect_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'discount_types': types,
            'avg_sales': avg_sales,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
    
    def analyze_stackable_discounts(self) -> Dict[str, Any]:
        """分析可叠加与不可叠加优惠的效果
        
        Returns:
            包含叠加类型和销量数据的字典
        """
        # 获取所有产品的销量和优惠信息
        products = Product.query.all()
        
        # 按叠加类型分组
        stackable_types = {
            '无优惠': {'count': 0, 'sales': 0},
            '不可叠加优惠': {'count': 0, 'sales': 0},
            '可叠加优惠': {'count': 0, 'sales': 0}
        }
        
        for product in products:
            # 获取产品的优惠信息
            discounts = PlatformDiscount.query.filter_by(product_id=product.id).all()
            
            # 获取产品的总销量
            sales = db.session.query(func.sum(ProductSale.sales_volume)).filter(
                ProductSale.product_id == product.id
            ).scalar() or 0
            
            # 根据叠加类型分类
            if not discounts:
                stackable_types['无优惠']['count'] += 1
                stackable_types['无优惠']['sales'] += sales
            elif any(discount.stackable for discount in discounts):
                stackable_types['可叠加优惠']['count'] += 1
                stackable_types['可叠加优惠']['sales'] += sales
            else:
                stackable_types['不可叠加优惠']['count'] += 1
                stackable_types['不可叠加优惠']['sales'] += sales
        
        # 计算每种叠加类型的平均销量
        for stackable_type in stackable_types:
            if stackable_types[stackable_type]['count'] > 0:
                stackable_types[stackable_type]['avg_sales'] = stackable_types[stackable_type]['sales'] / stackable_types[stackable_type]['count']
            else:
                stackable_types[stackable_type]['avg_sales'] = 0
        
        # 准备图表数据
        types = list(stackable_types.keys())
        avg_sales = [stackable_types[t]['avg_sales'] for t in types]
        
        # 生成图表
        plt.figure(figsize=(10, 6))
        bars = plt.bar(types, avg_sales, color=['#3498db', '#e74c3c', '#2ecc71'])
        plt.xlabel('优惠叠加类型')
        plt.ylabel('平均销量')
        plt.title('优惠叠加类型对销量的影响')
        
        # 在柱状图上添加销量标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{height:.0f}',
                    ha='center', va='bottom')
        
        # 保存图表
        chart_filename = f'stackable_effect_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'stackable_types': types,
            'avg_sales': avg_sales,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
    
    def analyze_shop_discount_relation(self) -> Dict[str, Any]:
        """分析店铺优惠券数量与销量的关系
        
        Returns:
            包含分析结果的字典
        """
        # 获取所有店铺信息
        shops = ShopInfo.query.all()
        
        # 提取数据
        discount_counts = [shop.discount_count for shop in shops]
        sales_volumes = [shop.sales_volume for shop in shops]
        shop_names = [shop.shop_name for shop in shops]
        
        # 计算相关系数
        correlation = np.corrcoef(discount_counts, sales_volumes)[0, 1]
        
        # 生成散点图
        plt.figure(figsize=(12, 8))
        plt.scatter(discount_counts, sales_volumes, alpha=0.7)
        
        # 添加趋势线
        z = np.polyfit(discount_counts, sales_volumes, 1)
        p = np.poly1d(z)
        plt.plot(discount_counts, p(discount_counts), "r--")
        
        # 添加标签
        for i, txt in enumerate(shop_names):
            plt.annotate(txt, (discount_counts[i], sales_volumes[i]), fontsize=8)
        
        plt.xlabel('优惠券数量')
        plt.ylabel('销售量')
        plt.title('店铺优惠券数量与销量的关系 (相关系数: {:.2f})'.format(correlation))
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 保存图表
        chart_filename = f'shop_discount_relation_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'correlation': correlation,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
    
    def analyze_user_reviews(self, product_id: int) -> Dict[str, Any]:
        """分析用户评价
        
        Args:
            product_id: 产品ID
            
        Returns:
            包含评价分析结果的字典
        """
        # 获取产品评价
        reviews = UserReview.query.filter_by(product_id=product_id).all()
        
        if not reviews:
            return {
                'average_rating': 0,
                'rating_counts': [0, 0, 0, 0, 0],
                'positive_ratio': 0,
                'chart_url': ''
            }
        
        # 计算平均评分
        average_rating = sum(review.rating for review in reviews) / len(reviews)
        
        # 统计各评分数量
        rating_counts = [0, 0, 0, 0, 0]  # 1-5星
        for review in reviews:
            if 1 <= review.rating <= 5:
                rating_counts[review.rating - 1] += 1
        
        # 计算正面评价比例 (4-5星)
        positive_count = rating_counts[3] + rating_counts[4]
        positive_ratio = positive_count / len(reviews) if reviews else 0
        
        # 生成评分分布图
        plt.figure(figsize=(10, 6))
        bars = plt.bar(['1星', '2星', '3星', '4星', '5星'], rating_counts, color=['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60'])
        plt.xlabel('评分')
        plt.ylabel('数量')
        plt.title('产品评分分布')
        
        # 在柱状图上添加数量标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height}',
                    ha='center', va='bottom')
        
        # 保存图表
        chart_filename = f'review_analysis_{product_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'average_rating': average_rating,
            'rating_counts': rating_counts,
            'positive_ratio': positive_ratio,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
    
    def get_optimal_purchase_plan(self, product_id: int) -> Dict[str, Any]:
        """获取最优购买方案
        
        Args:
            product_id: 产品ID
            
        Returns:
            包含最优购买方案的字典
        """
        # 获取产品信息
        product = Product.query.get(product_id)
        if not product:
            return {'error': '产品不存在'}
        
        # 获取产品在各平台的价格和优惠信息
        similar_products = Product.query.filter(
            Product.name.like(f'%{product.name}%'),
            Product.id != product_id
        ).all()
        
        # 合并当前产品和类似产品
        all_products = [product] + similar_products
        
        # 计算每个产品的最终价格
        best_plans = []
        for p in all_products:
            # 获取产品的优惠信息
            discounts = PlatformDiscount.query.filter_by(product_id=p.id).all()
            
            # 计算最终价格
            final_price = p.price
            discount_desc = []
            
            for discount in discounts:
                if discount.discount_type == '满减' and p.price >= discount.min_purchase:
                    final_price -= discount.discount_value
                    discount_desc.append(f'满{discount.min_purchase}减{discount.discount_value}')
                elif discount.discount_type == '折扣':
                    discount_amount = p.price * (1 - discount.discount_value / 10)
                    final_price -= discount_amount
                    discount_desc.append(f'{discount.discount_value}折')
                elif discount.discount_type == '消费券':
                    final_price -= discount.discount_value
                    discount_desc.append(f'消费券减{discount.discount_value}')
            
            # 添加到方案列表
            best_plans.append({
                'product_id': p.id,
                'product_name': p.name,
                'platform': p.platform,
                'original_price': p.price,
                'final_price': final_price,
                'discount_desc': '、'.join(discount_desc) if discount_desc else '无优惠',
                'discount_amount': p.price - final_price,
                'discount_percentage': (p.price - final_price) / p.price * 100 if p.price > 0 else 0
            })
        
        # 按最终价格排序
        best_plans.sort(key=lambda x: x['final_price'])
        
        # 生成对比图表
        platforms = [plan['platform'] for plan in best_plans[:5]]
        final_prices = [plan['final_price'] for plan in best_plans[:5]]
        original_prices = [plan['original_price'] for plan in best_plans[:5]]
        
        plt.figure(figsize=(12, 7))
        x = np.arange(len(platforms))
        width = 0.35
        
        plt.bar(x - width/2, original_prices, width, label='原价', color='#3498db')
        plt.bar(x + width/2, final_prices, width, label='优惠后价格', color='#e74c3c')
        
        plt.xlabel('平台')
        plt.ylabel('价格 (元)')
        plt.title('各平台最终价格对比')
        plt.xticks(x, platforms)
        plt.legend()
        
        # 添加价格标签
        for i, v in enumerate(original_prices):
            plt.text(i - width/2, v + 50, f'¥{v:.2f}', ha='center')
        
        for i, v in enumerate(final_prices):
            plt.text(i + width/2, v + 50, f'¥{v:.2f}', ha='center')
        
        # 保存图表
        chart_filename = f'optimal_plan_{product_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        chart_path = os.path.join(self.charts_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        return {
            'best_plans': best_plans,
            'chart_url': os.path.join('images', 'charts', chart_filename)
        }
