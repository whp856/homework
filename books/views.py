from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.models import CustomUser
from .models import Book
from .forms import BookForm

def is_admin(user):
    return user.is_authenticated and user.is_admin

def check_admin_permission(request, error_message="您没有权限执行此操作，只有管理员可以操作。"):
    """检查管理员权限的工具函数"""
    if not request.user.is_admin:
        messages.error(request, error_message)
        return False
    return True

def home(request):
    recent_books = Book.objects.all().order_by('-created_at')[:6]
    categories = Book.objects.values('category__name', 'category__id').filter(category__isnull=False).distinct()
    book_count = Book.objects.count()
    available_count = Book.objects.filter(available_copies__gt=0).count()

    return render(request, 'books/home.html', {
        'recent_books': recent_books,
        'categories': categories,
        'book_count': book_count,
        'available_count': available_count
    })

@login_required
def book_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    books = Book.objects.all().order_by('title')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Book.objects.values('category__name', 'category__id').filter(category__isnull=False).distinct()

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