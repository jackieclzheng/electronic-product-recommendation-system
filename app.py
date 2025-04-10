# API路由
# filename: app.py

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
import json
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import or_

# 导入自定义模块
# from models.models import db, init_db, User, Product, ProductCategory, UserBehavior, UserReview
# from .models.models import db, init_db, User, Product, ProductCategory, UserBehavior, UserReview
from models.models import db, init_db, User, Product, ProductCategory, UserBehavior, UserReview
from analysis.data_analysis import DataAnalysis
from recommendation.recommender import ProductRecommender
from config import Config

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化应用配置
Config.init_app(app)

# 确保静态文件目录存在
os.makedirs(os.path.join(app.static_folder, 'images/emotion_charts'), exist_ok=True)

# 配置
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///product_recommendation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB最大上传限制

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
init_db(app)

# 初始化推荐系统
recommender = ProductRecommender()

# 初始化数据分析
data_analysis = DataAnalysis(static_folder='static')

# 登录所需的装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 管理员权限所需的装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.username != 'admin':
            flash('需要管理员权限', 'danger')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# 路由定义
@app.route('/')
def index():
    """首页"""
    # 获取产品类别
    categories = ProductCategory.query.all()
    
    # 获取热门产品
    popular_products = recommender.get_popular_products(8)
    
    # 获取优惠产品
    discount_products = recommender.get_discount_recommendations(4)
    
    # 获取个性化推荐（如果用户已登录）
    personalized_products = []
    if 'user_id' in session:
        personalized_products = recommender.get_user_recommendations(session['user_id'], 4)
    
    return render_template('index.html', 
                          categories=categories,
                          popular_products=popular_products,
                          discount_products=discount_products,
                          personalized_products=personalized_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))
            
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('该邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        # 验证密码
        if len(password) < 6:
            flash('密码长度至少为6位', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        # 创建新用户
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            register_time=datetime.now(),
            last_login=datetime.now()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username

            # 判断是否为管理员，如果是则重定向到管理后台
            if user.username == 'admin':
                return redirect(url_for('admin_dashboard'))

            # 普通用户重定向到首页
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户登出"""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/products')
def products():
    """产品列表页面"""
    # 获取筛选参数
    category_id = request.args.get('category', type=int)
    platform = request.args.get('platform')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'price')
    
    # 构建查询
    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if platform:
        query = query.filter_by(platform=platform)
    
    if min_price:
        query = query.filter(Product.price >= min_price)
    
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    # 排序
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.price.asc())
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    # 获取类别和平台列表（用于筛选）
    categories = ProductCategory.query.all()
    platforms = db.session.query(Product.platform).distinct().all()
    platforms = [p[0] for p in platforms]
    
    return render_template('products.html',
                          products=products,
                          pagination=pagination,
                          categories=categories,
                          platforms=platforms,
                          selected_category=category_id,
                          selected_platform=platform,
                          min_price=min_price,
                          max_price=max_price,
                          sort_by=sort_by)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        # 获取产品信息
        product = Product.query.get_or_404(product_id)
        
        # 获取所有分类，用于导航栏
        categories = ProductCategory.query.all()
        
        # 获取产品规格
        specs = {}
        if product.spec_json:
            try:
                specs = json.loads(product.spec_json)
            except:
                pass
        
        # 获取产品评价
        reviews = UserReview.query.filter_by(product_id=product_id).order_by(UserReview.created_at.desc()).limit(10).all()
        
        # 获取相似产品推荐
        similar_products = recommender.get_similar_products(product_id, 4)
        
        # 获取价格趋势
        price_trend = data_analysis.get_price_trend(product_id)
        
        # 获取平台价格对比
        platform_compare = data_analysis.compare_platform_prices(product.name)
        
        # 获取评价分析
        review_analysis = data_analysis.analyze_user_reviews(product_id)
        
        # 获取最优购买方案
        optimal_plans = data_analysis.get_optimal_purchase_plan(product_id)
        
        # 记录用户浏览行为（如果已登录）
        if 'user_id' in session:
            user_behavior = UserBehavior(
                user_id=session['user_id'],
                product_id=product_id,
                behavior_type='浏览',
                created_at=datetime.now()
            )
            db.session.add(user_behavior)
            db.session.commit()
        
        return render_template('product_detail.html',
                             product=product,
                             categories=categories,  # 添加分类数据
                             reviews=reviews,
                             specs=specs,
                             price_trend=price_trend,
                             platform_compare=platform_compare,
                             optimal_plans=optimal_plans,
                             review_analysis=review_analysis,
                             similar_products=similar_products)
    except Exception as e:
        print(f"获取产品详情时出错: {str(e)}")
        return render_template('error.html', error="获取产品详情失败")

@app.route('/category/<int:category_id>')
def category_products(category_id):
    try:
        # 获取当前分类
        current_category = ProductCategory.query.get_or_404(category_id)
        
        # 获取所有分类用于导航
        categories = ProductCategory.query.all()
        
        # 获取该分类下的产品
        products = Product.query.filter_by(category_id=category_id).all()
        
        return render_template('category.html',
                             current_category=current_category,
                             categories=categories,  # 添加分类数据
                             products=products)
    except Exception as e:
        print(f"获取分类产品时出错: {str(e)}")
        return render_template('error.html', error="获取分类产品失败")

@app.route('/user/profile')
@login_required
def user_profile():
    """用户个人中心"""
    user = User.query.get(session['user_id'])
    
    # 获取用户行为数据
    behaviors = UserBehavior.query.filter_by(user_id=user.id).order_by(UserBehavior.created_at.desc()).limit(20).all()
    
    # 获取用户评价
    reviews = UserReview.query.filter_by(user_id=user.id).order_by(UserReview.created_at.desc()).all()
    
    return render_template('user_profile.html',
                          user=user,
                          behaviors=behaviors,
                          reviews=reviews)

@app.route('/user/favorites')
@login_required
def user_favorites():
    """用户收藏"""
    user_id = session['user_id']
    
    # 获取用户收藏的产品
    favorites = UserBehavior.query.filter_by(
        user_id=user_id,
        behavior_type='收藏'
    ).order_by(UserBehavior.created_at.desc()).all()
    
    # 获取产品详情
    favorite_products = []
    for favorite in favorites:
        product = Product.query.get(favorite.product_id)
        if product:
            favorite_products.append({
                'product': product,
                'favorite_time': favorite.created_at
            })
    
    return render_template('user_favorites.html',
                          favorite_products=favorite_products)

@app.route('/api/favorite/<int:product_id>', methods=['POST'])
@login_required
def toggle_favorite(product_id):
    """切换收藏状态"""
    # 检查产品是否存在
    product = Product.query.get_or_404(product_id)
    
    # 检查是否已收藏
    existing_favorite = UserBehavior.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id,
        behavior_type='收藏'
    ).first()
    
    if existing_favorite:
        # 取消收藏
        db.session.delete(existing_favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'remove'})
    else:
        # 添加收藏
        new_favorite = UserBehavior(
            user_id=session['user_id'],
            product_id=product_id,
            behavior_type='收藏',
            created_at=datetime.now()
        )
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'add'})

@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

# 管理员后台路由
@app.route('/admin')
@admin_required
def admin_dashboard():
    """管理员仪表盘"""
    # 统计数据admin_dash
    product_count = Product.query.count()
    user_count = User.query.count()
    review_count = UserReview.query.count()
    category_count = ProductCategory.query.count()
    
    # 最近注册用户
    recent_users = User.query.order_by(User.register_time.desc()).limit(5).all()
    
    # 最近添加的产品
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          product_count=product_count,
                          user_count=user_count,
                          review_count=review_count,
                          category_count=category_count,
                          recent_users=recent_users,
                          recent_products=recent_products)

@app.route('/admin/products')
@admin_required
def admin_products():
    """管理员产品管理"""
    # 获取筛选参数
    category_id = request.args.get('category', type=int)
    keyword = request.args.get('keyword')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # 构建查询
    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if keyword:
        query = query.filter(Product.name.like(f'%{keyword}%'))
    
    if min_price:
        query = query.filter(Product.price >= min_price)
    
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    # 获取所有分类
    categories = ProductCategory.query.all()
    
    return render_template('admin/products.html', 
                          products=products, 
                          categories=categories,
                          pagination=pagination)

@app.route('/admin/product/<int:product_id>/json')
@admin_required
def admin_get_product_json(product_id):
    """获取产品JSON数据（用于编辑）"""
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'category_id': product.category_id,
        'brand': product.brand,
        'model': product.model,
        'price': product.price,
        'platform': product.platform,
        'spec_json': product.spec_json,
        'image_url': product.image_url
    })

@app.route('/admin/add_product', methods=['POST'])
@admin_required
def admin_add_product():
    """添加新产品"""
    try:
        name = request.form.get('name')
        category_id = request.form.get('category_id', type=int)
        brand = request.form.get('brand')
        model = request.form.get('model')
        price = request.form.get('price', type=float)
        platform = request.form.get('platform')
        spec_json = request.form.get('spec_json')
        
        # 验证必填字段
        if not name or not category_id or not price:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin_products'))
        
        # 验证JSON格式
        if spec_json:
            try:
                json.loads(spec_json)
            except json.JSONDecodeError:
                flash('产品规格JSON格式不正确', 'danger')
                return redirect(url_for('admin_products'))
        
        # 处理图片上传
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # 生成唯一文件名
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                image_url = f"/static/uploads/{unique_filename}"
        
        # 创建新产品
        new_product = Product(
            name=name,
            category_id=category_id,
            brand=brand,
            model=model,
            price=price,
            platform=platform,
            spec_json=spec_json,
            image_url=image_url,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        flash('产品添加成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'产品添加失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/edit_product', methods=['POST'])
@admin_required
def admin_edit_product():
    """编辑产品"""
    try:
        product_id = request.form.get('product_id', type=int)
        name = request.form.get('name')
        category_id = request.form.get('category_id', type=int)
        brand = request.form.get('brand')
        model = request.form.get('model')
        price = request.form.get('price', type=float)
        platform = request.form.get('platform')
        spec_json = request.form.get('spec_json')
        
        # 验证必填字段
        if not product_id or not name or not category_id or not price:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin_products'))
        
        # 验证JSON格式
        if spec_json:
            try:
                json.loads(spec_json)
            except json.JSONDecodeError:
                flash('产品规格JSON格式不正确', 'danger')
                return redirect(url_for('admin_products'))
        
        # 获取产品
        product = Product.query.get_or_404(product_id)
        
        # 更新产品信息
        product.name = name
        product.category_id = category_id
        product.brand = brand
        product.model = model
        product.price = price
        product.platform = platform
        product.spec_json = spec_json
        product.updated_at = datetime.now()
        
        # 处理图片上传
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # 生成唯一文件名
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                product.image_url = f"/static/uploads/{unique_filename}"
        
        db.session.commit()
        
        flash('产品更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'产品更新失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/delete_product', methods=['POST'])
@admin_required
def admin_delete_product():
    """删除产品"""
    try:
        product_id = request.form.get('product_id', type=int)
        
        if not product_id:
            flash('产品ID不能为空', 'danger')
            return redirect(url_for('admin_products'))
        
        # 获取产品
        product = Product.query.get_or_404(product_id)
        
        # 删除相关记录
        UserBehavior.query.filter_by(product_id=product_id).delete()
        UserReview.query.filter_by(product_id=product_id).delete()
        
        # 删除产品
        db.session.delete(product)
        db.session.commit()
        
        flash('产品删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'产品删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/users')
@admin_required
def admin_users():
    """管理员用户管理"""
    # 获取筛选参数
    username = request.args.get('username')
    email = request.args.get('email')
    
    # 构建查询
    query = User.query
    
    if username:
        query = query.filter(User.username.like(f'%{username}%'))
    
    if email:
        query = query.filter(User.email.like(f'%{email}%'))
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(User.id).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return render_template('admin/users.html', users=users, pagination=pagination)

@app.route('/admin/user/<int:user_id>/json')
@admin_required
def admin_get_user_json(user_id):
    """获取用户JSON数据（用于编辑）"""
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    })

@app.route('/admin/add_user', methods=['POST'])
@admin_required
def admin_add_user():
    """添加新用户"""
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证必填字段
        if not username or not email or not password:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin_users'))
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('admin_users'))
        
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('该邮箱已被注册', 'danger')
            return redirect(url_for('admin_users'))
        
        # 验证密码
        if len(password) < 6:
            flash('密码长度至少为6位', 'danger')
            return redirect(url_for('admin_users'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('admin_users'))
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            register_time=datetime.now(),
            last_login=datetime.now()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('用户添加成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'用户添加失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/edit_user', methods=['POST'])
@admin_required
def admin_edit_user():
    """编辑用户"""
    try:
        user_id = request.form.get('user_id', type=int)
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 验证必填字段
        if not user_id or not username or not email:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin_users'))
        
        # 获取用户
        user = User.query.get_or_404(user_id)
        
        # 检查用户名是否已存在（排除当前用户）
        existing_user = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('admin_users'))
        
        # 检查邮箱是否已存在（排除当前用户）
        existing_email = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_email:
            flash('该邮箱已被注册', 'danger')
            return redirect(url_for('admin_users'))
        
        # 更新用户信息
        user.username = username
        user.email = email
        
        # 如果提供了新密码，则更新密码
        if password:
            if len(password) < 6:
                flash('密码长度至少为6位', 'danger')
                return redirect(url_for('admin_users'))
            
            user.password_hash = generate_password_hash(password)
        
        db.session.commit()
        
        flash('用户更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'用户更新失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def admin_delete_user():
    """删除用户"""
    try:
        user_id = request.form.get('user_id', type=int)
        
        if not user_id:
            flash('用户ID不能为空', 'danger')
            return redirect(url_for('admin_users'))
        
        # 不允许删除管理员账户
        user = User.query.get_or_404(user_id)
        if user.username == 'admin':
            flash('不能删除管理员账户', 'danger')
            return redirect(url_for('admin_users'))
        
        # 删除相关记录
        UserBehavior.query.filter_by(user_id=user_id).delete()
        UserReview.query.filter_by(user_id=user_id).delete()
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        flash('用户删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'用户删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """管理员类别管理"""
    categories = ProductCategory.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/category/<int:category_id>/json')
@admin_required
def admin_get_category_json(category_id):
    """获取分类JSON数据（用于编辑）"""
    category = ProductCategory.query.get_or_404(category_id)
    
    return jsonify({
        'id': category.id,
        'name': category.name,
        'description': category.description
    })

@app.route('/admin/add_category', methods=['POST'])
@admin_required
def admin_add_category():
    """添加新分类"""
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        
        # 验证必填字段
        if not name:
            flash('分类名称不能为空', 'danger')
            return redirect(url_for('admin_categories'))
        
        # 检查分类名称是否已存在
        existing_category = ProductCategory.query.filter_by(name=name).first()
        if existing_category:
            flash('分类名称已存在', 'danger')
            return redirect(url_for('admin_categories'))
        
        # 创建新分类
        new_category = ProductCategory(
            name=name,
            description=description,
            created_at=datetime.now()
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash('分类添加成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'分类添加失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/edit_category', methods=['POST'])
@admin_required
def admin_edit_category():
    """编辑分类"""
    try:
        category_id = request.form.get('category_id', type=int)
        name = request.form.get('name')
        description = request.form.get('description')
        
        # 验证必填字段
        if not category_id or not name:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin_categories'))
        
        # 获取分类
        category = ProductCategory.query.get_or_404(category_id)
        
        # 检查分类名称是否已存在（排除当前分类）
        existing_category = ProductCategory.query.filter(
            ProductCategory.name == name, 
            ProductCategory.id != category_id
        ).first()
        if existing_category:
            flash('分类名称已存在', 'danger')
            return redirect(url_for('admin_categories'))
        
        # 更新分类信息
        category.name = name
        category.description = description
        
        db.session.commit()
        
        flash('分类更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'分类更新失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/delete_category', methods=['POST'])
@admin_required
def admin_delete_category():
    """删除分类"""
    try:
        category_id = request.form.get('category_id', type=int)
        
        if not category_id:
            flash('分类ID不能为空', 'danger')
            return redirect(url_for('admin_categories'))
        
        # 获取分类
        category = ProductCategory.query.get_or_404(category_id)
        
        # 删除分类
        db.session.delete(category)
        db.session.commit()
        
        flash('分类删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'分类删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/analysis')
@admin_required
def admin_analysis():
    """管理员数据分析"""
    # 优惠券效果分析
    discount_effect = data_analysis.analyze_discount_effect()
    
    # 叠加优惠分析
    stackable_effect = data_analysis.analyze_stackable_discounts()
    
    # 平台销量分析
    platform_sales = data_analysis.analyze_platform_sales()
    
    # 用户行为分析
    user_behavior = data_analysis.analyze_user_behavior()
    
    # 产品类别分析
    category_analysis = data_analysis.analyze_product_categories()
    
    return render_template('admin/analysis.html',
                          discount_effect=discount_effect,
                          stackable_effect=stackable_effect,
                          platform_sales=platform_sales,
                          user_behavior=user_behavior,
                          category_analysis=category_analysis)


@app.route('/submit_review', methods=['POST'])
@login_required
def submit_review():
    """提交产品评价"""
    product_id = request.form.get('product_id', type=int)
    rating = request.form.get('rating', type=int)
    content = request.form.get('content')

    # 验证数据
    if not product_id or not rating or not content:
        flash('请填写所有必要信息', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

    if rating < 1 or rating > 5:
        flash('评分必须在1-5之间', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

    # 检查产品是否存在
    product = Product.query.get_or_404(product_id)

    # 创建评价
    review = UserReview(
        user_id=session['user_id'],
        product_id=product_id,
        rating=rating,
        content=content,
        sentiment=rating / 5.0,  # 简单地使用评分作为情感值
        created_at=datetime.now()
    )

    db.session.add(review)
    db.session.commit()

    flash('评价提交成功，感谢您的反馈！', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        # 只搜索名称
        products = Product.query.filter(
            Product.name.ilike(f'%{query}%')
        ).all()
    else:
        products = []
        
    return render_template('search_results.html',
                         query=query,
                         products=products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)