#!/usr/bin/env python
"""
修复图书状态不一致问题
确保图书状态与available_copies一致
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.db import transaction
from books.models import Book
from borrowing.models import BorrowRecord

def fix_book_status_consistency():
    """修复图书状态一致性"""
    print("=== 修复图书状态一致性 ===\n")

    books = Book.objects.all()
    fixed_count = 0

    for book in books:
        print(f"检查图书: {book.title}")
        print(f"  当前状态: {book.status}")
        print(f"  总册数: {book.total_copies}")
        print(f"  可借册数: {book.available_copies}")

        # 计算实际借阅数量
        active_records = BorrowRecord.objects.filter(
            book=book,
            status='borrowed'
        ).count()

        expected_available = book.total_copies - active_records
        print(f"  活跃借阅数: {active_records}")
        print(f"  预期可借数: {expected_available}")

        # 根据实际情况确定正确状态
        if expected_available > 0:
            correct_status = 'available'
            print(f"  应设状态: {correct_status}")
        elif expected_available == 0:
            correct_status = 'borrowed'
            print(f"  应设状态: {correct_status}")
        else:
            # 这种情况不应该发生，说明数据有问题
            correct_status = 'borrowed'
            print(f"  数据异常，设为借出: {correct_status}")
            expected_available = 0

        # 检查当前状态是否正确
        status_needs_fix = False
        copies_needs_fix = False

        if book.status != correct_status:
            print(f"  [修复] 状态不一致: {book.status} -> {correct_status}")
            book.status = correct_status
            status_needs_fix = True

        if book.available_copies != expected_available:
            print(f"  [修复] 可借数量不一致: {book.available_copies} -> {expected_available}")
            book.available_copies = expected_available
            copies_needs_fix = True

        # 如果需要修复，保存图书
        if status_needs_fix or copies_needs_fix:
            book.save()
            fixed_count += 1
            print(f"  [已修复] 图书状态已更新")
        else:
            print(f"  [正常] 图书状态一致")

        print()

    print(f"\n=== 修复结果 ===")
    print(f"总图书数: {books.count()}")
    print(f"修复数量: {fixed_count}")

    # 验证修复结果
    print(f"\n=== 验证修复结果 ===")
    remaining_issues = 0

    for book in books:
        active_records = BorrowRecord.objects.filter(
            book=book,
            status='borrowed'
        ).count()

        expected_available = book.total_copies - active_records

        if book.available_copies != expected_available:
            print(f"仍有问题: {book.title}")
            remaining_issues += 1
        elif (expected_available > 0 and book.status != 'available') or \
             (expected_available == 0 and book.status != 'borrowed'):
            print(f"状态仍有问题: {book.title}")
            remaining_issues += 1

    if remaining_issues == 0:
        print("所有图书状态已修复并保持一致!")
    else:
        print(f"仍有 {remaining_issues} 个图书存在状态问题")

def show_book_status_summary():
    """显示图书状态摘要"""
    print("\n=== 图书状态摘要 ===")

    books = Book.objects.all()
    status_summary = {}

    for book in books:
        status = book.status
        if status not in status_summary:
            status_summary[status] = 0
        status_summary[status] += 1

    print("按状态统计:")
    for status, count in status_summary.items():
        print(f"  {status}: {count}")

    print(f"\n总数: {books.count()}")

if __name__ == "__main__":
    with transaction.atomic():
        fix_book_status_consistency()
        show_book_status_summary()