#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分页性能测试脚本
"""
import os
import sys
import django
import time
from django.test import Client
from django.db import connection

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from books.models import Book
from library_management.pagination import get_paginated_books, OptimizedPaginator, SmartPagination
from django.core.paginator import Paginator


def test_pagination_performance():
    """测试分页性能"""
    print("=== 分页性能测试 ===")

    # 获取所有图书数量
    total_books = Book.objects.count()
    print(f"\n总图书数量: {total_books}")

    # 测试不同的分页策略
    per_page = 12
    # 确保测试页数不超过最大页数
    max_page = max(1, (total_books + per_page - 1) // per_page)
    test_page = min(2, max_page)  # 测试第2页或最后一页

    print("\n1. 测试传统Django分页...")
    start_time = time.time()

    # 传统分页方式
    queryset = Book.objects.all().order_by('id')
    django_paginator = Paginator(queryset, per_page)
    django_page = django_paginator.page(test_page)
    django_items = list(django_page.object_list)

    django_time = time.time() - start_time
    print(f"   Django分页耗时: {django_time:.4f}秒")
    print(f"   返回项目数: {len(django_items)}")

    print("\n2. 测试优化分页器...")
    start_time = time.time()

    # 优化分页方式
    query = ''
    category_id = ''
    optimized_data = get_paginated_books(
        query=query,
        category_id=category_id,
        page=test_page,
        per_page=per_page
    )

    optimized_time = time.time() - start_time
    print(f"   优化分页耗时: {optimized_time:.4f}秒")
    print(f"   返回项目数: {len(optimized_data['object_list'])}")
    if django_time > 0:
        print(f"   性能提升: {((django_time - optimized_time) / django_time * 100):.1f}%")
    else:
        print(f"   性能对比: Django分页非常快，优化分页耗时 {optimized_time:.4f}秒")

    # 测试缓存效果
    print("\n3. 测试缓存效果...")
    start_time = time.time()

    # 第二次调用应该从缓存获取
    cached_data = get_paginated_books(
        query=query,
        category_id=category_id,
        page=test_page,
        per_page=per_page
    )

    cached_time = time.time() - start_time
    print(f"   缓存分页耗时: {cached_time:.4f}秒")
    if django_time > 0:
        print(f"   缓存性能提升: {((django_time - cached_time) / django_time * 100):.1f}%")
    else:
        print(f"   缓存性能: 缓存分页耗时 {cached_time:.4f}秒")

    print("\n4. 测试不同每页数量的性能...")
    for per_page_test in [12, 24, 48, 96]:
        start_time = time.time()

        test_data = get_paginated_books(
            query=query,
            category_id=category_id,
            page=test_page,
            per_page=per_page_test
        )

        test_time = time.time() - start_time
        print(f"   每页 {per_page_test:2d} 项: {test_time:.4f}秒")

    print("\n=== 性能测试完成 ===")


def test_database_queries():
    """测试数据库查询次数"""
    print("\n=== 数据库查询测试 ===")

    # 重置查询计数器
    from django.test.utils import override_settings
    from django.conf import settings
    settings.DEBUG = True

    from django.test import Client
    client = Client()

    # 记录查询前的数量
    initial_queries = len(connection.queries)

    # 模拟访问第1页
    response = client.get('/books/list/?page=1')
    first_page_queries = len(connection.queries) - initial_queries

    # 清空查询日志
    connection.queries_log.clear()

    # 访问第2页（应该使用缓存）
    response = client.get('/books/list/?page=2')
    second_page_queries = len(connection.queries_log)

    print(f"第1页数据库查询次数: {first_page_queries}")
    print(f"第2页数据库查询次数: {second_page_queries}")

    if second_page_queries == 0:
        print("[缓存] 缓存工作正常，第2页使用了缓存")
    else:
        print("[警告] 缓存可能未生效，需要检查缓存配置")


def test_page_range_display():
    """测试页码范围显示"""
    print("\n=== 页码范围显示测试 ===")

    # 测试不同页数的页码范围
    test_cases = [
        (1, 10, "前10页"),
        (5, 10, "中间页"),
        (10, 10, "后10页"),
        (100, 100, "100页")
    ]

    for page, total, description in test_cases:
        from library_management.pagination import OptimizedPaginator

        # 创建模拟数据
        total_pages = total
        current_page = page
        window_size = 5

        # 手动计算页码范围
        if total_pages <= window_size:
            page_range = range(1, total_pages + 1)
        else:
            half_window = window_size // 2
            start_page = max(1, current_page - half_window)
            end_page = min(total_pages, current_page + half_window)

            # 调整范围
            if end_page - start_page < window_size:
                if start_page == 1:
                    end_page = min(total_pages, start_page + window_size - 1)
                else:
                    start_page = max(1, end_page - window_size + 1)

            page_range = range(start_page, end_page + 1)

        print(f"{description}: 页码 {page}/{total} -> 显示 {len(page_range)} 页: {list(page_range)[:10]}...")


if __name__ == "__main__":
    try:
        test_pagination_performance()
        test_database_queries()
        test_page_range_display()
        print("\n[成功] 所有测试完成！")
    except Exception as e:
        print(f"\n[错误] 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()