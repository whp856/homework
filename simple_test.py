#!/usr/bin/env python
"""
Django图书管理系统简单测试脚本
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')

def test_imports():
    """测试模块导入"""
    print("Testing Django imports...")

    try:
        import django
        from django.conf import settings

        # 配置Django
        django.setup()

        # 测试模型导入
        from accounts.models import CustomUser
        from books.models import Book
        from categories.models import Category
        from borrowing.models import BorrowRecord
        from reviews.models import Review

        print("✓ All models imported successfully")

        # 测试表单导入
        from accounts.forms import CustomUserCreationForm
        from books.forms import BookForm
        from categories.forms import CategoryForm

        print("✓ All forms imported successfully")

        # 测试视图导入
        from accounts import views as account_views
        from books import views as book_views

        print("✓ All views imported successfully")

        return True

    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_settings():
    """测试Django设置"""
    print("\nTesting Django settings...")

    try:
        import django
        from django.conf import settings

        # 检查关键设置
        print(f"DEBUG = {settings.DEBUG}")
        print(f"DATABASE ENGINE = {settings.DATABASES['default']['ENGINE']}")
        print(f"AUTH_USER_MODEL = {settings.AUTH_USER_MODEL}")
        print(f"INSTALLED_APPS = {len(settings.INSTALLED_APPS)} apps")

        print("✓ Settings check passed")
        return True

    except Exception as e:
        print(f"✗ Settings test failed: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Django Library Management System Test")
    print("=" * 50)

    tests = [test_settings, test_imports]
    passed = 0

    for test in tests:
        if test():
            passed += 1

    print(f"\nResult: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("\nAll tests passed! System is ready.")
        print("Next steps:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python manage.py createsuperuser")
        print("4. python manage.py runserver")
    else:
        print("\nSome tests failed. Please check the configuration.")

if __name__ == '__main__':
    main()