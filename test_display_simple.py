#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from books.models import Book
from borrowing.models import BorrowRecord

def test_display():
    print("=== 测试图书显示 ===")

    # 检查所有图书
    books = Book.objects.all()
    print(f"总图书数: {books.count()}")

    available_books = books.filter(available_copies__gt=0)
    print(f"可借图书数: {available_books.count()}")

    # 检查数据一致性
    inconsistencies = []
    for book in books:
        # 计算实际可借数量
        active_count = BorrowRecord.objects.filter(book=book, status='borrowed').count()
        expected_available = book.total_copies - active_count

        if book.available_copies != expected_available:
            inconsistencies.append({
                'title': book.title,
                'actual': book.available_copies,
                'expected': expected_available,
                'active': active_count
            })

    print(f"数据一致性检查:")
    if inconsistencies:
        print(f"发现 {len(inconsistencies)} 个数据不一致:")
        for inc in inconsistencies[:5]:
            print(f"  图书: {inc['title']}")
            print(f"    实际可借: {inc['actual']}")
            print(f"    预期可借: {inc['expected']}")
            print(f"    活跃借阅: {inc['active']}")
    else:
        print("所有图书数据一致")

    # 检查模板字段
    print("\n模板字段检查:")
    test_book = books.first()
    if test_book:
        fields_to_check = [
            'title', 'author', 'isbn', 'description',
            'total_copies', 'available_copies', 'status'
        ]

        for field in fields_to_check:
            if hasattr(test_book, field):
                value = getattr(test_book, field)
                print(f"  {field}: {value}")
            else:
                print(f"  字段不存在: {field}")

        # 检查属性
        print("\n属性检查:")
        properties_to_check = ['is_available', 'borrowed_copies']
        for prop in properties_to_check:
            if hasattr(test_book, prop):
                value = getattr(test_book, prop)
                print(f"  {prop}: {value}")
            else:
                print(f"  属性不存在: {prop}")

if __name__ == "__main__":
    test_display()