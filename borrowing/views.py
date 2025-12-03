from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import F
from accounts.models import CustomUser
from books.models import Book  # 将Book模型导入移到开头
from .models import BorrowRecord
from .forms import BorrowRecordForm
from django.http import HttpResponse
import pandas as pd
from datetime import datetime

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
@transaction.atomic
def borrow_book(request, book_id):
    """处理借阅图书请求，使用事务确保原子性"""
    try:
        # 使用select_for_update锁定图书记录，防止并发借阅
        book = Book.objects.select_for_update().get(id=book_id)

        # 检查图书是否可借阅
        if not book.can_borrow():
            messages.error(request, f'该图书当前不可借阅。剩余可借：{book.available_copies}册')
            return redirect('books:book_detail', book_id=book.id)

        # 检查用户是否已经借阅了这本书（包括管理员）
        existing_record = BorrowRecord.objects.filter(
            user=request.user,
            book=book,
            status='borrowed'
        ).first()

        if existing_record:
            messages.error(request, '您已经借阅了这本书，请勿重复借阅。')
            return redirect('books:book_detail', book_id=book.id)

        # 计算应还时间（管理员可以借阅更长时间）
        if request.user.is_admin:
            due_date = timezone.now() + timedelta(days=60)  # 管理员60天
        else:
            due_date = timezone.now() + timedelta(days=30)  # 普通用户30天

        # 创建借阅记录
        borrow_record = BorrowRecord.objects.create(
            user=request.user,
            book=book,
            due_date=due_date,
            status='borrowed'
        )

        # 原子性地更新图书状态
        if not book.borrow_book():
            # 如果更新失败，删除借阅记录
            borrow_record.delete()
            messages.error(request, '借阅失败，请重试。')
            return redirect('books:book_detail', book_id=book.id)

        # 记录借阅日志（可选）
        if request.user.is_admin:
            messages.success(request, f'管理员借阅《{book.title}》成功，请于{borrow_record.due_date.strftime("%Y-%m-%d")}前归还。')
        else:
            messages.success(request, f'成功借阅《{book.title}》，请于{borrow_record.due_date.strftime("%Y-%m-%d")}前归还。')

        return redirect('borrowing:my_records')

    except Book.DoesNotExist:
        messages.error(request, '图书不存在。')
        return redirect('books:book_list')
    except Exception as e:
        messages.error(request, f'借阅过程中出现错误：{str(e)}')
        return redirect('books:book_detail', book_id=book.id)

@login_required
@transaction.atomic
def return_book(request, record_id):
    """处理归还图书请求，使用事务确保原子性"""
    try:
        # 使用select_for_update锁定借阅记录，防止并发归还
        record = BorrowRecord.objects.select_for_update().get(id=record_id)

        # 权限检查：用户只能归还自己的书，管理员可以归还任何书
        if record.user != request.user and not request.user.is_admin:
            messages.error(request, '您没有权限归还这本书。')
            return redirect('borrowing:my_records')

        # 检查图书状态
        if record.status != 'borrowed':
            messages.warning(request, f'该借阅记录状态为"{record.get_status_display()}"，无需归还。')
            if request.user.is_admin:
                return redirect('borrowing:record_list')
            else:
                return redirect('borrowing:my_records')

        # 使用select_for_update锁定图书记录
        book = Book.objects.select_for_update().get(id=record.book.id)

        # 原子性地归还图书
        if not record.return_book():
            messages.error(request, '归还失败，请检查图书状态。')
            if request.user.is_admin:
                return redirect('borrowing:record_list')
            else:
                return redirect('borrowing:my_records')

        # 根据用户角色显示不同的成功消息
        if request.user.is_admin:
            if record.user != request.user:
                messages.success(request, f'已为用户{record.user.username}归还《{record.book.title}》。')
            else:
                messages.success(request, f'管理员归还《{record.book.title}》成功。')
        else:
            messages.success(request, f'《{record.book.title}》归还成功。')

        # 重定向到相应的页面
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')

    except BorrowRecord.DoesNotExist:
        messages.error(request, '借阅记录不存在。')
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')
    except Book.DoesNotExist:
        messages.error(request, '图书不存在。')
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')
    except Exception as e:
        messages.error(request, f'归还过程中出现错误：{str(e)}')
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


@login_required
@user_passes_test(is_admin)
def export_borrow_records(request):
    """导出所有借阅记录为Excel文件"""
    # 获取所有借阅记录
    records = BorrowRecord.objects.all()
    
    # 准备导出数据
    data = []
    for record in records:
        data.append({
            '用户': record.user.username,
            '图书名称': record.book.title,
            '借阅日期': record.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
            '应还日期': record.due_date.strftime('%Y-%m-%d'),
            '归还日期': record.return_date.strftime('%Y-%m-%d %H:%M:%S') if record.return_date else '',
            '状态': dict(BorrowRecord.STATUS_CHOICES).get(record.status, record.status),
            '备注': record.notes or '',
            '是否逾期': '是' if record.is_overdue else '否',
            '逾期天数': record.days_overdue if record.is_overdue else 0
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建HTTP响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'借阅记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # 导出到Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='借阅记录')
    
    return response

@login_required
def export_my_borrow_records(request):
    """导出个人借阅记录为Excel文件"""
    # 获取当前用户的借阅记录
    records = BorrowRecord.objects.filter(user=request.user)
    
    # 准备导出数据
    data = []
    for record in records:
        data.append({
            '图书名称': record.book.title,
            '作者': record.book.author,
            '借阅日期': record.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
            '应还日期': record.due_date.strftime('%Y-%m-%d'),
            '归还日期': record.return_date.strftime('%Y-%m-%d %H:%M:%S') if record.return_date else '',
            '状态': dict(BorrowRecord.STATUS_CHOICES).get(record.status, record.status),
            '是否逾期': '是' if record.is_overdue else '否',
            '逾期天数': record.days_overdue if record.is_overdue else 0
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建HTTP响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'我的借阅记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # 导出到Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='我的借阅记录')
    
    return response