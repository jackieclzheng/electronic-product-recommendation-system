# 电子产品推荐系统

这是一个基于Flask的电子产品推荐系统，提供产品展示、用户认证、产品推荐和管理员后台功能。

## 功能特点

- **用户认证系统**：用户注册、登录、"记住我"功能
- **产品展示**：分类浏览、详情查看、筛选搜索
- **个性化推荐**：基于用户行为的产品推荐
- **管理员后台**：
  - 仪表盘：系统概览和统计数据
  - 产品管理：产品的增删改查、图片上传
  - 用户管理：用户的增删改查
  - 分类管理：产品分类的增删改查
  - 数据分析：销售和用户行为分析

## 技术栈

- **后端**：Flask, SQLAlchemy, Werkzeug
- **前端**：Bootstrap 4, jQuery, Font Awesome
- **数据库**：SQLite
- **数据分析**：Pandas, NumPy, Scikit-learn

## 安装与运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python run.py
```

3. 在浏览器中访问：
```
http://localhost:5000
```

## 初始设置

- 首次运行时，系统会自动创建数据库和基本产品分类
- 请注册一个用户名为"admin"的账户，系统会自动赋予管理员权限
- 管理员后台入口：`/admin`

## 目录结构

- **static/**：静态资源文件（CSS、JavaScript、图片等）
- **templates/**：HTML模板文件
- **models/**：数据库模型定义
- **analysis/**：数据分析模块
- **recommendation/**：推荐系统模块
- **crawler/**：数据爬虫模块

## 用户指南

### 普通用户

1. 注册/登录：点击导航栏的"注册"或"登录"按钮
2. 浏览产品：可通过首页、分类页或搜索功能浏览产品
3. 产品详情：点击产品卡片查看详细信息、规格和评价
4. 个人中心：登录后可访问个人中心，查看收藏和浏览历史

### 管理员

1. 登录：使用管理员账户登录
2. 访问后台：登录后访问`/admin`进入管理后台
3. 产品管理：
   - 添加产品：点击"添加新产品"按钮
   - 编辑产品：点击产品列表中的编辑图标
   - 删除产品：点击产品列表中的删除图标
4. 用户管理：可添加、编辑、删除用户
5. 分类管理：可添加、编辑、删除产品分类

## 新增功能说明

本版本在原有系统基础上增加了以下功能：

1. **用户认证系统**：
   - 完整的注册和登录功能
   - "记住我"功能，延长登录会话
   - 密码加密存储和验证

2. **管理员后台**：
   - 仪表盘：系统概览和统计数据
   - 产品管理：完整的CRUD操作
   - 用户管理：完整的CRUD操作
   - 分类管理：完整的CRUD操作

## 注意事项

- 默认使用SQLite数据库，无需额外配置
- 上传的产品图片存储在`static/uploads`目录
- 管理员账户（用户名为"admin"）拥有特殊权限
