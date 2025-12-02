#!/usr/bin/env python
"""
简单测试评论功能
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

def test_review_urls():
    """测试评论URL"""
    print("=== 测试评论URL ===\n")

    client = Client()

    # 获取测试图书
    test_book = Book.objects.first()
    test_user = User.objects.filter(role='user').first()

    if not test_book:
        print("没有测试图书")
        return

    print(f"测试图书: {test_book.title}")
    print(f"测试用户: {test_user.username}")

    # 清理现有评论
    Review.objects.filter(
        user=test_user,
        book=test_book
    ).delete()

    # 测试各个URL
    urls_to_test = [
        ('我的评论', '/reviews/my-reviews/'),
        ('图书评论', '/reviews/book/1/'),
        ('创建评论', '/reviews/create/1/'),
    ]

    print("\n测试URL访问:")
    client.force_login(test_user)

    for name, url in urls_to_test:
        try:
            response = client.get(url)
            print(f"{name}: {url} -> {response.status_code}")

            if response.status_code == 200:
                print("  [成功]")
            elif response.status_code == 302:
                print("  [重定向]")
            else:
                print(f"  [失败]: {response.status_code}")

                # 尝试分析错误
                if 'not found' in response.content.decode('utf-8', errors='ignore').lower():
                    print("  [原因]: URL未找到")
                elif 'page not found' in response.content.decode('utf-8', errors='ignore').lower():
                    print("  [原因]: 页面未找到")

        except Exception as e:
            print(f"  [错误]: {str(e)}")

if __name__ == "__main__":
    test_review_urls()