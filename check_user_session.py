#!/usr/bin/env python
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
import django
django.setup()

from django.test import Client
from accounts.models import CustomUser
from django.urls import reverse

def test_user_session():
    """测试用户会话和导航功能"""
    print("=== 测试用户会话 ===\n")

    # 测试几个用户
    users = CustomUser.objects.all()[:3]

    for user in users:
        print(f"用户: {user.username} (邮箱: {user.email}, 角色: {user.role})")
        print(f"  - 是否为管理员: {user.is_admin}")
        print(f"  - 是否已认证: {user.is_authenticated}")

        # 模拟登录
        client = Client()
        client.force_login(user)

        # 测试几个关键页面的访问
        test_pages = [
            ('home', '系统首页'),
            ('books:book_list', '图书列表'),
            ('categories:category_list', '分类管理'),
            ('borrowing:my_records', '我的借阅'),
            ('reviews:my_reviews', '我的评论'),
        ]

        for url_name, description in test_pages:
            try:
                url = reverse(url_name)
                response = client.get(url)

                if response.status_code == 200:
                    status = "可访问"
                elif response.status_code == 302:
                    status = "重定向"
                else:
                    status = f"状态码: {response.status_code}"

                print(f"  - {description}: {status}")

            except Exception as e:
                print(f"  - {description}: 错误 - {e}")

        print()

if __name__ == '__main__':
    test_user_session()