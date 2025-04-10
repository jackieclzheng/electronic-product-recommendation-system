# init_test_data.py
from app import app
from models.models import db, User, Product, ProductCategory, UserBehavior, UserReview, ProductSale, PlatformDiscount, \
    ShopInfo
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import json

def init_data(app):
    """初始化基础数据"""
    with app.app_context():
        print("开始生成测试数据...")

        # 清空相关表数据
        print("清空现有数据...")
        UserBehavior.query.delete()
        UserReview.query.delete()
        ProductSale.query.delete()
        PlatformDiscount.query.delete()
        ShopInfo.query.delete()
        Product.query.delete()
        User.query.delete()
        ProductCategory.query.delete()

        # 添加产品分类
        print("创建产品分类...")
        categories = []
        for name, desc in [
            ('手机', '智能手机类别，各品牌最新款手机，性能卓越'),
            ('平板', '平板电脑类别，轻薄便携，适合娱乐和工作'),
            ('电脑', '笔记本和台式电脑，高性能办公与游戏设备')
        ]:
            category = ProductCategory(name=name, description=desc, created_at=datetime.now())
            db.session.add(category)
            categories.append(category)
        db.session.commit()

        # 添加测试用户
        print("创建测试用户...")
        users = []
        for i in range(1, 21):  # 创建20个测试用户
            user = User(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password_hash=generate_password_hash(f'password{i}'),
                register_time=datetime.now() - timedelta(days=random.randint(0, 60)),
                last_login=datetime.now() - timedelta(days=random.randint(0, 10))
            )
            db.session.add(user)
            users.append(user)

        # 创建管理员用户
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            register_time=datetime.now() - timedelta(days=90),
            last_login=datetime.now()
        )
        db.session.add(admin)
        users.append(admin)
        db.session.commit()

        # 添加测试产品
        print("创建测试产品...")
        products = []
        platforms = ['京东', '天猫', '苏宁', '拼多多']

        # 手机产品数据
        phone_data = [
            ('iPhone 15 Pro', '苹果', 'A17 Pro', 7999,
             '{"屏幕尺寸":"6.1英寸","内存":"8GB","存储":"256GB","处理器":"A17 Pro","电池":"3274mAh"}'),
            ('iPhone 14', '苹果', 'A15', 5999, '{"屏幕尺寸":"6.1英寸","内存":"6GB","存储":"128GB","处理器":"A15","电池":"3279mAh"}'),
            ('Galaxy S23 Ultra', '三星', 'S23', 8999,
             '{"屏幕尺寸":"6.8英寸","内存":"12GB","存储":"256GB","处理器":"骁龙8 Gen 2","电池":"5000mAh"}'),
            (
            'Galaxy S22+', '三星', 'S22+', 6999, '{"屏幕尺寸":"6.6英寸","内存":"8GB","存储":"128GB","处理器":"骁龙8 Gen 1","电池":"4500mAh"}'),
            ('Mate 60 Pro', '华为', 'Mate60', 6999,
             '{"屏幕尺寸":"6.8英寸","内存":"12GB","存储":"512GB","处理器":"麒麟9000S","电池":"5000mAh"}'),
            ('P60 Pro', '华为', 'P60', 5988, '{"屏幕尺寸":"6.6英寸","内存":"8GB","存储":"256GB","处理器":"骁龙8+","电池":"4815mAh"}'),
            (
            'Redmi K60', '小米', 'K60', 2699, '{"屏幕尺寸":"6.67英寸","内存":"12GB","存储":"256GB","处理器":"骁龙8+ Gen 1","电池":"5500mAh"}'),
            ('小米13', '小米', '13', 3999, '{"屏幕尺寸":"6.36英寸","内存":"8GB","存储":"128GB","处理器":"骁龙8 Gen 2","电池":"4500mAh"}'),
            ('Reno10 Pro+', 'OPPO', 'Reno10', 3899,
             '{"屏幕尺寸":"6.74英寸","内存":"12GB","存储":"256GB","处理器":"骁龙8+ Gen 1","电池":"4700mAh"}'),
            ('Find X6 Pro', 'OPPO', 'FindX6', 5999,
             '{"屏幕尺寸":"6.82英寸","内存":"12GB","存储":"256GB","处理器":"骁龙8 Gen 2","电池":"5000mAh"}')
        ]

        # 平板产品数据
        tablet_data = [
            ('iPad Pro 2022', '苹果', 'M2', 6799, '{"屏幕尺寸":"11英寸","内存":"8GB","存储":"256GB","处理器":"M2","电池":"7538mAh"}'),
            ('iPad Air', '苹果', 'M1', 4799, '{"屏幕尺寸":"10.9英寸","内存":"8GB","存储":"64GB","处理器":"M1","电池":"7606mAh"}'),
            ('Galaxy Tab S9 Ultra', '三星', 'TabS9', 7999,
             '{"屏幕尺寸":"14.6英寸","内存":"12GB","存储":"256GB","处理器":"骁龙8 Gen 2","电池":"11200mAh"}'),
            ('Galaxy Tab S8+', '三星', 'TabS8+', 5999,
             '{"屏幕尺寸":"12.4英寸","内存":"8GB","存储":"128GB","处理器":"骁龙8 Gen 1","电池":"10090mAh"}'),
            ('MatePad Pro', '华为', 'MatePad', 4699, '{"屏幕尺寸":"11英寸","内存":"8GB","存储":"128GB","处理器":"麒麟9000","电池":"7250mAh"}'),
            ('MatePad 11', '华为', 'MatePad11', 2299,
             '{"屏幕尺寸":"10.95英寸","内存":"6GB","存储":"128GB","处理器":"骁龙865","电池":"7250mAh"}'),
            ('Xiaomi Pad 6 Pro', '小米', 'Pad6Pro', 2499,
             '{"屏幕尺寸":"11英寸","内存":"8GB","存储":"128GB","处理器":"骁龙8+ Gen 1","电池":"8600mAh"}'),
            ('Xiaomi Pad 6', '小米', 'Pad6', 1899, '{"屏幕尺寸":"11英寸","内存":"6GB","存储":"128GB","处理器":"骁龙870","电池":"8840mAh"}')
        ]

        # 电脑产品数据
        computer_data = [
            ('MacBook Pro 14"', '苹果', 'M2 Pro', 14999,
             '{"屏幕尺寸":"14.2英寸","内存":"16GB","存储":"512GB","处理器":"M2 Pro","电池":"70Wh"}'),
            ('MacBook Air', '苹果', 'M2', 9499, '{"屏幕尺寸":"13.6英寸","内存":"8GB","存储":"256GB","处理器":"M2","电池":"52.6Wh"}'),
            ('ThinkPad X1 Carbon', '联想', 'X1C', 9999,
             '{"屏幕尺寸":"14英寸","内存":"16GB","存储":"512GB","处理器":"i7-1165G7","电池":"57Wh"}'),
            ('ThinkPad T14s', '联想', 'T14s', 6999, '{"屏幕尺寸":"14英寸","内存":"16GB","存储":"512GB","处理器":"i5-1135G7","电池":"57Wh"}'),
            ('XPS 15', '戴尔', 'XPS15', 12999, '{"屏幕尺寸":"15.6英寸","内存":"16GB","存储":"512GB","处理器":"i7-12700H","电池":"86Wh"}'),
            (
            'XPS 13 Plus', '戴尔', 'XPS13+', 9999, '{"屏幕尺寸":"13.4英寸","内存":"16GB","存储":"512GB","处理器":"i7-1260P","电池":"55Wh"}'),
            ('华为 MateBook X Pro', '华为', 'MateBookXPro', 9999,
             '{"屏幕尺寸":"14.2英寸","内存":"16GB","存储":"1TB","处理器":"i7-1260P","电池":"60Wh"}'),
            ('华为 MateBook 14', '华为', 'MateBook14', 5699,
             '{"屏幕尺寸":"14英寸","内存":"16GB","存储":"512GB","处理器":"i5-12500H","电池":"56Wh"}'),
            ('RedmiBook Pro 15', '小米', 'RedmiBookPro', 5499,
             '{"屏幕尺寸":"15.6英寸","内存":"16GB","存储":"512GB","处理器":"i5-12450H","电池":"72Wh"}'),
            ('小米笔记本 Pro X', '小米', 'ProX', 7499, '{"屏幕尺寸":"15.6英寸","内存":"16GB","存储":"512GB","处理器":"i7-11370H","电池":"80Wh"}')
        ]

        # 创建店铺信息
        print("创建店铺信息...")
        shops = []
        shop_names = {
            '京东': ['京东自营', '京东电器旗舰店', '数码电器专营店', '京东电子旗舰店'],
            '天猫': ['天猫官方旗舰店', '数码电子旗舰店', '天猫电器专营店', '品牌官方旗舰店'],
            '苏宁': ['苏宁自营', '苏宁电器旗舰店', '苏宁易购官方店', '电子数码专营'],
            '拼多多': ['拼多多官方旗舰店', '电子数码优选', '品牌折扣店', '好货优选店']
        }

        for platform, names in shop_names.items():
            for name in names:
                shop = ShopInfo(
                    platform=platform,
                    shop_name=name,
                    shop_id=f"{platform}_{random.randint(10000, 99999)}",
                    rating=random.uniform(4.0, 5.0),
                    sales_volume=random.randint(5000, 50000),
                    discount_count=random.randint(5, 20),
                    created_at=datetime.now() - timedelta(days=random.randint(90, 180)),
                    updated_at=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                db.session.add(shop)
                shops.append(shop)
        db.session.commit()

        # 保存所有产品
        print("创建产品和价格数据...")
        for category_idx, data in enumerate([phone_data, tablet_data, computer_data]):
            category = categories[category_idx]
            for item in data:
                name, brand, model, base_price, specs = item
                # 在这里遍历平台列表
                for current_platform in platforms:
                    # 随机选择店铺
                    platform_shops = [s for s in shops if s.platform == current_platform]
                    shop = random.choice(platform_shops) if platform_shops else None

                    # 随机价格变动 (±5%)
                    price_var = base_price * random.uniform(0.95, 1.05)

                    product = Product(
                        name=name,
                        brand=brand,
                        model=model,
                        price=round(price_var, 2),
                        platform=current_platform,  # 使用当前平台
                        spec_json=specs,
                        category_id=category.id,
                        image_url=f'/static/images/category_{category.name}.jpg',
                        created_at=datetime.now() - timedelta(days=random.randint(0, 90)),
                        updated_at=datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    db.session.add(product)
                    products.append(product)

        db.session.commit()
        print(f"已创建 {len(products)} 个产品")

        # 添加用户行为数据
        print("创建用户行为数据...")
        behavior_types = ['浏览', '收藏', '加购', '购买']
        behavior_weights = {'浏览': 10, '收藏': 3, '加购': 2, '购买': 1}  # 权重，浏览行为最多

        total_behaviors = 0
        for user in users:
            # 每个用户与多个产品交互
            num_interactions = random.randint(10, 30)
            interaction_products = random.sample(products, min(num_interactions, len(products)))

            for product in interaction_products:
                # 根据权重随机选择行为类型
                behavior_type = random.choices(
                    population=list(behavior_weights.keys()),
                    weights=list(behavior_weights.values()),
                    k=1
                )[0]

                # 创建行为记录
                behavior = UserBehavior(
                    user_id=user.id,
                    product_id=product.id,
                    behavior_type=behavior_type,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 60))
                )
                db.session.add(behavior)
                total_behaviors += 1

                # 用户可能对同一产品有多个行为
                if random.random() < 0.5:  # 50%的概率有额外行为
                    if behavior_type == '购买':  # 如果已购买，则不会再有其他行为
                        continue

                    # 选择一个不同于已有行为的行为
                    remaining_behaviors = [b for b in behavior_types if b != behavior_type]
                    if behavior_type == '加购':  # 如果已加购，可能会购买
                        remaining_behaviors = ['购买']
                    elif behavior_type == '收藏':  # 如果已收藏，可能会加购或购买
                        remaining_behaviors = ['加购', '购买']

                    second_behavior_type = random.choice(remaining_behaviors)
                    second_behavior = UserBehavior(
                        user_id=user.id,
                        product_id=product.id,
                        behavior_type=second_behavior_type,
                        created_at=datetime.now() - timedelta(days=random.randint(0, 30))  # 更近期的行为
                    )
                    db.session.add(second_behavior)
                    total_behaviors += 1

        db.session.commit()
        print(f"已创建 {total_behaviors} 条用户行为记录")

        # 添加销售数据
        print("创建销售数据...")
        total_sales = 0
        for product in products:
            # 90天销售数据
            for i in range(90):
                date = datetime.now().date() - timedelta(days=i)

                # 价格波动模式：
                # 1. 正常波动 (±10%)
                # 2. 大促时段价格下降幅度更大

                # 模拟大促时段（如618、双11等）
                is_promotion = False
                if i in [11, 12, 13, 14, 15] or i in [60, 61, 62, 63, 64]:  # 模拟双11和618
                    is_promotion = True

                if is_promotion:
                    price_var = product.price * random.uniform(0.7, 0.9)  # 大促期间降价更多
                    discount_price = price_var * random.uniform(0.8, 0.9)  # 在此基础上还有折扣
                    sales_volume = random.randint(50, 200)  # 大促期间销量更高
                else:
                    price_var = product.price * random.uniform(0.9, 1.1)  # 正常波动
                    discount_price = price_var * random.uniform(0.85, 0.95)  # 正常折扣
                    sales_volume = random.randint(5, 50)  # 正常销量

                sale = ProductSale(
                    product_id=product.id,
                    platform=product.platform,
                    price=round(price_var, 2),
                    discount_price=round(discount_price, 2),
                    sales_volume=sales_volume,
                    date=date
                )
                db.session.add(sale)
                total_sales += 1

        db.session.commit()
        print(f"已创建 {total_sales} 条销售数据记录")

        # 添加优惠信息
        print("创建优惠券数据...")
        total_discounts = 0
        for product in products:
            # 不同的优惠类型概率
            discount_types = {
                '满减': 0.4,  # 40%的概率
                '折扣': 0.3,  # 30%的概率
                '消费券': 0.3  # 30%的概率
            }

            # 75%的产品有优惠
            if random.random() < 0.75:
                # 根据概率选择优惠类型
                discount_type = random.choices(
                    population=list(discount_types.keys()),
                    weights=list(discount_types.values()),
                    k=1
                )[0]

                if discount_type == '满减':
                    # 满减值通常是价格的5%-15%
                    discount_value = round(product.price * random.uniform(0.05, 0.15), 0)
                    # 满减门槛通常是价格的85%-95%
                    min_purchase = round(product.price * random.uniform(0.85, 0.95), 0)
                elif discount_type == '折扣':
                    # 折扣范围一般是7折到9.5折
                    discount_value = round(random.uniform(7.0, 9.5), 1)
                    min_purchase = 0
                else:  # 消费券
                    # 消费券通常是价格的5%-20%
                    discount_value = round(product.price * random.uniform(0.05, 0.2), 0)
                    min_purchase = 0

                # 设置优惠的开始和结束日期
                start_date = datetime.now() - timedelta(days=random.randint(1, 30))
                end_date = start_date + timedelta(days=random.randint(7, 30))

                # 创建优惠记录
                discount = PlatformDiscount(
                    platform=product.platform,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    min_purchase=min_purchase,
                    start_date=start_date,
                    end_date=end_date,
                    stackable=random.random() < 0.3,  # 30%的概率可叠加
                    product_id=product.id
                )
                db.session.add(discount)
                total_discounts += 1

                # 20%的概率同时有第二种优惠
                if random.random() < 0.2:
                    # 选择一个不同的优惠类型
                    remaining_types = [t for t in discount_types.keys() if t != discount_type]
                    second_type = random.choice(remaining_types)

                    if second_type == '满减':
                        discount_value = round(product.price * random.uniform(0.05, 0.15), 0)
                        min_purchase = round(product.price * random.uniform(0.85, 0.95), 0)
                    elif second_type == '折扣':
                        discount_value = round(random.uniform(7.0, 9.5), 1)
                        min_purchase = 0
                    else:  # 消费券
                        discount_value = round(product.price * random.uniform(0.05, 0.2), 0)
                        min_purchase = 0

                    # 不同的时间段
                    start_date = datetime.now() + timedelta(days=random.randint(1, 15))
                    end_date = start_date + timedelta(days=random.randint(7, 30))

                    second_discount = PlatformDiscount(
                        platform=product.platform,
                        discount_type=second_type,
                        discount_value=discount_value,
                        min_purchase=min_purchase,
                        start_date=start_date,
                        end_date=end_date,
                        stackable=random.random() < 0.3,  # 30%的概率可叠加
                        product_id=product.id
                    )
                    db.session.add(second_discount)
                    total_discounts += 1

        db.session.commit()
        print(f"已创建 {total_discounts} 条优惠信息")

        # 添加用户评价
        print("创建用户评价数据...")
        total_reviews = 0
        # 常见评价内容模板
        positive_reviews = [
            "非常满意，产品质量很好，外观漂亮，性能强劲，值得推荐！",
            "物超所值，比我想象的要好，配置很高，运行很流畅，使用体验很好。",
            "{brand}的产品一如既往的优秀，这款{name}无论是做工还是性能都非常满意。",
            "收到货很惊喜，包装很完好，产品外观设计很漂亮，使用起来也很方便，很满意这次购买。",
            "用了一段时间了，很稳定，不卡顿，电池续航也不错，总体来说是一次不错的购买体验。",
            "价格合理，{brand}的产品一直很喜欢，这次购买的{name}不负所望，各方面都很好。",
            "客服态度很好，发货速度快，产品质量没话说，是正品，值得购买！"
        ]

        neutral_reviews = [
            "产品还行，没有惊喜但也没有失望，符合这个价位的期望。",
            "{name}整体表现一般，有优点也有不足，但价格还算合理。",
            "收到货已经使用一周，感觉一般，不算特别好但也说不上差。",
            "外观设计不错，但性能表现一般，对于这个价格来说勉强可以接受。",
            "产品功能基本符合描述，使用体验中规中矩，没有特别惊艳的地方。"
        ]

        negative_reviews = [
            "有点失望，{name}的实际效果不如宣传的那么好，性价比不高。",
            "产品质量一般，有轻微瑕疵，客服解决问题的态度也不够好。",
            "使用几天后发现有问题，运行不稳定，有点后悔购买了。",
            "收到的产品有划痕，虽然不影响使用，但还是感觉很不爽。",
            "价格偏高，性能一般，不值这个价，不推荐购买。"
        ]

        for user in users:
            # 每个用户评价5-15个产品
            review_count = random.randint(5, 15)
            review_products = random.sample(products, min(review_count, len(products)))

            for product in review_products:
                # 根据星级分布随机选择评分
                # 通常产品评分偏向正面，设置权重反映这一点
                rating = random.choices(
                    population=[1, 2, 3, 4, 5],
                    weights=[0.05, 0.05, 0.1, 0.3, 0.5],  # 5星占50%
                    k=1
                )[0]

                # 根据评分选择评价内容
                if rating >= 4:
                    template = random.choice(positive_reviews)
                elif rating >= 3:
                    template = random.choice(neutral_reviews)
                else:
                    template = random.choice(negative_reviews)

                # 填充模板中的变量
                content = template.replace("{brand}", product.brand).replace("{name}", product.name)

                # 创建评价记录
                review = UserReview(
                    user_id=user.id,
                    product_id=product.id,
                    rating=rating,
                    content=content,
                    sentiment=rating / 5.0,  # 简单地将评分转换为情感值
                    created_at=datetime.now() - timedelta(days=random.randint(0, 60))
                )
                db.session.add(review)
                total_reviews += 1

        db.session.commit()
        print(f"已创建 {total_reviews} 条用户评价")

        print("测试数据生成完成！系统现在应该有足够数据来训练推荐模型。")

if __name__ == '__main__':
    init_data(app)