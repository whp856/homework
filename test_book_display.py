#!/usr/bin/env python
"""
测试图书显示一致性
检查最新上架页面和详情页面的借阅信息
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from books.models import Book
from borrowing.models import BorrowRecord

User = get_user_model()

def test_book_display_consistency():
    """测试图书显示一致性"""
    print("=== 测试图书显示一致性 ===\n")

    # 1. 检查所有图书的基本信息
    print("1. 图书基本信息检查:")
    books = Book.objects.all()
    print(f"   总图书数: {books.count()}")

    available_books = books.filter(available_copies__gt=0)
    print(f"   可借图书数: {available_books.count()}")

    # 2. 检查具体图书的属性
    print("\n2. 图书属性检查:")
    for book in books[:5]:  # 只检查前5本
        print(f"\n   图书: {book.title}")
        print(f"   - 总册数 (total_copies): {book.total_copies}")
        print(f"   - 可借册数 (available_copies): {book.available_copies}")
        print(f"   - 状态 (status): {book.status}")

        # 检查 is_available 属性
        print(f"   - is_available: {book.is_available}")

        # 手动检查
        manual_available = book.available_copies > 0 and book.status == 'available'
        print(f"   - 手动检查可用: {manual_available}")

        # 检查一致性
        if book.is_available == manual_available:
            print(f"   - ✅ 状态一致")
        else:
            print(f"   - ❌ 状态不一致!")

    # 3. 检查借阅记录
    print("\n3. 借阅记录检查:")
    borrow_records = BorrowRecord.objects.all()
    print(f"   总借阅记录数: {borrow_records.count()}")

    active_records = borrow_records.filter(status='borrowed')
    print(f"   活跃借阅记录数: {active_records.count()}")

    returned_records = borrow_records.filter(status='returned')
    print(f"   已归还记录数: {returned_records.count()}")

    overdue_records = [r for r in active_records if r.is_overdue]
    print(f"   逾期记录数: {len(overdue_records)}")

    # 4. 检查数据一致性
    print("\n4. 数据一致性检查:")
    inconsistencies = []

    for book in books:
        # 计算预期可借数量
        active_count = BorrowRecord.objects.filter(book=book, status='borrowed').count()
        expected_available = book.total_copies - active_count

        if book.available_copies != expected_available:
            inconsistencies.append({
                'book': book.title,
                'actual': book.available_copies,
                'expected': expected_available,
                'active_borrows': active_count
            })

    if inconsistencies:
        print(f"   ❌ 发现 {len(inconsistencies)} 个数据不一致:")
        for inconsistency in inconsistencies[:5]:  # 只显示前5个
            print(f"   - {inconsistency['book']}")
            print(f"     实际可借: {inconsistency['actual']}")
            print(f"     预期可借: {inconsistency['expected']}")
            print(f"     活跃借阅: {inconsistency['active_borrows']}")
    else:
        print("   ✅ 所有图书数据一致")

    # 5. 检查模板中可能的问题
    print("\n5. 模板字段检查:")
    test_book = books.first()
    if test_book:
        print(f"   测试图书: {test_book.title}")

        # 检查模板中使用的字段是否存在
        fields_to_check = [
            'title', 'author', 'isbn', 'description',
            'total_copies', 'available_copies', 'status',
            'publication_date', 'category'
        ]

        for field in fields_to_check:
            if hasattr(test_book, field):
                value = getattr(test_book, field)
                print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ {field}: 字段不存在")

        # 检查属性
        properties_to_check = ['is_available', 'borrowed_copies']
        for prop in properties_to_check:
            if hasattr(test_book, prop):
                value = getattr(test_book, prop)
                print(f"   ✅ {prop}: {value}")
            else:
                print(f"   ❌ {prop}: 属性不存在")

def test_borrow_record_display():
    """测试借阅记录显示"""
    print("\n=== 测试借阅记录显示 ===")

    # 获取用户
    users = User.objects.all()[:2]

    for user in users:
        print(f"\n用户: {user.username}")

        # 获取用户的借阅记录
        records = BorrowRecord.objects.filter(user=user)[:3]

        if records:
            for record in records:
                print(f"   借阅记录:")
                print(f"   - 图书: {record.book.title}")
                print(f"   - 状态: {record.status}")
                print(f"   - 借阅时间: {record.borrow_date}")
                print(f"   - 应还时间: {record.due_date}")
                print(f"   - 归还时间: {record.return_date}")
                print(f"   - 是否逾期: {record.is_overdue}")
                if record.is_overdue:
                    print(f"   - 逾期天数: {record.days_overdue}")
                print()
        else:
            print("   暂无借阅记录")

def test_template_compatibility():
    """测试模板兼容性"""
    print("\n=== 测试模板兼容性 ===")

    # 检查图书详情页面模板中使用的字段
    test_book = Book.objects.first()
    if not test_book:
        print("   ⚠️ 没有找到测试图书")
        return

    print(f"   测试图书: {test_book.title}")

    # 模拟模板中的变量访问
    template_vars = {
        'book.title': test_book.title,
        'book.author': test_book.author,
        'book.isbn': test_book.isbn,
        'book.total_copies': test_book.total_copies,
        'book.available_copies': test_book.available_copies,
        'book.is_available': test_book.is_available,
        'book.status': test_book.status,
        'book.category.name': test_book.category.name if test_book.category else None,
        'book.publication_date': test_book.publication_date,
        'book.description': test_book.description,
    }

    print("   模板变量检查:")
    for var_name, value in template_vars.items():
        if value is not None:
            print(f"   ✅ {var_name}: {str(value)[:50]}")
        else:
            print(f"   ⚠️ {var_name}: None")

if __name__ == "__main__":
    test_book_display_consistency()
    test_borrow_record_display()
    test_template_compatibility()
    print("\n=== 测试完成 ===")