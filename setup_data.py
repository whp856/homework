#!/usr/bin/env python
"""
Django图书管理系统初始数据创建脚本
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')

import django
django.setup()

def create_admin_user():
    """创建管理员用户"""
    print("Creating admin user...")

    try:
        from accounts.models import CustomUser

        # 检查是否已存在管理员
        if CustomUser.objects.filter(username='admin').exists():
            print("Admin user already exists")
            return CustomUser.objects.get(username='admin')

        # 创建管理员用户
        admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@library.com',
            password='admin123',
            first_name='管理员',
            last_name='用户',
            role='admin',
            phone='1234567890',
            address='系统管理员'
        )
        print(f"Admin user created: {admin.username}")
        return admin

    except Exception as e:
        print(f"Error creating admin: {e}")
        return None

def create_test_user():
    """创建测试用户"""
    print("Creating test user...")

    try:
        from accounts.models import CustomUser

        # 检查是否已存在测试用户
        if CustomUser.objects.filter(username='user').exists():
            print("Test user already exists")
            return CustomUser.objects.get(username='user')

        # 创建测试用户
        user = CustomUser.objects.create_user(
            username='user',
            email='user@library.com',
            password='user123',
            first_name='普通',
            last_name='用户',
            role='user',
            phone='0987654321',
            address='测试用户'
        )
        print(f"Test user created: {user.username}")
        return user

    except Exception as e:
        print(f"Error creating test user: {e}")
        return None

def create_categories():
    """创建分类"""
    print("Creating categories...")

    try:
        from categories.models import Category

        categories_data = [
            {'name': '小说', 'description': '各类小说作品'},
            {'name': '科技', 'description': '科学技术类书籍'},
            {'name': '历史', 'description': '历史类书籍'},
            {'name': '文学', 'description': '文学作品'},
            {'name': '教育', 'description': '教育类书籍'},
        ]

        created_categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                print(f"  Created category: {category.name}")
            else:
                print(f"  Category already exists: {category.name}")
            created_categories.append(category)

        return created_categories

    except Exception as e:
        print(f"Error creating categories: {e}")
        return []

def create_books(categories):
    """创建图书"""
    print("Creating books...")

    try:
        from books.models import Book
        from django.utils import timezone

        books_data = [
            {
                'title': 'Python编程从入门到实践',
                'author': 'Eric Matthes',
                'isbn': '9787115546081',
                'publisher': '人民邮电出版社',
                'publication_date': '2020-01-01',
                'category': categories[1],  # 科技
                'description': '一本针对所有层次Python读者而作的Python入门书。',
                'total_copies': 5,
                'available_copies': 5,
                'location': 'A1-001'
            },
            {
                'title': '红楼梦',
                'author': '曹雪芹',
                'isbn': '9787020002207',
                'publisher': '人民文学出版社',
                'publication_date': '2008-07-01',
                'category': categories[3],  # 文学
                'description': '中国古典文学四大名著之一。',
                'total_copies': 3,
                'available_copies': 2,
                'location': 'B2-001'
            },
            {
                'title': '史记',
                'author': '司马迁',
                'isbn': '9787101003048',
                'publisher': '中华书局',
                'publication_date': '2006-06-01',
                'category': categories[2],  # 历史
                'description': '中国第一部纪传体通史。',
                'total_copies': 2,
                'available_copies': 1,
                'location': 'C3-001'
            },
            {
                'title': '三体',
                'author': '刘慈欣',
                'isbn': '9787536692930',
                'publisher': '重庆出版社',
                'publication_date': '2008-01-01',
                'category': categories[0],  # 小说
                'description': '中国科幻基石之作。',
                'total_copies': 4,
                'available_copies': 3,
                'location': 'D4-001'
            },
            {
                'title': '教育心理学',
                'author': '陈琦',
                'isbn': '9787040415061',
                'publisher': '高等教育出版社',
                'publication_date': '2015-05-01',
                'category': categories[4],  # 教育
                'description': '教育心理学经典教材。',
                'total_copies': 2,
                'available_copies': 2,
                'location': 'E5-001'
            }
        ]

        created_books = []
        for book_data in books_data:
            book, created = Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults=book_data
            )
            if created:
                print(f"  Created book: {book.title}")
            else:
                print(f"  Book already exists: {book.title}")
            created_books.append(book)

        return created_books

    except Exception as e:
        print(f"Error creating books: {e}")
        return []

def main():
    """主函数"""
    print("=" * 50)
    print("Django Library Management System Setup")
    print("=" * 50)

    # 创建用户
    admin = create_admin_user()
    user = create_test_user()

    # 创建分类和图书
    categories = create_categories()
    if categories:
        books = create_books(categories)

    print("\nSetup completed!")
    print("You can now login with:")
    print("Admin: username=admin, password=admin123")
    print("User:  username=user, password=user123")
    print("\nRun 'python manage.py runserver' to start the server")

if __name__ == '__main__':
    main()