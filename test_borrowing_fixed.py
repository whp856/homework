#!/usr/bin/env python
"""
测试修复后的借阅功能
验证并发安全和权限控制
"""

import os
import django
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.db import transaction
from books.models import Book
from borrowing.models import BorrowRecord
from django.utils import timezone

User = get_user_model()

def test_borrowing_functionality():
    """测试借阅功能的完整性"""
    print("=== 测试修复后的借阅功能 ===\n")

    # 1. 检查用户
    users = User.objects.all()
    print(f"系统用户数: {users.count()}")
    for user in users:
        print(f"  - {user.username} (角色: {user.role}, 管理员: {user.is_admin})")

    # 2. 检查图书状态
    print(f"\n=== 图书状态检查 ===")
    books = Book.objects.all()
    available_books = books.filter(available_copies__gt=0)
    print(f"总图书数: {books.count()}")
    print(f"可借图书数: {available_books.count()}")

    if available_books.exists():
        test_book = available_books.first()
        print(f"\n测试图书: {test_book.title}")
        print(f"  - 总册数: {test_book.total_copies}")
        print(f"  - 可借册数: {test_book.available_copies}")
        print(f"  - 状态: {test_book.status}")
        print(f"  - 是否可借: {test_book.is_available}")

        # 3. 测试普通用户借阅
        normal_user = User.objects.filter(role='user').first()
        if normal_user:
            print(f"\n=== 测试普通用户借阅 ===")
            test_user_borrow(normal_user, test_book)

        # 4. 测试管理员借阅
        admin_user = User.objects.filter(role='admin').first()
        if admin_user:
            print(f"\n=== 测试管理员借阅 ===")
            test_user_borrow(admin_user, test_book)

        # 5. 测试并发借阅
        if test_book.total_copies >= 2:
            print(f"\n=== 测试并发借阅 ===")
            test_concurrent_borrowing(test_book)

def test_user_borrow(user, book):
    """测试单个用户借阅"""
    client = Client()
    client.force_login(user)

    # 检查用户是否已经借阅了这本书
    existing_record = BorrowRecord.objects.filter(
        user=user,
        book=book,
        status='borrowed'
    ).first()

    if existing_record:
        print(f"  用户 {user.username} 已经借阅了这本书")
        print(f"  借阅时间: {existing_record.borrow_date}")
        print(f"  应还时间: {existing_record.due_date}")
        return

    # 测试借阅请求
    response = client.post(f'/borrowing/borrow/{book.id}/')
    print(f"  借阅请求状态码: {response.status_code}")

    if response.status_code == 302:
        # 检查借阅记录是否创建成功
        record = BorrowRecord.objects.filter(
            user=user,
            book=book,
            status='borrowed'
        ).first()

        if record:
            print(f"  [成功] {user.username} 借阅成功")
            print(f"     借阅记录ID: {record.id}")
            print(f"     应还时间: {record.due_date}")

            # 检查图书状态是否正确更新
            book.refresh_from_db()
            print(f"     图书剩余可借: {book.available_copies}")

            # 清理测试数据
            record.return_book()
            print(f"     [成功] 测试后归还成功")
        else:
            print(f"  [失败] 借阅失败：未找到借阅记录")
    else:
        print(f"  [失败] 借阅请求失败，状态码: {response.status_code}")

def test_concurrent_borrowing(book):
    """测试并发借阅场景"""
    print(f"  测试图书: {book.title} (可借数量: {book.available_copies})")

    # 获取多个普通用户
    users = User.objects.filter(role='user')[:min(5, book.available_copies + 2)]
    if users.count() < 2:
        print("  [警告] 需要至少2个用户进行并发测试")
        return

    results = []
    errors = []

    def borrow_book_concurrently(user):
        try:
            client = Client()
            client.force_login(user)

            # 先清理用户可能的借阅记录
            BorrowRecord.objects.filter(
                user=user,
                book=book,
                status='borrowed'
            ).delete()

            # 重置图书状态
            book.available_copies = book.total_copies
            book.status = 'available'
            book.save()

            response = client.post(f'/borrowing/borrow/{book.id}/')
            return {
                'user': user.username,
                'status_code': response.status_code,
                'success': response.status_code == 302
            }
        except Exception as e:
            return {
                'user': user.username,
                'status_code': 0,
                'success': False,
                'error': str(e)
            }

    # 使用线程池模拟并发借阅
    with ThreadPoolExecutor(max_workers=min(5, users.count())) as executor:
        futures = [executor.submit(borrow_book_concurrently, user) for user in users]

        for future in futures:
            try:
                result = future.result(timeout=10)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

    print(f"  并发测试结果:")
    successful_borrows = [r for r in results if r['success']]
    failed_borrows = [r for r in results if not r['success']]

    print(f"    成功借阅: {len(successful_borrows)}")
    for borrow in successful_borrows:
        print(f"      - {borrow['user']}")

    print(f"    失败借阅: {len(failed_borrows)}")
    for borrow in failed_borrows:
        print(f"      - {borrow['user']}: {borrow.get('error', '状态码:'+str(borrow['status_code']))}")

    # 检查最终状态
    book.refresh_from_db()
    active_records = BorrowRecord.objects.filter(
        book=book,
        status='borrowed'
    ).count()

    print(f"  最终状态:")
    print(f"    图书可借数: {book.available_copies}")
    print(f"    活跃借阅记录: {active_records}")
    print(f"    预期可借数: {book.total_copies - active_records}")

    if book.available_copies == book.total_copies - active_records:
        print(f"    ✅ 状态一致性正确")
    else:
        print(f"    ❌ 状态不一致！")

    # 清理测试数据
    BorrowRecord.objects.filter(
        book=book,
        status='borrowed'
    ).delete()
    book.available_copies = book.total_copies
    book.status = 'available'
    book.save()

def test_admin_privileges():
    """测试管理员特权"""
    print(f"\n=== 测试管理员特权 ===")

    admin_user = User.objects.filter(role='admin').first()
    normal_user = User.objects.filter(role='user').first()
    test_book = Book.objects.filter(available_copies__gt=0).first()

    if not all([admin_user, normal_user, test_book]):
        print("  [警告] 缺少测试数据")
        return

    # 清理现有借阅记录
    BorrowRecord.objects.filter(
        book=test_book,
        status='borrowed'
    ).delete()
    test_book.available_copies = test_book.total_copies
    test_book.save()

    admin_client = Client()
    admin_client.force_login(admin_user)

    normal_client = Client()
    normal_client.force_login(normal_user)

    print(f"  测试图书: {test_book.title}")

    # 普通用户借阅
    response = normal_client.post(f'/borrowing/borrow/{test_book.id}/')
    normal_record = BorrowRecord.objects.filter(
        user=normal_user,
        book=test_book,
        status='borrowed'
    ).first()

    if normal_record:
        print(f"  [成功] 普通用户借阅成功")
        print(f"    应还时间: {normal_record.due_date}")

    # 管理员借阅同一本书
    response = admin_client.post(f'/borrowing/borrow/{test_book.id}/')
    admin_record = BorrowRecord.objects.filter(
        user=admin_user,
        book=test_book,
        status='borrowed'
    ).first()

    if admin_record:
        print(f"  [成功] 管理员借阅成功")
        print(f"    应还时间: {admin_record.due_date}")

        # 检查管理员借阅时间是否更长
        if admin_record.due_date > normal_record.due_date:
            print(f"    [成功] 管理员借阅时间更长")

        # 测试管理员归还普通用户的书
        return_response = admin_client.post(f'/borrowing/return/{normal_record.id}/')
        if return_response.status_code == 302:
            normal_record.refresh_from_db()
            if normal_record.status == 'returned':
                print(f"    [成功] 管理员可以归还普通用户的书")

    # 清理测试数据
    BorrowRecord.objects.filter(
        book=test_book,
        status__in=['borrowed', 'returned']
    ).delete()
    test_book.available_copies = test_book.total_copies
    test_book.status = 'available'
    test_book.save()

if __name__ == "__main__":
    test_borrowing_functionality()
    test_admin_privileges()
    print(f"\n=== 测试完成 ===")