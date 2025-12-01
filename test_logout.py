#!/usr/bin/env python
import os
import sys
import django
from django.test import Client

# 配置Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import reverse
from accounts.models import CustomUser

def test_logout_functionality():
    """测试登出功能"""
    print("=== 测试登出功能 ===\n")

    # 创建客户端
    client = Client()

    # 测试GET请求登出（原始问题）
    print("1. 测试GET请求登出:")
    try:
        logout_url = reverse('accounts:logout')
        print(f"   登出URL: {logout_url}")

        # 先模拟登录
        admin_user = CustomUser.objects.get(username='admin')
        client.force_login(admin_user)

        # 测试GET请求登出
        response = client.get(logout_url)
        print(f"   GET请求状态码: {response.status_code}")

        if response.status_code == 302:
            print("   [成功] GET请求登出正常重定向")
        elif response.status_code == 405:
            print("   [失败] GET请求仍然返回405错误")
        else:
            print(f"   [异常] 意外的状态码: {response.status_code}")

        # 测试POST请求登出
        response = client.post(logout_url)
        print(f"   POST请求状态码: {response.status_code}")

        if response.status_code == 302:
            print("   [成功] POST请求登出正常重定向")
        else:
            print(f"   [异常] 意外的状态码: {response.status_code}")

    except Exception as e:
        print(f"   [错误] 测试失败: {e}")

if __name__ == '__main__':
    test_logout_functionality()