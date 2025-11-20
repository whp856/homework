from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test
from accounts.models import CustomUser
from books.models import Book  # 将Book模型导入移到开头
from .models import BorrowRecord
from .forms import BorrowRecordForm

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
def my_borrow_records(request):
    records = BorrowRecord.objects.filter(user=request.user).order_by('-borrow_date')
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'borrowing/my_records.html', {'page_obj': page_obj})

@user_passes_test(is_admin)
def borrow_record_list(request):
    records = BorrowRecord.objects.all().order_by('-borrow_date')
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'borrowing/record_list.html', {'page_obj': page_obj})

@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not book.can_borrow():
        messages.error(request, '该图书当前不可借阅。')
        return redirect('books:book_detail', book_id=book.id)

    existing_record = BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        status='borrowed'
    ).first()

    if existing_record:
        messages.error(request, '您已经借阅了这本书。')
        return redirect('books:book_detail', book_id=book.id)

    borrow_record = BorrowRecord.objects.create(
        user=request.user,
        book=book,
        due_date=timezone.now() + timedelta(days=30)
    )

    book.borrow_book()
    messages.success(request, f'成功借阅《{book.title}》，请于{borrow_record.due_date.strftime("%Y-%m-%d")}前归还。')
    return redirect('borrowing:my_records')

@login_required
def return_book(request, record_id):
    record = get_object_or_404(BorrowRecord, id=record_id)

    if record.user != request.user and not request.user.is_admin:
        messages.error(request, '您没有权限归还这本书。')
        return redirect('borrowing:my_records')

    if record.return_book():
        messages.success(request, f'《{record.book.title}》归还成功。')
    else:
        messages.error(request, '归还失败，请检查图书状态。')

    if request.user.is_admin:
        return redirect('borrowing:record_list')
    else:
        return redirect('borrowing:my_records')

@user_passes_test(is_admin)
def create_borrow_record(request):
    if request.method == 'POST':
        form = BorrowRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            if record.book.can_borrow():
                record.save()
                record.book.borrow_book()
                messages.success(request, '借阅记录创建成功！')
                return redirect('borrowing:record_list')
            else:
                messages.error(request, '该图书当前不可借阅。')
    else:
        form = BorrowRecordForm()
    return render(request, 'borrowing/record_form.html', {
        'form': form,
        'title': '创建借阅记录'
    })

@user_passes_test(is_admin)
def update_borrow_record(request, record_id):
    record = get_object_or_404(BorrowRecord, id=record_id)
    if request.method == 'POST':
        form = BorrowRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, '借阅记录更新成功！')
            return redirect('borrowing:record_list')
    else:
        form = BorrowRecordForm(instance=record)
    return render(request, 'borrowing/record_form.html', {
        'form': form,
        'title': '编辑借阅记录',
        'record': record
    })

@user_passes_test(is_admin)
def delete_borrow_record(request, record_id):
    record = get_object_or_404(BorrowRecord, id=record_id)
    if request.method == 'POST':
        record.delete()
        messages.success(request, '借阅记录删除成功！')
        return redirect('borrowing:record_list')
    return render(request, 'borrowing/record_delete.html', {'record': record})