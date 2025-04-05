from PIL import Image
import os

# 确保目录存在
os.makedirs('static/images', exist_ok=True)

# 创建banner图片 - 纯色版本
colors = [(52, 152, 219), (46, 204, 113), (155, 89, 182)]  # 蓝色、绿色、紫色
for i, color in enumerate(colors, 1):
    img = Image.new('RGB', (1200, 400), color=color)
    img.save(f'static/images/banner{i}.jpg')

# 创建分类图片
category_colors = {
    '手机': (231, 76, 60),    # 红色
    '平板': (241, 196, 15),   # 黄色
    '电脑': (26, 188, 156)    # 青色
}

for category, color in category_colors.items():
    img = Image.new('RGB', (600, 400), color=color)
    img.save(f'static/images/category_{category}.jpg')

print("纯色图片创建完成！")