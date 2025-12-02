#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from books.models import Book
from borrowing.models import BorrowRecord

def final_verification():
    """最终验证图书状态"""
    print("=== 最终验证图书状态 ===")

    # 检查单本测试图书
    single_book = Book.objects.filter(title='单本测试图书').first()
    if single_book:
        borrowed_count = BorrowRecord.objects.filter(book=single_book, status='borrowed').count()

        print(f"\n单本测试图书状态:")
        print(f"  书名: {single_book.title}")
        print(f"  总册数: {single_book.total_copies}")
        print(f"  可借册数: {single_book.available_copies}")
        print(f"  数据库状态: {single_book.status}")
        print(f"  实际借出数: {borrowed_count}")

        list_display = "可借阅" if single_book.available_copies > 0 else "已借出"
        print(f"  列表页面应显示: {list_display}")

        if single_book.available_copies == 0 and single_book.status == 'borrowed':
            print(f"  [OK] 状态正确：应该显示'已借出'")
        else:
            print(f"  [ERROR] 状态异常")

    # 检查所有图书的预期显示
    print(f"\n所有图书列表显示预期:")
    books = Book.objects.all()
    for book in books:
        borrowed_count = BorrowRecord.objects.filter(book=book, status='borrowed').count()
        display_status = "可借阅" if book.available_copies > 0 else "已借出"

        print(f"  {book.title}: {book.available_copies}/{book.total_copies} → {display_status}")

    # 测试建议
    print(f"\n=== 测试建议 ===")
    print("1. 请访问图书列表页面: /books/")
    print("2. 找到'单本测试图书'")
    print("3. 确认它显示'已借出'状态")
    print("4. 如果仍然显示'可借阅'，可能需要:")
    print("   - 刷新浏览器缓存 (Ctrl+F5)")
    print("   - 重启Django服务器")
    print("   - 检查是否有其他缓存机制")

if __name__ == "__main__":
    final_verification()