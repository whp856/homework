#!/usr/bin/env python
import os
import sys
from django.urls import reverse
from django.conf import settings

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
import django
django.setup()

def test_navigation_urls():
    """测试导航栏中所有URL的解析"""
    print("=== 测试导航栏URL解析 ===\n")

    # 测试的URL列表
    test_urls = [
        ('welcome', '欢迎页面'),
        ('home', '系统首页'),
        ('books:book_list', '图书列表'),
        ('categories:category_list', '分类管理'),
        ('borrowing:my_records', '我的借阅'),
        ('reviews:my_reviews', '我的评论'),
        ('accounts:login', '登录'),
        ('accounts:logout', '退出登录'),
        ('accounts:register', '注册'),
        ('accounts:profile', '个人资料'),
        ('borrowing:record_list', '所有借阅记录'),
        ('reviews:review_list', '评论管理'),
    ]

    print(f"{'URL名称':<25} {'反向解析结果':<40} {'状态'}")
    print("=" * 70)

    for url_name, description in test_urls:
        try:
            resolved_url = reverse(url_name)
            status = "[正常]"
        except Exception as e:
            resolved_url = f"错误: {e}"
            status = "[失败]"

        print(f"{url_name:<25} {resolved_url:<40} {status}")

    print("\n=== 测试带参数的URL ===")

    # 测试需要参数的URL
    param_urls = [
        ('books:book_detail', {'book_id': 1}, '图书详情'),
        ('books:book_update', {'book_id': 1}, '编辑图书'),
        ('books:book_delete', {'book_id': 1}, '删除图书'),
        ('categories:category_detail', {'category_id': 1}, '分类详情'),
        ('reviews:book_reviews', {'book_id': 1}, '图书评论'),
    ]

    for url_name, kwargs, description in param_urls:
        try:
            resolved_url = reverse(url_name, kwargs=kwargs)
            status = "[正常]"
        except Exception as e:
            resolved_url = f"错误: {e}"
            status = "[失败]"

        print(f"{url_name:<25} {resolved_url:<40} {status} ({description})")

if __name__ == '__main__':
    test_navigation_urls()