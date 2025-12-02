#!/usr/bin/env python
"""
测试URL路径问题
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.models import Book

User = get_user_model()

def test_url_patterns():
    """测试URL路径问题"""
    print("=== 测试URL路径问题 ===\n")

    client = Client()
    test_book = Book.objects.first()
    test_user = User.objects.filter(role='user').first()

    if not test_book or not test_user:
        print("缺少测试数据")
        return

    print(f"测试图书ID: {test_book.id}")
    print(f"测试用户: {test_user.username}")

    # 清理现有评论
    from reviews.models import Review
    Review.objects.filter(user=test_user, book=test_book).delete()

    # 测试URL反向解析
    print("\n测试URL反向解析:")
    urls_to_test = [
        ('my_reviews', '我的评论'),
        ('book_reviews', '图书评论'),
        ('create_review', '创建评论'),
        ('edit_review', '编辑评论'),
        ('delete_review', '删除评论'),
        ('review_list', '评论管理'),
    ]

    client.force_login(test_user)

    for url_name, description in urls_to_test:
        try:
            if url_name == 'book_reviews':
                url = reverse(f'reviews:{url_name}', kwargs={'book_id': test_book.id})
            else:
                url = reverse(f'reviews:{url_name}')

            print(f"{url_name}: {url}")

            # 测试URL访问
            response = client.get(url)
            print(f"  访问结果: {response.status_code}")

            if response.status_code == 200:
                print("  [成功]")
                # 检查页面是否包含预期内容
                content = response.content.decode('utf-8', errors='ignore')
                if description in content or '添加评论' in content:
                    print("  [成功] 页面内容正常")
                else:
                    print("  [警告] 页面内容可能不完整")
            elif response.status_code == 302:
                print("  [重定向]")
            elif response.status_code == 404:
                print("  [错误] URL未找到")
            else:
                print(f"  [未知] 状态码: {response.status_code}")

        except Exception as e:
            print(f"  [错误] {str(e)}")

    print("\n直接测试URL模式:")
    test_patterns = [
        '/reviews/book/1/',
        '/reviews/book/1/',
        '/reviews/create/1/',
        '/reviews/create/1/',
        '/reviews/book/create/',
        '/reviews/book/1/create/',
    ]

    for pattern in test_patterns:
        try:
            if pattern == '/reviews/book/1/':
                expected_url = reverse('reviews:book_reviews', kwargs={'book_id': 1})
            elif pattern == '/reviews/book/1/':
                expected_url = reverse('reviews:book_reviews', kwargs={'book_id': 1})
            elif pattern == '/reviews/create/1/':
                expected_url = reverse('reviews:create_review', kwargs={'book_id': 1})
            elif pattern == '/reviews/create/1/':
                expected_url = reverse('reviews:create_review', kwargs={'book_id': 1})
            elif pattern == '/reviews/book/create/':
                expected_url = reverse('reviews:create_review', kwargs={'book_id': 1})
            elif pattern == '/reviews/book/1/create/':
                expected_url = reverse('reviews:create_review', kwargs={'book_id': 1})
            else:
                expected_url = "未匹配"

            print(f"  路径: {pattern}")
            print(f"  期望URL: {expected_url}")

        except Exception as e:
            print(f"  [错误] {str(e)}")

if __name__ == "__main__":
    test_url_patterns()