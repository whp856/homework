import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from books.models import Book

User = get_user_model()

def test_review_final():
    print("=== 测试评论功能 ===")

    # 获取测试数据
    test_book = Book.objects.first()
    test_user = User.objects.filter(role='user').first()

    if not test_book or not test_user:
        print("缺少测试数据")
        return

    print("测试图书: " + str(test_book.title))
    print("测试用户: " + test_user.username)

    # 清理现有评论
    from reviews.models import Review
    Review.objects.filter(user=test_user, book=test_book).delete()

    # 测试URL
    client = Client()
    client.force_login(test_user)

    urls = [
        ("我的评论", "reviews:my_reviews"),
        ("图书评论", "reviews:book_reviews", {"book_id": test_book.id}),
        ("创建评论", "reviews:create_review", {"book_id": test_book.id}),
        ("查看评论", "reviews:book_reviews", {"book_id": test_book.id}),
    ]

    print("\n测试URL:")
    for name, url_name, kwargs in urls:
        try:
            if kwargs:
                url = reverse(f"reviews:{url_name}", kwargs=kwargs)
            else:
                url = reverse(f"reviews:{url_name}")

            response = client.get(url)
            print(f"  {name}: {url} -> {response.status_code}")

            if response.status_code == 200:
                print("    [成功]")
            else:
                print(f"    [失败]: {response.status_code}")
        except Exception as e:
            print(f"  [错误]: {str(e)}")

if __name__ == "__main__":
    test_review_final()