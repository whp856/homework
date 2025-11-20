from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from accounts.models import CustomUser
from .models import Book
from .forms import BookForm

def is_admin(user):
    return user.is_authenticated and user.is_admin

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

@user_passes_test(is_admin)
def book_create(request):
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

@user_passes_test(is_admin)
def book_update(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, '图书更新成功！')
            return redirect('books:book_detail', book_id=book.id)
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {
        'form': form,
        'title': '编辑图书',
        'book': book
    })

@user_passes_test(is_admin)
def book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, '图书删除成功！')
        return redirect('books:book_list')
    return render(request, 'books/book_delete.html', {'book': book})