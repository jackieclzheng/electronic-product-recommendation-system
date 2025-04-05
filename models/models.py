# 数据库模型定义
# filename: models/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    register_time = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    behaviors = db.relationship('UserBehavior', backref='user', lazy='dynamic')
    reviews = db.relationship('UserReview', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'


class ProductCategory(db.Model):
    """产品种类模型"""
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'


class Product(db.Model):
    """产品信息模型"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    name = db.Column(db.String(128), nullable=False)
    brand = db.Column(db.String(64))
    model = db.Column(db.String(64))
    price = db.Column(db.Float)
    platform = db.Column(db.String(32))
    spec_json = db.Column(db.Text)
    image_url = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    sales = db.relationship('ProductSale', backref='product', lazy='dynamic')
    behaviors = db.relationship('UserBehavior', backref='product', lazy='dynamic')
    reviews = db.relationship('UserReview', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    @property
    def specifications(self):
        """将JSON规格转换为字典"""
        if self.spec_json:
            try:
                return json.loads(self.spec_json)
            except:
                return {}
        return {}


class PlatformDiscount(db.Model):
    """平台优惠模型"""
    __tablename__ = 'platform_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False)
    discount_type = db.Column(db.String(32), nullable=False)
    discount_value = db.Column(db.Float)
    min_purchase = db.Column(db.Float)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    stackable = db.Column(db.Boolean, default=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    
    def __repr__(self):
        return f'<PlatformDiscount {self.platform} {self.discount_type}>'


class UserBehavior(db.Model):
    """用户行为模型"""
    __tablename__ = 'user_behaviors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    behavior_type = db.Column(db.String(32), nullable=False)  # 浏览/收藏/加购/购买
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<UserBehavior {self.behavior_type}>'


class UserReview(db.Model):
    """用户评价模型"""
    __tablename__ = 'user_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    rating = db.Column(db.Integer)  # 1-5星
    content = db.Column(db.Text)
    sentiment = db.Column(db.Float)  # 情感分析结果
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<UserReview {self.rating}>'


class ProductSale(db.Model):
    """产品销售模型"""
    __tablename__ = 'product_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    platform = db.Column(db.String(32))
    price = db.Column(db.Float)
    discount_price = db.Column(db.Float)
    sales_volume = db.Column(db.Integer)
    date = db.Column(db.Date)
    
    def __repr__(self):
        return f'<ProductSale {self.platform} {self.price}>'


class ShopInfo(db.Model):
    """店铺信息模型"""
    __tablename__ = 'shop_info'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False)
    shop_name = db.Column(db.String(128), nullable=False)
    shop_id = db.Column(db.String(64))
    rating = db.Column(db.Float)  # 店铺评分
    sales_volume = db.Column(db.Integer)  # 销售量
    discount_count = db.Column(db.Integer)  # 优惠券数量
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<ShopInfo {self.platform} {self.shop_name}>'


# 创建数据库表
def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # 初始化产品类别
        if not ProductCategory.query.filter_by(name='手机').first():
            categories = [
                ProductCategory(name='手机', description='智能手机类别'),
                ProductCategory(name='平板', description='平板电脑类别'),
                ProductCategory(name='电脑', description='笔记本和台式电脑类别')
            ]
            db.session.add_all(categories)
            db.session.commit()
