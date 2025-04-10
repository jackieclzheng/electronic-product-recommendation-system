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
from textblob import TextBlob
# import matplotlib
# matplotlib.use('Agg')  # 设置非交互式后端
#
# # 设置matplotlib中文字体
# matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS中文字体
# matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

import platform
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端
import matplotlib.pyplot as plt


# 根据操作系统选择合适的中文字体
def set_chinese_fonts():
    system = platform.system().lower()

    if system == 'darwin':  # macOS
        matplotlib.rcParams['font.family'] = 'Arial Unicode MS'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif system == 'windows':
        matplotlib.rcParams['font.family'] = 'Microsoft YaHei'
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    elif system == 'linux':
        matplotlib.rcParams['font.family'] = 'WenQuanYi Micro Hei'
        matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
    else:
        # 备选方案
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial']

    # 解决负号显示问题
    matplotlib.rcParams['axes.unicode_minus'] = False


# 在导入 matplotlib 后立即调用
set_chinese_fonts()

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
    
    def analyze_user_reviews(self, product_id):
        """分析产品评论"""
        reviews = UserReview.query.filter_by(product_id=product_id).all()
        
        if not reviews:
            return {
                'review_count': 0,
                'average_rating': 0,
                'average_sentiment': 0,
                'emotion_dimensions': get_default_emotions()
            }

        # 初始化统计数据
        total_emotions = {
            'positive_emotion': 0.0,
            'negative_emotion': 0.0,
            'objectivity': 0.0,
            'length_factor': 0.0
        }
        
        valid_reviews = 0
        total_rating = 0
        total_sentiment = 0
        
        for review in reviews:
            try:
                total_rating += review.rating
                total_sentiment += review.sentiment if review.sentiment else 0
                
                if review.emotion_dimensions:
                    emotions = json.loads(review.emotion_dimensions)
                    for key in total_emotions:
                        if key in emotions:
                            total_emotions[key] += float(emotions[key])
                valid_reviews += 1
                    
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"处理评论 {review.id} 时出错: {str(e)}")
                continue
        
        # 计算平均值
        if valid_reviews > 0:
            average_rating = total_rating / valid_reviews
            average_sentiment = total_sentiment / valid_reviews
            
            for key in total_emotions:
                total_emotions[key] /= valid_reviews
        else:
            average_rating = 0
            average_sentiment = 0
        
        # 生成并保存雷达图
        chart_url = generate_emotion_radar_chart(total_emotions, product_id)
        
        return {
            'review_count': valid_reviews,
            'average_rating': round(average_rating, 2),
            'average_sentiment': round(average_sentiment, 2),
            'emotion_dimensions': total_emotions,
            'emotion_chart_url': chart_url
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
                # 'original_price': p.price,
                # 'final_price': final_price,
                'original_price': round(p.price, 2),  # 保留两位小数
                'final_price': round(final_price, 2),  # 保留两位小数
                'discount_desc': '、'.join(discount_desc) if discount_desc else '无优惠',
                # 'discount_amount': p.price - final_price,
                # 'discount_percentage': (p.price - final_price) / p.price * 100 if p.price > 0 else 0

                'discount_amount': round(p.price - final_price, 2),  # 保留两位小数
                'discount_percentage': round((p.price - final_price) / p.price * 100, 2) if p.price > 0 else 0
            })
        
        # 按最终价格排序
        best_plans.sort(key=lambda x: x['final_price'])
        
        # 生成对比图表
        # platforms = [plan['platform'] for plan in best_plans[:5]]
        # final_prices = [plan['final_price'] for plan in best_plans[:5]]
        # original_prices = [plan['original_price'] for plan in best_plans[:5]]

        # 生成对比图表部分的代码也可以使用 round() 函数
        platforms = [plan['platform'] for plan in best_plans[:5]]
        final_prices = [round(plan['final_price'], 2) for plan in best_plans[:5]]
        original_prices = [round(plan['original_price'], 2) for plan in best_plans[:5]]
        
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

    def analyze_platform_sales(self) -> Dict[str, Any]:
        """分析各平台销售数据
        
        Returns:
            包含平台销售数据分析结果的字典
        """
        try:
            # 查询各平台的销售数据
            platform_sales = db.session.query(
                Product.platform,
                func.count(Product.id).label('product_count'),
                func.sum(ProductSale.sales_volume).label('total_sales'),
                func.avg(Product.price).label('avg_price')
            ).join(
                ProductSale, Product.id == ProductSale.product_id
            ).group_by(
                Product.platform
            ).all()

            # 准备数据
            platforms = []
            sales_volumes = []
            avg_prices = []
            product_counts = []

            for platform, count, sales, price in platform_sales:
                platforms.append(platform)
                product_counts.append(count)
                sales_volumes.append(int(sales or 0))
                avg_prices.append(round(float(price or 0), 2))

            # 创建图表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # 销量柱状图
            bars1 = ax1.bar(platforms, sales_volumes, color='#3498db')
            ax1.set_title('各平台销量对比')
            ax1.set_xlabel('平台')
            ax1.set_ylabel('总销量')
            # 添加数据标签
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')

            # 平均价格柱状图
            bars2 = ax2.bar(platforms, avg_prices, color='#e74c3c')
            ax2.set_title('各平台平均价格对比')
            ax2.set_xlabel('平台')
            ax2.set_ylabel('平均价格 (元)')
            # 添加数据标签
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'¥{height:.2f}',
                        ha='center', va='bottom')

            plt.tight_layout()

            # 保存图表
            chart_filename = f'platform_sales_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
            chart_path = os.path.join(self.charts_folder, chart_filename)
            plt.savefig(chart_path)
            plt.close()

            return {
                'platforms': platforms,
                'sales_volumes': sales_volumes,
                'avg_prices': avg_prices,
                'product_counts': product_counts,
                'chart_url': os.path.join('images', 'charts', chart_filename),
                'total_products': sum(product_counts),
                'total_sales': sum(sales_volumes),
                'avg_total_price': round(sum(avg_prices) / len(avg_prices), 2) if avg_prices else 0
            }
            
        except Exception as e:
            print(f"分析平台销售数据时出错: {str(e)}")
            return {
                'error': f"分析失败: {str(e)}",
                'platforms': [],
                'sales_volumes': [],
                'avg_prices': [],
                'product_counts': [],
                'chart_url': '',
                'total_products': 0,
                'total_sales': 0,
                'avg_total_price': 0
            }

    def analyze_user_behavior(self) -> Dict[str, Any]:
        """分析用户行为数据
        
        Returns:
            包含用户行为分析结果的字典
        """
        try:
            # 查询用户行为数据
            behaviors = db.session.query(
                UserBehavior.behavior_type,
                func.count(UserBehavior.id).label('count')
            ).group_by(
                UserBehavior.behavior_type
            ).all()

            # 准备数据
            behavior_types = []
            counts = []

            for behavior_type, count in behaviors:
                behavior_types.append(behavior_type)
                counts.append(count)

            # 创建图表
            plt.figure(figsize=(10, 6))
            
            # 创建饼图
            plt.pie(counts, labels=behavior_types, autopct='%1.1f%%',
                    colors=['#3498db', '#e74c3c', '#2ecc71', '#f1c40f'])
            plt.title('用户行为分布')
            
            # 保存图表
            chart_filename = f'user_behavior_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
            chart_path = os.path.join(self.charts_folder, chart_filename)
            plt.savefig(chart_path)
            plt.close()

            # 计算转化率
            conversion_rates = {}
            total_users = len(set(db.session.query(UserBehavior.user_id).all()))
            
            if total_users > 0:
                for behavior_type, count in behaviors:
                    conversion_rates[behavior_type] = round((count / total_users) * 100, 2)

            return {
                'behavior_types': behavior_types,
                'counts': counts,
                'total_behaviors': sum(counts),
                'conversion_rates': conversion_rates,
                'chart_url': os.path.join('images', 'charts', chart_filename),
                'total_users': total_users,
                'behavior_distribution': dict(zip(behavior_types, counts))
            }
            
        except Exception as e:
            print(f"分析用户行为数据时出错: {str(e)}")
            return {
                'error': f"分析失败: {str(e)}",
                'behavior_types': [],
                'counts': [],
                'total_behaviors': 0,
                'conversion_rates': {},
                'chart_url': '',
                'total_users': 0,
                'behavior_distribution': {}
            }

    def analyze_product_categories(self) -> Dict[str, Any]:
        """分析产品分类数据
        
        Returns:
            包含产品分类分析结果的字典
        """
        try:
            # 查询各分类的产品数量和销量数据
            category_stats = db.session.query(
                ProductCategory.name,
                func.count(Product.id).label('product_count'),
                func.sum(ProductSale.sales_volume).label('total_sales'),
                func.avg(Product.price).label('avg_price')
            ).join(
                Product, ProductCategory.id == Product.category_id
            ).join(
                ProductSale, Product.id == ProductSale.product_id
            ).group_by(
                ProductCategory.name
            ).all()

            # 准备数据
            categories = []
            product_counts = []
            sales_volumes = []
            avg_prices = []

            for name, count, sales, price in category_stats:
                categories.append(name)
                product_counts.append(count)
                sales_volumes.append(int(sales or 0))
                avg_prices.append(round(float(price or 0), 2))

            # 创建多子图
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

            # 产品数量分布饼图
            ax1.pie(product_counts, labels=categories, autopct='%1.1f%%',
                    colors=['#3498db', '#e74c3c', '#2ecc71', '#f1c40f'])
            ax1.set_title('各分类产品数量分布')

            # 销量柱状图
            bars2 = ax2.bar(categories, sales_volumes, color='#3498db')
            ax2.set_title('各分类总销量对比')
            ax2.set_xlabel('分类')
            ax2.set_ylabel('总销量')
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            # 添加数据标签
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')

            # 平均价格柱状图
            bars3 = ax3.bar(categories, avg_prices, color='#e74c3c')
            ax3.set_title('各分类平均价格对比')
            ax3.set_xlabel('分类')
            ax3.set_ylabel('平均价格 (元)')
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            # 添加数据标签
            for bar in bars3:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'¥{height:.2f}',
                        ha='center', va='bottom')

            plt.tight_layout()

            # 保存图表
            chart_filename = f'category_analysis_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
            chart_path = os.path.join(self.charts_folder, chart_filename)
            plt.savefig(chart_path)
            plt.close()

            return {
                'categories': categories,
                'product_counts': product_counts,
                'sales_volumes': sales_volumes,
                'avg_prices': avg_prices,
                'chart_url': os.path.join('images', 'charts', chart_filename),
                'total_products': sum(product_counts),
                'total_sales': sum(sales_volumes),
                'avg_total_price': round(sum(avg_prices) / len(avg_prices), 2) if avg_prices else 0,
                'category_distribution': dict(zip(categories, product_counts))
            }
            
        except Exception as e:
            print(f"分析产品分类数据时出错: {str(e)}")
            return {
                'error': f"分析失败: {str(e)}",
                'categories': [],
                'product_counts': [],
                'sales_volumes': [],
                'avg_prices': [],
                'chart_url': '',
                'total_products': 0,
                'total_sales': 0,
                'avg_total_price': 0,
                'category_distribution': {}
            }


def analyze_review_emotions(review_text):
    """分析评论文本的情感"""
    try:
        blob = TextBlob(review_text)
        # 获取情感极性（-1到1之间）
        polarity = blob.sentiment.polarity
        # 获取主观性分数（0到1之间）
        subjectivity = blob.sentiment.subjectivity
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'is_positive': polarity > 0,
            'is_negative': polarity < 0,
            'is_neutral': abs(polarity) < 0.1
        }
    except Exception as e:
        print(f"情感分析出错: {str(e)}")
        return {
            'polarity': 0,
            'subjectivity': 0.5,
            'is_positive': False,
            'is_negative': False,
            'is_neutral': True
        }

def generate_emotion_radar_chart(emotion_dimensions, product_id):
    """生成情感雷达图"""
    # 创建图形
    plt.figure(figsize=(8, 8))
    
    # 雷达图的角度
    categories = ['积极情感', '消极情感', '客观程度', '评价详细度']
    num_vars = len(categories)
    
    # 计算角度
    angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
    angles += angles[:1]
    
    # 初始化雷达图
    ax = plt.subplot(111, projection='polar')
    
    # 获取数值
    values = [
        emotion_dimensions.get('positive_emotion', 0),
        emotion_dimensions.get('negative_emotion', 0),
        emotion_dimensions.get('objectivity', 0),
        emotion_dimensions.get('length_factor', 0)
    ]
    values += values[:1]
    
    # 绘制图形
    ax.plot(angles, values, 'o-', linewidth=2, label='情感得分')
    ax.fill(angles, values, alpha=0.25)
    
    # 设置角度标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    # 设置标题
    plt.title('产品评价情感分析雷达图', pad=20)
    
    # 确保static/images目录存在
    os.makedirs('static/images/emotion_charts', exist_ok=True)
    
    # 保存图片
    chart_path = f'images/emotion_charts/emotion_radar_{product_id}.png'
    plt.savefig(f'static/{chart_path}')
    plt.close()
    
    return chart_path
