#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from accounts.models import CustomUser

def create_admin():
    """创建管理员用户"""
    username = input("请输入管理员用户名: ")
    email = input("请输入邮箱: ")
    password = input("请输入密码: ")

    try:
        # 检查用户是否已存在
        if CustomUser.objects.filter(username=username).exists():
            print(f"用户 '{username}' 已存在！")
            return

        # 创建管理员用户
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin'  # 设置为管理员角色
        )

        print(f"管理员用户 '{username}' 创建成功！")
        print(f"用户ID: {user.id}")
        print(f"角色: {user.get_role_display()}")

    except Exception as e:
        print(f"创建管理员用户失败: {e}")

if __name__ == '__main__':
    print("=== 创建管理员用户 ===")
    create_admin()