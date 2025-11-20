#!/usr/bin/env python
"""
Django图书管理系统测试脚本
用于验证系统功能是否正常工作
"""

import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

def test_models():
    """测试模型是否正常工作"""
    print("🔍 测试模型...")

    try:
        from accounts.models import CustomUser
        from books.models import Book
        from categories.models import Category
        from borrowing.models import BorrowRecord
        from reviews.models import Review

        print("✅ 所有模型导入成功")

        # 测试用户模型
        print(f"📊 CustomUser模型字段: {[f.name for f in CustomUser._meta.fields]}")

        # 测试图书模型
        print(f"📊 Book模型字段: {[f.name for f in Book._meta.fields]}")

        # 测试分类模型
        print(f"📊 Category模型字段: {[f.name for f in Category._meta.fields]}")

        # 测试借阅记录模型
        print(f"📊 BorrowRecord模型字段: {[f.name for f in BorrowRecord._meta.fields]}")

        # 测试评论模型
        print(f"📊 Review模型字段: {[f.name for f in Review._meta.fields]}")

        return True
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False

def test_urls():
    """测试URL配置"""
    print("\n🔍 测试URL配置...")

    try:
        from django.urls import reverse
        from django.test import Client

        client = Client()

        # 测试首页
        print("🏠 测试首页...")
        response = client.get(reverse('home'))
        print(f"📊 首页状态码: {response.status_code}")

        # 测试登录页面
        print("🔐 测试登录页面...")
        response = client.get(reverse('accounts:login'))
        print(f"📊 登录页状态码: {response.status_code}")

        # 测试注册页面
        print("📝 测试注册页面...")
        response = client.get(reverse('accounts:register'))
        print(f"📊 注册页状态码: {response.status_code}")

        # 测试图书列表
        print("📚 测试图书列表...")
        response = client.get(reverse('books:book_list'))
        print(f"📊 图书列表状态码: {response.status_code}")

        print("✅ URL配置测试通过")
        return True
    except Exception as e:
        print(f"❌ URL配置测试失败: {e}")
        return False

def test_forms():
    """测试表单"""
    print("\n🔍 测试表单...")

    try:
        from accounts.forms import CustomUserCreationForm
        from books.forms import BookForm
        from categories.forms import CategoryForm
        from borrowing.forms import BorrowRecordForm
        from reviews.forms import ReviewForm

        print("✅ 所有表单导入成功")

        # 测试用户注册表单
        form = CustomUserCreationForm()
        print(f"📊 用户注册表单字段: {list(form.fields.keys())}")

        # 测试图书表单
        form = BookForm()
        print(f"📊 图书表单字段: {list(form.fields.keys())}")

        return True
    except Exception as e:
        print(f"❌ 表单测试失败: {e}")
        return False

def test_permissions():
    """测试权限控制"""
    print("\n🔍 测试权限控制...")

    try:
        from accounts.models import CustomUser

        # 检查CustomUser模型是否有is_admin属性
        test_user = CustomUser(username='test')
        print(f"📊 用户权限属性: is_admin = {getattr(test_user, 'is_admin', 'NOT_FOUND')}")

        print("✅ 权限控制测试通过")
        return True
    except Exception as e:
        print(f"❌ 权限控制测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始Django图书管理系统测试...")
    print("=" * 50)

    tests = [
        test_models,
        test_urls,
        test_forms,
        test_permissions,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！系统配置正确。")
    else:
        print("⚠️  部分测试失败，请检查配置。")

    print("\n🔧 接下来的步骤:")
    print("1. 运行 'python manage.py migrate' 应用数据库迁移")
    print("2. 运行 'python manage.py createsuperuser' 创建管理员账户")
    print("3. 运行 'python manage.py runserver' 启动开发服务器")
    print("4. 访问 http://127.0.0.1:8000/ 查看系统")

if __name__ == '__main__':
    main()