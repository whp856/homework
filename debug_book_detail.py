#!/usr/bin/env python
"""
调试图书详情页面
测试模板渲染和借阅逻辑
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from books.models import Book
from borrowing.models import BorrowRecord

User = get_user_model()

def debug_book_detail():
    """调试图书详情页面"""
    print("=== 调试图书详情页面 ===\n")

    # 获取测试用户和图书
    test_user = User.objects.filter(role='user').first()
    admin_user = User.objects.filter(role='admin').first()
    test_book = Book.objects.first()

    if not all([test_user, admin_user, test_book]):
        print("缺少测试数据")
        return

    print(f"测试图书: {test_book.title}")
    print(f"  总册数: {test_book.total_copies}")
    print(f"  可借册数: {test_book.available_copies}")
    print(f"  图书状态: {test_book.status}")
    print(f"  is_available: {test_book.is_available}")
    print(f"  can_borrow: {test_book.can_borrow()}")

    # 检查借阅记录
    records = BorrowRecord.objects.filter(book=test_book)
    active_records = records.filter(status='borrowed')
    print(f"  活跃借阅: {active_records.count()}")

    # 模拟不同的用户状态
    contexts = [
        {
            'name': '未登录用户',
            'user': None,
            'user.is_authenticated': False,
            'user.is_admin': False
        },
        {
            'name': '普通用户(未借阅)',
            'user': test_user,
            'user.is_authenticated': True,
            'user.is_admin': False
        },
        {
            'name': '普通用户(已借阅)',
            'user': test_user,
            'user.is_authenticated': True,
            'user.is_admin': False,
            'has_borrowed': True
        },
        {
            'name': '管理员用户',
            'user': admin_user,
            'user.is_authenticated': True,
            'user.is_admin': True
        }
    ]

    # 添加图书到上下文
    for context in contexts:
        context['book'] = test_book

        print(f"\n=== {context['name']} ===")
        print(f"  用户登录: {context['user.is_authenticated']}")
        print(f"  是否管理员: {context.get('user.is_admin', False)}")
        print(f"  图书可借: {test_book.is_available}")
        print(f"  图书状态: {test_book.status}")

        # 模拟模板条件
        if context['user.is_authenticated']:
            print(f"  用户已登录，会显示借阅按钮")
            if test_book.is_available:
                print(f"  图书可借阅，显示[借阅本书]按钮")
            else:
                print(f"  图书不可借阅，显示[当前不可借阅]按钮")
        else:
            print(f"  用户未登录，显示[登录后借阅]按钮")

    # 测试实际的借阅操作
    print(f"\n=== 测试实际借阅 ===")
    if test_user:
        # 清理现有借阅记录
        BorrowRecord.objects.filter(
            user=test_user,
            book=test_book,
            status='borrowed'
        ).delete()

        # 重置图书状态
        test_book.available_copies = test_book.total_copies
        test_book.status = 'available'
        test_book.save()

        print(f"清理后状态:")
        print(f"  图书可借: {test_book.is_available}")

        # 模拟借阅请求
        from django.test import Client
        client = Client()
        client.force_login(test_user)

        print(f"\n用户 {test_user.username} 尝试借阅图书 {test_book.title}")

        # 检查借阅前的状态
        response = client.get(f'/books/{test_book.id}/')
        print(f"访问详情页状态: {response.status_code}")

        # 模拟点击借阅按钮
        response = client.post(f'/borrowing/borrow/{test_book.id}/')
        print(f"借阅请求状态: {response.status_code}")

        if response.status_code == 302:
            # 检查借阅记录
            record = BorrowRecord.objects.filter(
                user=test_user,
                book=test_book,
                status='borrowed'
            ).first()

            if record:
                print(f"借阅成功!")
                print(f"  借阅时间: {record.borrow_date}")
                print(f"  应还时间: {record.due_date}")

                # 检查图书状态
                test_book.refresh_from_db()
                print(f"  图书剩余可借: {test_book.available_copies}")
                print(f"  图书状态: {test_book.status}")
            else:
                print("借阅失败：未找到借阅记录")
        else:
            print(f"借阅失败，状态码: {response.status_code}")

if __name__ == "__main__":
    debug_book_detail()