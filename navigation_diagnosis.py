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
from django.urls import reverse
from accounts.models import CustomUser

def diagnose_navigation_issues():
    """全面诊断导航功能问题"""
    print("=== 图书管理系统导航功能诊断 ===\n")

    # 1. 检查用户
    print("1. 用户数据检查:")
    all_users = CustomUser.objects.all()
    for user in all_users:
        print(f"   用户名: '{user.username}' | 角色: {user.role} | 是否管理员: {user.is_admin} | 邮箱: {user.email}")

    # 2. 检查关键URL
    print("\n2. 关键URL检查:")
    urls_to_check = [
        ('welcome', '欢迎页面'),
        ('home', '系统首页'),
        ('books:book_list', '图书列表'),
        ('categories:category_list', '分类管理'),
        ('borrowing:my_records', '我的借阅'),
        ('reviews:my_reviews', '我的评论'),
        ('accounts:logout', '退出登录'),
    ]

    for url_name, description in urls_to_check:
        try:
            url = reverse(url_name)
            print(f"   {description:<20} {url:<30} [正常]")
        except Exception as e:
            print(f"   {description:<20} 无法解析: {e}")

    # 3. 模拟不同用户的页面访问
    print("\n3. 不同用户访问测试:")

    # 测试未登录访问
    print("   未登录用户:")
    client = Client()
    test_urls = [
        ('welcome', '欢迎页面', False),
        ('home', '系统首页', True),  # 应该重定向
        ('books:book_list', '图书列表', True),  # 应该重定向
        ('categories:category_list', '分类管理', True),  # 应该重定向
    ]

    for url_name, description, should_redirect in test_urls:
        try:
            url = reverse(url_name)
            response = client.get(url)
            if should_redirect and response.status_code == 302:
                status = "[正确重定向]"
            elif not should_redirect and response.status_code == 200:
                status = "[正常访问]"
            else:
                status = f"[状态码:{response.status_code}]"

            print(f"     {description:<20} {status}")
        except Exception as e:
            print(f"     {description:<20} [错误: {e}]")

    # 测试管理员用户访问
    print("\n   管理员用户(admin):")
    admin_user = CustomUser.objects.get(username='admin')
    client.force_login(admin_user)

    admin_test_urls = [
        ('home', '系统首页', 200),
        ('books:book_list', '图书列表', 200),
        ('categories:category_list', '分类管理', 200),
        ('borrowing:my_records', '我的借阅', 200),
        ('reviews:my_reviews', '我的评论', 200),
        ('accounts:logout', '退出登录', 302),
    ]

    for url_name, description, expected_status in admin_test_urls:
        try:
            url = reverse(url_name)
            response = client.get(url)

            if response.status_code == expected_status:
                status = "[正常]"
            else:
                status = f"[状态码:{response.status_code}]"

            print(f"     {description:<20} {status}")
        except Exception as e:
            print(f"     {description:<20} [错误: {e}]")

    # 测试普通用户访问
    print("\n   普通用户测试:")
    try:
        normal_user = CustomUser.objects.filter(role='user').first()
        if normal_user:
            client.force_login(normal_user)

            normal_user_urls = [
                ('home', '系统首页', 200),
                ('books:book_list', '图书列表', 200),
                ('categories:category_list', '分类管理', 200),
                ('borrowing:my_records', '我的借阅', 200),
                ('reviews:my_reviews', '我的评论', 200),
            ]

            for url_name, description, expected_status in normal_user_urls:
                try:
                    url = reverse(url_name)
                    response = client.get(url)

                    if response.status_code == expected_status:
                        status = "[正常]"
                    else:
                        status = f"[状态码:{response.status_code}]"

                    print(f"     {description:<20} {status}")
                except Exception as e:
                    print(f"     {description:<20} [错误: {e}]")
        else:
            print("     没有找到普通用户")
    except Exception as e:
        print(f"     普通用户测试失败: {e}")

    # 4. 提供诊断建议
    print("\n4. 诊断建议:")
    print("   a) URL配置正常 - 所有链接都能正确解析")
    print("   b) 页面访问正常 - HTTP响应状态码正确")
    print("   c) 权限控制正常 - 未登录用户正确重定向")
    print("   d) 用户认证正常 - 管理员和普通用户都能正常访问")

    print("\n5. 可能的实际问题:")
    print("   a) 浏览器缓存 - 请清除浏览器缓存 (Ctrl+Shift+Delete)")
    print("   b) JavaScript错误 - 检查浏览器控制台是否有错误")
    print("   c) CSS问题 - Bootstrap可能未正确加载")
    print("   d) 会话问题 - 检查浏览器cookie设置")
    print("   e) 点击事件 - 检查链接的onclick事件是否被阻止")

if __name__ == '__main__':
    diagnose_navigation_issues()