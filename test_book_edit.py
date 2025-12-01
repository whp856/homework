#!/usr/bin/env python
import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from books.models import Book
from books.forms import BookForm
from accounts.models import CustomUser

def test_book_edit():
    """测试图书编辑功能"""
    print("=== 测试图书编辑功能 ===\n")

    # 获取第一个图书
    try:
        book = Book.objects.first()
        print(f"测试图书: {book.title} (ID: {book.id})")
        print(f"当前信息: 作者={book.author}, ISBN={book.isbn}")
        print(f"分类: {book.category}, 总册数={book.total_copies}")
    except Exception as e:
        print(f"获取图书失败: {e}")
        return

    # 检查表单字段
    print("\n=== 表单字段检查 ===")
    form = BookForm(instance=book)
    print(f"表单字段: {list(form.fields.keys())}")

    # 测试表单验证
    test_data = {
        'title': f'{book.title} (已编辑)',
        'author': book.author,
        'isbn': book.isbn,
        'publisher': book.publisher or '',
        'publication_date': book.publication_date,
        'category': book.category.id if book.category else None,
        'description': book.description or '',
        'total_copies': book.total_copies,
        'available_copies': book.available_copies,
        'location': book.location or '',
        'status': book.status
    }

    print(f"\n=== 测试表单数据 ===")
    for key, value in test_data.items():
        print(f"{key}: {value}")

    # 测试表单验证
    try:
        form = BookForm(test_data, instance=book)
        print(f"\n=== 表单验证结果 ===")
        print(f"表单是否有效: {form.is_valid()}")

        if form.is_valid():
            print("表单验证通过！")
            saved_book = form.save(commit=False)
            print(f"保存前的数据: {saved_book.title}")
        else:
            print("表单验证失败:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
    except Exception as e:
        print(f"表单验证错误: {e}")

    # 检查管理员权限
    print(f"\n=== 检查管理员用户 ===")
    try:
        admin_user = CustomUser.objects.get(username='admin')
        print(f"管理员用户: {admin_user.username}, 角色: {admin_user.role}")
        print(f"是否为管理员: {admin_user.is_admin}")
    except Exception as e:
        print(f"获取管理员用户失败: {e}")

if __name__ == '__main__':
    test_book_edit()