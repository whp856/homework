#!/usr/bin/env python
"""
修复图书数据不一致问题
同步图书的available_copies与实际借阅数量
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.db import transaction
from books.models import Book
from borrowing.models import BorrowRecord

def fix_data_consistency():
    """修复数据不一致"""
    print("=== 修复数据不一致 ===\n")

    books = Book.objects.all()
    fixed_count = 0
    error_count = 0

    for book in books:
        try:
            # 计算实际活跃借阅数量
            active_borrows = BorrowRecord.objects.filter(
                book=book,
                status='borrowed'
            ).count()

            expected_available = book.total_copies - active_borrows

            print(f"图书: {book.title}")
            print(f"  当前可借: {book.available_copies}")
            print(f"  预期可借: {expected_available}")
            print(f"  活跃借阅: {active_borrows}")

            if book.available_copies != expected_available:
                print(f"  [修复] 数据不一致")

                # 修复图书的可借数量
                book.available_copies = expected_available

                # 更新图书状态
                if expected_available > 0:
                    book.status = 'available'
                    print(f"  状态更新为: available")
                else:
                    book.status = 'borrowed'
                    print(f"  状态更新为: borrowed")

                book.save()
                fixed_count += 1
                print(f"  修复成功!")
            else:
                print(f"  [正常] 数据一致")

            print()

        except Exception as e:
            print(f"  [错误] 修复失败: {str(e)}")
            error_count += 1

    print(f"=== 修复结果 ===")
    print(f"总图书数: {books.count()}")
    print(f"修复数量: {fixed_count}")
    print(f"错误数量: {error_count}")

    # 验证修复结果
    print(f"\n=== 验证修复结果 ===")
    remaining_inconsistencies = 0

    for book in books:
        active_borrows = BorrowRecord.objects.filter(
            book=book,
            status='borrowed'
        ).count()
        expected_available = book.total_copies - active_borrows

        if book.available_copies != expected_available:
            remaining_inconsistencies += 1
            print(f"仍不一致: {book.title} - 实际:{book.available_copies}, 预期:{expected_available}")

    if remaining_inconsistencies == 0:
        print("所有图书数据已修复并保持一致!")
    else:
        print(f"仍有 {remaining_inconsistencies} 个图书存在数据不一致")

def fix_borrow_record_statuses():
    """修复借阅记录状态"""
    print("\n=== 修复借阅记录状态 ===")

    # 检查可能的无效借阅记录
    suspicious_records = BorrowRecord.objects.filter(
        status='borrowed'
    ).select_related('book')

    for record in suspicious_records:
        # 检查对应的图书是否有足够的副本
        if record.book.available_copies < 0:
            print(f"发现可疑记录: {record.user.username} - {record.book.title}")
            print(f"  借阅时间: {record.borrow_date}")
            print(f"  图书可借数: {record.book.available_copies}")

            # 标记为异常状态
            record.status = 'overdue'
            record.save()
            print(f"  已标记为异常状态")

def cleanup_orphaned_records():
    """清理孤立的借阅记录"""
    print("\n=== 清理孤立记录 ===")

    # 查找指向不存在图书的借阅记录
    orphaned_records = BorrowRecord.objects.filter(book__isnull=True)
    orphaned_count = orphaned_records.count()

    if orphaned_count > 0:
        print(f"发现 {orphaned_count} 条孤立借阅记录")
        orphaned_records.delete()
        print("已清理所有孤立记录")
    else:
        print("没有发现孤立借阅记录")

def generate_status_report():
    """生成状态报告"""
    print("\n=== 生成状态报告 ===")

    # 统计信息
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available_copies__gt=0).count()
    borrowed_books = Book.objects.filter(status='borrowed').count()

    total_records = BorrowRecord.objects.count()
    active_records = BorrowRecord.objects.filter(status='borrowed').count()
    returned_records = BorrowRecord.objects.filter(status='returned').count()
    overdue_records = sum(1 for r in BorrowRecord.objects.filter(status='borrowed') if r.is_overdue)

    print("图书统计:")
    print(f"  总图书数: {total_books}")
    print(f"  可借图书数: {available_books}")
    print(f"  借出图书数: {borrowed_books}")

    print("\n借阅记录统计:")
    print(f"  总借阅记录数: {total_records}")
    print(f"  活跃借阅数: {active_records}")
    print(f"  已归还记录数: {returned_records}")
    print(f"  逾期记录数: {overdue_records}")

if __name__ == "__main__":
    with transaction.atomic():
        fix_data_consistency()
        fix_borrow_record_statuses()
        cleanup_orphaned_records()
        generate_status_report()