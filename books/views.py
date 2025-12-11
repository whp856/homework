from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import pandas as pd
from datetime import datetime
import logging
from accounts.models import CustomUser
from .models import Book
from .forms import BookForm
from library_management.cache import (
    cache, CACHE_KEY_HOME_STATS, CACHE_KEY_CATEGORIES, CACHE_KEY_PAGINATED_BOOKS,
    CACHE_KEY_BOOK_LIST, CACHE_KEY_POPULAR_BOOKS, CACHE_KEY_RECENT_BOOKS,
    CACHE_KEY_BOOK_DETAIL, CACHE_KEY_SEARCH_RESULTS, cache_query, get_cache_key_with_params,
    invalidate_book_cache
)
from library_management.pagination import get_paginated_books, get_pagination_context, PaginationCacheManager
from library_management.excel_export import ExcelExporter, ExcelImporter

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_admin

def check_admin_permission(request, error_message="您没有权限执行此操作，只有管理员可以操作。"):
    """检查管理员权限的工具函数"""
    if not request.user.is_admin:
        messages.error(request, error_message)
        return False
    return True

@cache_query(timeout=600, namespace='books')
def get_popular_books():
    """获取热门图书（按借阅次数排序）"""
    from borrowing.models import BorrowRecord
    from django.db.models import Count

    # 统计每本书的借阅次数
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowrecord')
    ).filter(borrow_count__gt=0).order_by('-borrow_count')[:8]

    return list(popular_books)

@cache_query(timeout=600, namespace='books')
def get_recent_books():
    """获取最新添加的图书"""
    return list(Book.objects.all().order_by('-created_at')[:8])

@cache_query(timeout=600, namespace='books')
def get_home_stats():
    """获取首页统计数据"""
    return {
        'book_count': Book.objects.count(),
        'available_count': Book.objects.filter(available_copies__gt=0).count(),
        'categories': list(Book.objects.values('category__name', 'category__id').filter(category__isnull=False).distinct()),
    }

def home(request):
    """首页视图，使用缓存优化"""
    # 并行获取缓存数据
    recent_books = cache.get_or_set(CACHE_KEY_RECENT_BOOKS, get_recent_books, timeout=600, namespace='books')
    popular_books = cache.get_or_set(CACHE_KEY_POPULAR_BOOKS, get_popular_books, timeout=600, namespace='books')
    stats = cache.get_or_set(CACHE_KEY_HOME_STATS, get_home_stats, timeout=600, namespace='books')

    home_data = {
        'recent_books': recent_books,
        'popular_books': popular_books,
        **stats
    }

    return render(request, 'books/home.html', home_data)

@cache_query(timeout=300, namespace='books')
def get_books_with_filters(query='', category_id=''):
    """获取带筛选条件的图书列表（缓存版本）"""
    books = Book.objects.select_related('category').all().order_by('title')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    return list(books)

@login_required
def book_list(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 12))

    # 验证页码
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
    except (ValueError, TypeError):
        page_number = 1

    # 验证每页数量
    allowed_per_page = [12, 24, 48, 96]
    if per_page not in allowed_per_page:
        per_page = 12

    # 获取缓存的分类列表
    categories_cache_key = 'category_list'
    categories = cache.get(categories_cache_key, namespace='books')
    if categories is None:
        categories = list(Book.objects.values('category__name', 'category__id')
                          .filter(category__isnull=False)
                          .distinct())
        cache.set(categories_cache_key, categories, timeout=1800, namespace='books')  # 30分钟缓存

    # 使用优化的分页获取数据
    try:
        pagination_data = get_paginated_books(
            query=query,
            category_id=category_id,
            page=page_number,
            per_page=per_page
        )

        # 生成分页上下文
        pagination_context = get_pagination_context(
            pagination_data,
            request_path=request.path
        )

        # 添加查询参数
        context = {
            **pagination_context,
            'query': query,
            'selected_category': category_id,
            'categories': categories,
            'per_page': per_page,
            'per_page_options': allowed_per_page,
            'current_search_params': f"q={query}&category={category_id}&per_page={per_page}",
        }

        return render(request, 'books/book_list.html', context)

    except Exception as e:
        logger.error(f"获取图书列表时出错: {str(e)}", exc_info=True)
        messages.error(request, f"获取图书列表失败: {str(e)}")

        # 降级到简单查询
        books = Book.objects.all().order_by('title')[:12]
        return render(request, 'books/book_list.html', {
            'object_list': books,
            'query': query,
            'selected_category': category_id,
            'categories': categories,
            'is_paginated': False,
            'error_message': "分页功能暂时不可用，显示前12条记录"
        })

@cache_query(timeout=600, namespace='books')
def get_book_detail_data(book_id, user_id=None):
    """获取图书详情数据的缓存函数"""
    book = Book.objects.select_related('category').get(id=book_id)
    user_borrow_records = None

    if user_id:
        from borrowing.models import BorrowRecord
        user_borrow_records = list(BorrowRecord.objects.filter(
            user_id=user_id,
            book=book
        ).order_by('-borrow_date')[:5].values(
            'id', 'borrow_date', 'due_date', 'return_date', 'status'
        ))

    return {
        'book': book,
        'user_borrow_records': user_borrow_records
    }

@login_required
def book_detail(request, book_id):
    """图书详情视图，使用缓存优化"""
    cache_key = get_cache_key_with_params(CACHE_KEY_BOOK_DETAIL, book_id=book_id)

    # 生成缓存键的函数
    def key_func():
        user_id = request.user.id if request.user.is_authenticated else None
        return get_cache_key_with_params(CACHE_KEY_BOOK_DETAIL, book_id=book_id, user_id=user_id)

    # 获取缓存数据或执行查询
    data = cache.get(key_func())
    if data is None:
        user_id = request.user.id if request.user.is_authenticated else None
        data = get_book_detail_data(book_id, user_id)
        cache.set(key_func(), data, timeout=600)  # 10分钟缓存

    return render(request, 'books/book_detail.html', data)

@login_required
def book_create(request):
    # 检查管理员权限
    if not check_admin_permission(request, '您没有权限添加图书，只有管理员可以执行此操作。'):
        return redirect('books:book_list')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '图书添加成功！')
            return redirect('books:book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {
        'form': form,
        'title': '添加图书'
    })

@login_required
def book_update(request, book_id):
    # 检查管理员权限
    if not check_admin_permission(request, '您没有权限编辑图书，只有管理员可以执行此操作。'):
        return redirect('books:book_detail', book_id=book_id)

    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            try:
                updated_book = form.save()
                messages.success(request, '图书更新成功！')
                return redirect('books:book_detail', book_id=updated_book.id)
            except Exception as e:
                messages.error(request, f'保存失败: {e}')
        else:
            # 显示表单验证错误
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = BookForm(instance=book)

    return render(request, 'books/book_form.html', {
        'form': form,
        'title': '编辑图书',
        'book': book
    })

@login_required
def book_delete(request, book_id):
    # 检查管理员权限
    if not check_admin_permission(request, '您没有权限删除图书，只有管理员可以执行此操作。'):
        return redirect('books:book_detail', book_id=book_id)

    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, '图书删除成功！')
        return redirect('books:book_list')
    return render(request, 'books/book_delete.html', {'book': book})


@login_required
@user_passes_test(is_admin)
def export_books(request):
    """导出图书数据为Excel文件"""
    try:
        # 获取所有图书数据
        books = Book.objects.all()

        # 准备导出数据
        data = []
        for book in books:
            try:
                data.append({
                    '书名': book.title or '',
                    '作者': book.author or '',
                    'ISBN': book.isbn or '',
                    '出版社': book.publisher or '',
                    '出版日期': book.publication_date.strftime('%Y-%m-%d') if book.publication_date else '',
                    '分类': book.category.name if book.category else '',
                    '总册数': book.total_copies or 0,
                    '可借册数': book.available_copies or 0,
                    '书架位置': book.location or '',
                    '状态': dict(Book.STATUS_CHOICES).get(book.status, book.status),
                    '创建时间': book.created_at.strftime('%Y-%m-%d %H:%M:%S') if book.created_at else '',
                    '更新时间': book.updated_at.strftime('%Y-%m-%d %H:%M:%S') if book.updated_at else ''
                })
            except Exception as e:
                logger.error(f"处理图书 {book.title} 时出错: {str(e)}")
                continue

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 创建HTTP响应
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'图书数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # 导出到Excel
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='图书数据')

        return response

    except Exception as e:
        logger.error(f"导出图书数据时出错: {str(e)}", exc_info=True)
        messages.error(request, f'导出失败: {str(e)}')
        return redirect('books:book_list')

@user_passes_test(is_admin)
def export_statistics(request):
    """导出图书馆统计数据"""
    try:
        from categories.models import Category
        from accounts.models import CustomUser

        # 准备统计数据
        stats_data = {
            'total_books': Book.objects.count(),
            'available_books': Book.objects.filter(available_copies__gt=0).count(),
            'borrowed_books': Book.objects.filter(available_copies=0, status='borrowed').count(),
            'total_users': CustomUser.objects.count(),
            'active_users': CustomUser.objects.filter(is_active=True).count(),
        }

        # 分类统计
        category_stats = {}
        categories = Category.objects.all()
        for category in categories:
            category_books = Book.objects.filter(category=category)
            category_stats[category.name] = {
                'book_count': category_books.count(),
                'available_count': category_books.filter(available_copies__gt=0).count(),
                'borrowed_count': category_books.filter(available_copies=0, status='borrowed').count()
            }
        stats_data['category_stats'] = category_stats

        # 使用通用导出工具
        response = ExcelExporter.export_statistics(stats_data)
        messages.success(request, '统计数据导出成功！')
        return response

    except Exception as e:
        logger.error(f"导出统计数据时出错: {str(e)}", exc_info=True)
        messages.error(request, f'导出失败: {str(e)}')
        return redirect('books:book_list')


@login_required
@user_passes_test(is_admin)
def import_books(request):
    """图书导入页面视图"""
    return render(request, 'books/import_books.html')


@login_required
@user_passes_test(is_admin)
def import_books_excel(request):
    """处理Excel文件导入"""
    try:
        if 'excel_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '请选择要导入的Excel文件'
            })

        excel_file = request.FILES['excel_file']

        # 验证文件类型
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'message': '请上传Excel文件（.xlsx或.xls格式）'
            })

        # 验证文件大小（限制10MB）
        if excel_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'message': '文件大小不能超过10MB'
            })

        # 使用导入工具处理文件
        result = ExcelImporter.import_books_from_excel(excel_file)

        if result['success']:
            # 清除相关缓存
            invalidate_book_cache()

            # 记录操作日志
            logger.info(f"管理员 {request.user.username} 成功导入 {result['imported_count']} 本图书")

            return JsonResponse(result)
        else:
            return JsonResponse(result)

    except Exception as e:
        logger.error(f"导入图书时出错: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'导入失败: {str(e)}',
            'imported_count': 0,
            'errors': [f'系统错误: {str(e)}']
        })


@login_required
@user_passes_test(is_admin)
def download_import_template(request):
    """下载图书导入模板"""
    try:
        return ExcelImporter.get_import_template()
    except Exception as e:
        logger.error(f"下载导入模板时出错: {str(e)}", exc_info=True)
        messages.error(request, f'下载模板失败: {str(e)}')
        return redirect('books:import_books')