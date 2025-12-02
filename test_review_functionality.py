#!/usr/bin/env python
"""
测试评论功能
诊断评论功能不可用的问题
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from books.models import Book
from reviews.models import Review

User = get_user_model()

def test_review_functionality():
    """测试评论功能"""
    print("=== 测试评论功能 ===\n")

    # 1. 检查应用配置
    print("1. 应用配置检查:")
    try:
        # 直接导入模型来检查应用是否正常加载
        from reviews.models import Review
        print(f"  评论应用已加载: Review模型可用")
        print(f"  应用配置: 正常")
    except Exception as e:
        print(f"  [ERROR] 评论应用加载失败: {str(e)}")
        return

    # 2. 检查数据
    print("\n2. 数据检查:")
    users = User.objects.all()
    books = Book.objects.all()
    reviews = Review.objects.all()

    print(f"  总用户数: {users.count()}")
    print(f"  总图书数: {books.count()}")
    print(f"  总评论数: {reviews.count()}")

    approved_reviews = reviews.filter(is_approved=True)
    pending_reviews = reviews.filter(is_approved=False)

    print(f"  已审核评论数: {approved_reviews.count()}")
    print(f"  待审核评论数: {pending_reviews.count()}")

    # 3. 获取测试数据
    test_user = User.objects.filter(role='user').first()
    admin_user = User.objects.filter(role='admin').first()
    test_book = Book.objects.first()

    if not all([test_user, admin_user, test_book]):
        print("缺少测试数据")
        return

    print(f"\n测试用户: {test_user.username}")
    print(f"管理员用户: {admin_user.username}")
    print(f"测试图书: {test_book.title}")

    # 4. 测试URL访问
    print("\n3. URL访问测试:")
    client = Client()

    # 测试未登录访问
    print("\n  未登录用户访问:")
    urls_to_test = [
        ('my_reviews', '我的评论'),
        ('book_reviews', '图书评论'),
        ('create_review', '创建评论'),
    ]

    for url_name, description in urls_to_test:
        try:
            url = f'/reviews/{url_name}/' if url_name != 'book_reviews' else f'/reviews/{url_name}/{test_book.id}/'
            response = client.get(url)
            print(f"    {description} ({url_name}): {response.status_code}")
            if response.status_code == 200:
                print(f"      [OK] 页面可访问")
            elif response.status_code == 302:
                print(f"      [重定向] 可能需要登录")
            else:
                print(f"      [ERROR] 状态码: {response.status_code}")
        except Exception as e:
            print(f"    [ERROR] {description}: {str(e)}")

    # 5. 测试登录用户访问
    print("\n  登录用户访问:")
    client.force_login(test_user)

    for url_name, description in urls_to_test:
        try:
            url = f'/reviews/{url_name}/' if url_name != 'book_reviews' else f'/reviews/{url_name}/{test_book.id}/'
            response = client.get(url)
            print(f"    {description} ({url_name}): {response.status_code}")
            if response.status_code == 200:
                print(f"      [OK] 页面可访问")
                # 检查页面内容
                content = response.content.decode('utf-8', errors='ignore')
                if '添加评论' in content:
                    print(f"      [OK] 包含添加评论按钮")
                elif '编辑' in content:
                    print(f"      [OK] 包含编辑按钮")
                elif '删除' in content:
                    print(f"      [OK] 包含删除按钮")
            else:
                print(f"      [ERROR] 页面内容异常")
        except Exception as e:
            print(f"    [ERROR] {description}: {str(e)}")

    # 6. 测试评论创建功能
    print("\n  测试评论创建:")
    try:
        url = f'/reviews/create/{test_book.id}/'
        response = client.post(url, {
            'rating': 5,
            'comment': '这是一条测试评论，功能正常！'
        })

        print(f"    创建评论请求: {response.status_code}")

        if response.status_code == 302:
            # 检查是否创建了评论
            review = Review.objects.filter(
                user=test_user,
                book=test_book,
                comment='这是一条测试评论，功能正常！'
            ).first()

            if review:
                print(f"    [OK] 评论创建成功")
                print(f"      评论ID: {review.id}")
                print(f"      评分: {review.rating}")
                print(f"      内容: {review.comment}")
                print(f"      审核状态: {review.is_approved}")
                print(f"      创建时间: {review.created_at}")
            else:
                print(f"    [ERROR] 评论创建失败，未找到记录")
        else:
            print(f"    [ERROR] 评论创建失败: {response.status_code}")

    except Exception as e:
        print(f"    [ERROR] 评论创建异常: {str(e)}")

    # 7. 测试评论列表功能
    print("\n  测试评论列表功能:")
    try:
        response = client.get(f'/reviews/book/{test_book.id}/')
        print(f"    图书评论列表: {response.status_code}")

        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            if 'book_reviews' in content or '评论列表' in content:
                print(f"      [OK] 评论列表页面正常")
            else:
                print(f"      [ERROR] 页面内容异常")
        else:
            print(f"    [ERROR] 状态码: {response.status_code}")

    except Exception as e:
        print(f"    [ERROR] 评论列表访问异常: {str(e)}")

    # 8. 测试管理员功能
    print("\n  测试管理员功能:")
    client.force_login(admin_user)

    admin_functions = [
        ('review_list', '评论管理'),
        ('delete_review_admin', '删除评论'),
    ]

    for url_name, description in admin_functions:
        try:
            response = client.get(f'/reviews/{url_name}/')
            print(f"    {description} ({url_name}): {response.status_code}")
            if response.status_code == 200:
                print(f"      [OK] 管理员功能可用")
            else:
                print(f"      [ERROR] 状态码: {response.status_code}")
        except Exception as e:
            print(f"    [ERROR] {description}: {str(e)}")

    # 9. 检查模板文件
    print("\n9. 模板文件检查:")
    template_files = [
        'book_reviews.html',
        'my_reviews.html',
        'review_form.html',
        'review_list.html'
    ]

    import os.path
    templates_dir = 'templates/reviews/'

    for template_file in template_files:
        template_path = os.path.join(templates_dir, template_file)
        if os.path.exists(template_path):
            print(f"  [OK] {template_file} 存在")
        else:
            print(f"  [ERROR] {template_file} 不存在")

if __name__ == "__main__":
    test_review_functionality()