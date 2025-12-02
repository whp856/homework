#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from books.models import Book
from borrowing.models import BorrowRecord

User = get_user_model()

def test_borrowing():
    print("=== 测试借阅功能 ===")

    # 获取测试用户
    normal_user = User.objects.filter(role='user').first()
    admin_user = User.objects.filter(role='admin').first()

    if not normal_user:
        print("没有找到普通用户")
        return

    if not admin_user:
        print("没有找到管理员用户")
        return

    print(f"普通用户: {normal_user.username}")
    print(f"管理员用户: {admin_user.username}")

    # 获取测试图书
    test_book = Book.objects.filter(available_copies__gt=0).first()
    if not test_book:
        print("没有找到可借阅的图书")
        return

    print(f"测试图书: {test_book.title}")
    print(f"总册数: {test_book.total_copies}")
    print(f"可借册数: {test_book.available_copies}")
    print(f"状态: {test_book.status}")

    # 清理现有借阅记录
    BorrowRecord.objects.filter(
        user__in=[normal_user, admin_user],
        book=test_book,
        status='borrowed'
    ).delete()

    # 重置图书状态
    test_book.available_copies = test_book.total_copies
    test_book.status = 'available'
    test_book.save()
    print("已清理现有借阅记录")

    # 测试普通用户借阅
    client = Client()
    client.force_login(normal_user)

    response = client.post(f'/borrowing/borrow/{test_book.id}/')
    print(f"普通用户借阅状态码: {response.status_code}")

    if response.status_code == 302:
        normal_record = BorrowRecord.objects.filter(
            user=normal_user,
            book=test_book,
            status='borrowed'
        ).first()

        if normal_record:
            print(f"普通用户借阅成功")
            print(f"应还时间: {normal_record.due_date}")

            # 检查图书状态
            test_book.refresh_from_db()
            print(f"图书剩余可借: {test_book.available_copies}")

    # 测试管理员借阅
    admin_client = Client()
    admin_client.force_login(admin_user)

    response = admin_client.post(f'/borrowing/borrow/{test_book.id}/')
    print(f"管理员借阅状态码: {response.status_code}")

    if response.status_code == 302:
        admin_record = BorrowRecord.objects.filter(
            user=admin_user,
            book=test_book,
            status='borrowed'
        ).first()

        if admin_record:
            print(f"管理员借阅成功")
            print(f"应还时间: {admin_record.due_date}")

            # 检查管理员借阅时间是否更长
            if admin_record.due_date > normal_record.due_date:
                print(f"管理员借阅时间更长")

            # 测试管理员归还普通用户的书
            return_response = admin_client.post(f'/borrowing/return/{normal_record.id}/')
            if return_response.status_code == 302:
                normal_record.refresh_from_db()
                if normal_record.status == 'returned':
                    print(f"管理员可以归还普通用户的书")

    # 测试重复借阅
    response = client.post(f'/borrowing/borrow/{test_book.id}/')
    print(f"重复借阅状态码: {response.status_code}")

    # 检查图书最终状态
    test_book.refresh_from_db()
    active_records = BorrowRecord.objects.filter(
        book=test_book,
        status='borrowed'
    ).count()

    print(f"最终状态:")
    print(f"图书可借数: {test_book.available_copies}")
    print(f"活跃借阅记录: {active_records}")
    print(f"预期可借数: {test_book.total_copies - active_records}")

    if test_book.available_copies == test_book.total_copies - active_records:
        print(f"状态一致性正确")
    else:
        print(f"状态不一致!")

if __name__ == "__main__":
    test_borrowing()