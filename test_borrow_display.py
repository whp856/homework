#!/usr/bin/env python
"""
测试借阅显示问题
诊断详情页面显示的借阅状态
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from books.models import Book
from borrowing.models import BorrowRecord
from django.contrib.auth import get_user_model

User = get_user_model()

def test_borrow_display_issue():
    """测试借阅显示问题"""
    print("=== 测试借阅显示问题 ===\n")

    # 1. 检查所有图书
    books = Book.objects.all()
    print(f"总图书数: {books.count()}")

    # 2. 检查具体图书的状态
    test_book = Book.objects.filter(available_copies__gt=0).first()
    if not test_book:
        print("没有找到可借阅的图书")
        return

    print(f"\n测试图书: {test_book.title}")
    print(f"  总册数: {test_book.total_copies}")
    print(f"  可借册数: {test_book.available_copies}")
    print(f"  图书状态: {test_book.status}")
    print(f"  is_available: {test_book.is_available}")
    print(f"  can_borrow: {test_book.can_borrow()}")

    # 3. 检查借阅记录
    records = BorrowRecord.objects.filter(book=test_book)
    print(f"\n借阅记录数: {records.count()}")

    for record in records:
        print(f"  记录: 用户={record.user.username}, 状态={record.status}, 借阅时间={record.borrow_date}")

    # 4. 检查数据一致性
    active_records = records.filter(status='borrowed')
    expected_available = test_book.total_copies - active_records.count()

    print(f"\n数据检查:")
    print(f"  活跃借阅数: {active_records.count()}")
    print(f"  预期可借数: {expected_available}")
    print(f"  实际可借数: {test_book.available_copies}")

    if test_book.available_copies == expected_available:
        print(f"  [OK] 数据一致")
    else:
        print(f"  [ERROR] 数据不一致!")

    # 5. 测试不同用户的借阅状态
    print(f"\n=== 测试用户借阅权限 ===")
    users = User.objects.all()[:3]

    for user in users:
        print(f"\n用户: {user.username} (管理员: {user.is_admin})")

        # 检查用户是否已借阅
        existing_record = BorrowRecord.objects.filter(
            user=user,
            book=test_book,
            status='borrowed'
        ).first()

        if existing_record:
            print(f"  已借阅: 是 (记录ID: {existing_record.id})")
        else:
            print(f"  已借阅: 否")

        # 模拟查看详情页面时的状态
        print(f"  书籍状态: {test_book.status}")
        print(f"  可借数量: {test_book.available_copies}")
        print(f"  是否可借: {test_book.is_available}")

def test_book_detail_logic():
    """测试图书详情页面的逻辑"""
    print("\n=== 测试详情页面逻辑 ===")

    # 获取测试图书
    test_book = Book.objects.first()
    if not test_book:
        print("没有找到测试图书")
        return

    print(f"测试图书: {test_book.title}")

    # 手动检查is_available逻辑
    print(f"\n手动检查:")
    print(f"  available_copies > 0: {test_book.available_copies > 0}")
    print(f"  status == 'available': {test_book.status == 'available'}")

    manual_available = test_book.available_copies > 0 and test_book.status == 'available'
    print(f"  手动计算: {manual_available}")
    print(f"  属性返回: {test_book.is_available}")

    if manual_available != test_book.is_available:
        print(f"  [ERROR] is_available属性计算错误!")
    else:
        print(f"  [OK] is_available属性正确")

    # 检查can_borrow方法
    print(f"\ncan_borrow方法:")
    print(f"  can_borrow(): {test_book.can_borrow()}")

    # 检查Book模型的available_copies属性
    print(f"\navailable_copies属性:")
    print(f"  类型: {type(test_book.available_copies)}")
    print(f"  值: {test_book.available_copies}")

    # 检查BorrowRecord的status字段
    print(f"\n相关借阅记录:")
    records = BorrowRecord.objects.filter(book=test_book)
    for record in records:
        print(f"  记录: ID={record.id}, 用户={record.user.username}, 状态={record.status}")

def test_template_variables():
    """测试模板变量"""
    print("\n=== 测试模板变量 ===")

    test_book = Book.objects.first()
    if not test_book:
        print("没有找到测试图书")
        return

    print(f"图书: {test_book.title}")

    # 模拟在模板中访问这些变量
    template_context = {
        'book': test_book,
        'user': None,  # 未登录用户
        'user.is_authenticated': False
    }

    print(f"\n模板上下文:")
    for key, value in template_context.items():
        print(f"  {key}: {value}")

    # 测试模板条件
    print(f"\n模板条件测试:")
    print(f"  用户登录状态: {template_context['user.is_authenticated']}")
    print(f"  图书可借状态: {template_context['book'].is_available}")

if __name__ == "__main__":
    test_borrow_display_issue()
    test_book_detail_logic()
    test_template_variables()