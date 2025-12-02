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
from django.utils import timezone

User = get_user_model()

def test_admin_borrowing():
    """测试管理员用户的借阅功能"""
    print("=== 测试管理员用户借阅功能 ===")

    # 获取管理员用户
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("没有找到管理员用户")
        return

    print(f"管理员用户: {admin_user.username}")
    print(f"角色: {admin_user.role}")
    print(f"is_admin: {admin_user.is_admin}")
    print(f"is_staff: {admin_user.is_staff}")
    print(f"is_superuser: {admin_user.is_superuser}")

    # 获取一本可借的图书
    test_book = Book.objects.filter(available_copies__gt=0).exclude(title='测试图书').first()
    if not test_book:
        print("没有找到可借阅的图书")
        return

    print(f"\n测试图书: {test_book.title}")
    print(f"借阅前状态:")
    print(f"  总册数: {test_book.total_copies}")
    print(f"  可借册数: {test_book.available_copies}")
    print(f"  状态: {test_book.status}")
    print(f"  是否可借阅: {test_book.is_available}")

    # 检查是否已经借阅过这本书
    existing_record = BorrowRecord.objects.filter(
        user=admin_user,
        book=test_book,
        status='borrowed'
    ).first()

    if existing_record:
        print(f"\n管理员已经借阅过这本书:")
        print(f"  借阅时间: {existing_record.borrow_date}")
        print(f"  应还时间: {existing_record.due_date}")
        print(f"  状态: {existing_record.status}")

        # 先归还这本书
        print(f"\n先归还这本书...")
        if existing_record.return_book():
            print(f"  归还成功")
            test_book.refresh_from_db()
            print(f"  图书可借册数: {test_book.available_copies}")
        else:
            print(f"  归还失败")
            return

    # 创建Django测试客户端
    client = Client()
    client.force_login(admin_user)

    # 测试访问图书详情页面
    print(f"\n=== 测试访问图书详情页面 ===")
    response = client.get(f'/books/book/{test_book.id}/')

    if response.status_code == 200:
        print(f"[OK] 成功访问图书详情页面，状态码: {response.status_code}")
        content = response.content.decode('utf-8')

        # 检查页面内容
        if test_book.title in content:
            print(f"[OK] 页面包含图书标题")
        else:
            print(f"[ERROR] 页面不包含图书标题")

        if '借阅本书' in content:
            print(f"[OK] 页面包含借阅按钮")
        else:
            print(f"[ERROR] 页面不包含借阅按钮")

        if f"{test_book.available_copies}" in content:
            print(f"[OK] 页面显示正确的可借册数")
        else:
            print(f"[ERROR] 页面不显示正确的可借册数")

        # 检查按钮的href属性
        import re
        borrow_links = re.findall(r'href="[^"]*borrow[^"]*"', content)
        if borrow_links:
            print(f"[OK] 找到借阅链接: {borrow_links[0]}")
        else:
            print(f"[ERROR] 没有找到借阅链接")
    else:
        print(f"[ERROR] 访问图书详情页面失败，状态码: {response.status_code}")

    # 测试借阅操作
    print(f"\n=== 测试借阅操作 ===")
    borrow_url = f'/borrowing/borrow/{test_book.id}/'
    print(f"借阅URL: {borrow_url}")

    response = client.post(borrow_url)
    print(f"借阅请求状态码: {response.status_code}")

    if response.status_code == 302:  # 重定向表示成功
        print(f"[OK] 借阅请求成功（重定向）")

        # 获取重定向的目标URL
        if response.has_header('Location'):
            redirect_url = response['Location']
            print(f"重定向到: {redirect_url}")

        # 检查数据库状态
        test_book.refresh_from_db()
        borrow_record = BorrowRecord.objects.filter(
            user=admin_user,
            book=test_book,
            status='borrowed'
        ).first()

        if borrow_record:
            print(f"[OK] 借阅记录创建成功")
            print(f"  记录ID: {borrow_record.id}")
            print(f"  借阅时间: {borrow_record.borrow_date}")
            print(f"  应还时间: {borrow_record.due_date}")

            print(f"\n借阅后图书状态:")
            print(f"  总册数: {test_book.total_copies}")
            print(f"  可借册数: {test_book.available_copies}")
            print(f"  状态: {test_book.status}")

            if test_book.available_copies < test_book.total_copies:
                print(f"[OK] 图书状态正确更新")
            else:
                print(f"[ERROR] 图书状态未正确更新")
        else:
            print(f"[ERROR] 没有找到借阅记录")

    elif response.status_code == 200:
        print(f"[ERROR] 借阅请求没有重定向，可能显示了错误页面")
        content = response.content.decode('utf-8')
        print("页面内容:")
        print(content[:500] + "..." if len(content) > 500 else content)

        # 检查是否有错误消息
        if '错误' in content or 'error' in content.lower():
            print("[ERROR] 页面包含错误信息")

    else:
        print(f"[ERROR] 借阅请求失败，状态码: {response.status_code}")

        # 检查响应内容
        try:
            content = response.content.decode('utf-8')
            print("响应内容:")
            print(content[:500] + "..." if len(content) > 500 else content)
        except:
            print("无法解码响应内容")

    # 检查可能的权限问题
    print(f"\n=== 检查可能的权限问题 ===")
    print(f"管理员用户权限:")
    print(f"  is_authenticated: {admin_user.is_authenticated}")
    print(f"  is_active: {admin_user.is_active}")
    print(f"  is_admin: {admin_user.is_admin}")
    print(f"  is_staff: {admin_user.is_staff}")
    print(f"  is_superuser: {admin_user.is_superuser}")

    # 清理测试数据
    print(f"\n=== 清理测试数据 ===")
    BorrowRecord.objects.filter(user=admin_user, book=test_book, status='borrowed').delete()
    test_book.available_copies = test_book.total_copies
    test_book.status = 'available'
    test_book.save()
    print("测试数据已清理")

if __name__ == "__main__":
    test_admin_borrowing()