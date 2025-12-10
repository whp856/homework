from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import pandas as pd
from datetime import datetime
import logging
from accounts.models import CustomUser
from .models import Book
from .forms import BookForm
from library_management.cache import cache, CACHE_KEY_HOME_STATS, CACHE_KEY_CATEGORIES, CACHE_KEY_PAGINATED_BOOKS, CACHE_KEY_BOOK_LIST
from library_management.excel_export import ExcelExporter

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_admin

def check_admin_permission(request, error_message="您没有权限执行此操作，只有管理员可以操作。"):
    """检查管理员权限的工具函数"""
    if not request.user.is_admin:
        messages.error(request, error_message)
        return False
    return True

def home(request):
    # 使用增强的缓存获取首页数据，设置10分钟过期，并使用命名空间
    home_data = cache.get_or_set(
        CACHE_KEY_HOME_STATS,
        lambda: {
            'recent_books': list(Book.objects.all().order_by('-created_at')[:6]),
            'categories': list(Book.objects.values('category__name', 'category__id').filter(category__isnull=False).distinct()),
            'book_count': Book.objects.count(),
            'available_count': Book.objects.filter(available_copies__gt=0).count()
        },
        timeout=600,  # 10分钟
        namespace='books'
    )

    return render(request, 'books/home.html', home_data)

@login_required
def book_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    page_number = request.GET.get('page', 1)

    # 清理可能有问题的缓存
    try:
        cache.clear('books')
    except Exception:
        pass  # 如果缓存清理失败，继续执行

    # 执行数据库查询
    books = Book.objects.all().order_by('title')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    # 分页
    paginator = Paginator(books, 12)
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1

    page_obj = paginator.get_page(page_number)

    # 获取分类列表（不使用缓存）
    categories = list(Book.objects.values('category__name', 'category__id').filter(category__isnull=False).distinct())

    # 渲染模板
    return render(request, 'books/book_list.html', {
        'page_obj': page_obj,
        'query': query,
        'selected_category': category_id,
        'categories': categories
    })

@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user_borrow_records = None

    if request.user.is_authenticated:
        from borrowing.models import BorrowRecord
        user_borrow_records = BorrowRecord.objects.filter(
            user=request.user,
            book=book
        ).order_by('-borrow_date')[:5]

    return render(request, 'books/book_detail.html', {
        'book': book,
        'user_borrow_records': user_borrow_records
    })

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