#!/usr/bin/env python
"""
完整测试借阅功能
验证所有借阅场景是否正常工作
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from books.models import Book
from borrowing.models import BorrowRecord
from django.utils import timezone

User = get_user_model()

def test_complete_borrowing_system():
    """完整测试借阅系统"""
    print("=== 完整测试借阅系统 ===\n")

    # 1. 检查系统状态
    print("1. 系统状态检查:")
    books = Book.objects.all()
    users = User.objects.all()

    print(f"  总图书数: {books.count()}")
    print(f"  总用户数: {users.count()}")

    available_books = books.filter(available_copies__gt=0)
    print(f"  可借图书数: {available_books.count()}")

    borrowed_books = books.filter(status='borrowed')
    print(f"  借出图书数: {borrowed_books.count()}")

    # 2. 获取测试用户
    normal_user = User.objects.filter(role='user').first()
    admin_user = User.objects.filter(role='admin').first()

    if not all([normal_user, admin_user]):
        print("缺少测试用户")
        return

    print(f"\n2. 测试用户:")
    print(f"  普通用户: {normal_user.username}")
    print(f"  管理员用户: {admin_user.username}")

    # 3. 获取测试图书
    test_books = Book.objects.filter(available_copies__gte=2)[:3]

    if not test_books:
        print("没有足够的测试图书")
        return

    # 4. 测试每个图书的借阅流程
    for i, test_book in enumerate(test_books):
        print(f"\n=== 测试图书 {i+1}: {test_book.title} ===")

        print(f"  基本信息:")
        print(f"    总册数: {test_book.total_copies}")
        print(f"    可借册数: {test_book.available_copies}")
        print(f"    图书状态: {test_book.status}")
        print(f"    是否可借: {test_book.is_available}")

        # 清理现有借阅记录
        BorrowRecord.objects.filter(
            book=test_book,
            status='borrowed'
        ).delete()

        # 重置图书状态
        test_book.available_copies = test_book.total_copies
        test_book.status = 'available'
        test_book.save()

        print(f"  清理后状态:")
        print(f"    可借册数: {test_book.available_copies}")
        print(f"    图书状态: {test_book.status}")
        print(f"    是否可借: {test_book.is_available}")

        # 测试普通用户借阅
        test_user_borrowing(normal_user, test_book, "普通用户")

        # 测试管理员借阅
        test_user_borrowing(admin_user, test_book, "管理员")

        # 测试并发借阅（模拟多个用户同时借阅）
        test_concurrent_borrowing(test_book)

def test_user_borrowing(user, book, user_type):
    """测试用户借阅功能"""
    print(f"\n--- {user_type}借阅测试 ---")

    client = Client()
    client.force_login(user)

    # 1. 访问图书详情页面
    response = client.get(f'/books/{book.id}/')
    print(f"访问详情页面: 状态码 {response.status_code}")

    if response.status_code == 200:
        content = response.content.decode('utf-8', errors='ignore')

        # 检查页面内容
        if "借阅本书" in content and book.is_available:
            print(f"  [OK] 页面显示借阅按钮")
        elif "当前不可借阅" in content and not book.is_available:
            print(f"  [OK] 页面显示不可借阅按钮")
        else:
            print(f"  [WARNING] 页面显示异常")
            print(f"    图书可借: {book.is_available}")
            print(f"    页面内容包含借阅按钮: {'借阅本书' in content}")

    # 2. 尝试借阅
    response = client.post(f'/borrowing/borrow/{book.id}/')
    print(f"借阅请求: 状态码 {response.status_code}")

    if response.status_code == 302:
        # 检查借阅记录
        record = BorrowRecord.objects.filter(
            user=user,
            book=book,
            status='borrowed'
        ).first()

        if record:
            print(f"  [OK] 借阅成功")
            print(f"    借阅时间: {record.borrow_date}")
            print(f"    应还时间: {record.due_date}")

            # 检查图书状态是否正确更新
            book.refresh_from_db()
            print(f"    更新后可借数: {book.available_copies}")
            print(f"    更新后状态: {book.status}")

            return record
        else:
            print(f"  [ERROR] 借阅成功但未找到记录")

    else:
        print(f"  [ERROR] 借阅失败，状态码: {response.status_code}")
        if response.status_code == 302:
            # 跟踪重定向
            if response.has_header('Location'):
                print(f"    重定向到: {response['Location']}")

    return None

def test_concurrent_borrowing(book):
    """测试并发借阅"""
    print(f"\n--- 并发借阅测试 ---")

    users = User.objects.filter(role='user')[:min(3, book.total_copies)]

    if len(users) < 2:
        print("用户数量不足，跳过并发测试")
        return

    print(f"  使用 {len(users)} 个用户进行并发借阅")

    # 清理现有记录
    BorrowRecord.objects.filter(
        book=book,
        status='borrowed'
    ).delete()

    # 重置图书状态
    book.available_copies = book.total_copies
    book.status = 'available'
    book.save()

    # 并发借阅测试
    from concurrent.futures import ThreadPoolExecutor
    import time

    def borrow_book_concurrently(user):
        try:
            client = Client()
            client.force_login(user)

            # 稍微延迟，模拟真实场景
            time.sleep(0.1)

            response = client.post(f'/borrowing/borrow/{book.id}/')

            if response.status_code == 302:
                return {"success": True, "user": user.username}
            else:
                return {"success": False, "user": user.username, "status": response.status_code}

        except Exception as e:
            return {"success": False, "user": user.username, "error": str(e)}

    with ThreadPoolExecutor(max_workers=len(users)) as executor:
        futures = [executor.submit(borrow_book_concurrently, user) for user in users]

        results = []
        for future in futures:
            try:
                result = future.result(timeout=5)
                results.append(result)
            except Exception as e:
                results.append({"success": False, "error": str(e)})

    successful_borrows = [r for r in results if r.get("success", False)]
    failed_borrows = [r for r in results if not r.get("success", False)]

    print(f"  并发结果:")
    print(f"    成功借阅: {len(successful_borrows)}")
    for result in successful_borrows:
        print(f"      - {result['user']}")

    print(f"    失败借阅: {len(failed_borrows)}")
    for result in failed_borrows:
        error_msg = result.get('error', str(result.get('status', 'Unknown')))
        print(f"      - {result['user']}: {error_msg}")

    # 检查最终状态
    time.sleep(1)  # 等待所有操作完成

    book.refresh_from_db()
    actual_borrowed = BorrowRecord.objects.filter(book=book, status='borrowed').count()
    expected_available = book.total_copies - actual_borrowed

    print(f"  最终状态:")
    print(f"    实际借出数: {actual_borrowed}")
    print(f"    预期可借数: {expected_available}")
    print(f"    实际可借数: {book.available_copies}")

    if book.available_copies == expected_available:
        print(f"    [OK] 并发借阅数据一致")
    else:
        print(f"    [ERROR] 并发借阅数据不一致!")
        print(f"    实际可借数: {book.available_copies}")
        print(f"    预期可借数: {expected_available}")

def test_page_display_logic():
    """测试页面显示逻辑"""
    print("\n=== 页面显示逻辑测试 ===")

    test_book = Book.objects.first()
    if not test_book:
        print("没有测试图书")
        return

    print(f"测试图书: {test_book.title}")
    print(f"  总册数: {test_book.total_copies}")
    print(f"  可借册数: {test_book.available_copies}")
    print(f"  图书状态: {test_book.status}")

    # 手动计算is_available
    manual_available = test_book.available_copies > 0 and test_book.status == 'available'
    property_available = test_book.is_available

    print(f"  手动计算is_available: {manual_available}")
    print(f"  属性返回is_available: {property_available}")

    if manual_available != property_available:
        print(f"  [ERROR] is_available属性计算错误!")
    else:
        print(f"  [OK] is_available属性正确")

if __name__ == "__main__":
    test_complete_borrowing_system()
    test_page_display_logic()
    print("\n=== 测试完成 ===")