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
import logging
from library_management.cache import (
    cache, CACHE_KEY_HOME_STATS, CACHE_KEY_BORROW_STATS, CACHE_KEY_USER_BORROW_RECORDS,
    cache_query, get_cache_key_with_params, invalidate_user_cache, invalidate_book_cache
)

# 添加邮件相关导入
from .emails import send_borrow_confirmation_email, send_return_confirmation_email

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
def my_borrow_records(request):
    # 首先更新所有用户借阅记录的逾期状态
    BorrowRecord.check_and_update_overdue_status(user=request.user)
    
    records = BorrowRecord.objects.filter(user=request.user).order_by('-borrow_date')
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'borrowing/my_records.html', {'page_obj': page_obj})

@user_passes_test(is_admin)
def borrow_record_list(request):
    # 管理员查看时更新所有记录的逾期状态
    BorrowRecord.check_and_update_overdue_status()
    
    records = BorrowRecord.objects.all().order_by('-borrow_date')
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'borrowing/record_list.html', {'page_obj': page_obj})

@login_required
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
            status__in=['borrowed', 'overdue']
        ).first()

        if existing_record:
            messages.error(request, '您已经借阅了这本书，请勿重复借阅。')
            return redirect('books:book_detail', book_id=book.id)

        # 计算应还时间（管理员可以借阅更长时间）
        if request.user.is_admin:
            due_date = timezone.now() + timedelta(days=60)  # 管理员60天
        else:
            due_date = timezone.now() + timedelta(days=30)  # 普通用户30天

        # 先更新图书状态
        if not book.borrow_book():
            messages.error(request, '借阅失败，图书状态更新失败。')
            logger.error(f"用户{request.user.username}借阅图书{book.title}(ID:{book.id})失败，图书状态更新失败")
            return redirect('books:book_detail', book_id=book.id)

        # 再创建借阅记录
        borrow_record = BorrowRecord.objects.create(
            user=request.user,
            book=book,
            due_date=due_date,
            status='borrowed'
        )

        # 在成功借阅后发送邮件
        if request.user.email:
            try:
                send_borrow_confirmation_email(borrow_record)
            except Exception as e:
                # 邮件发送失败不应影响借阅流程
                logger.error(f"发送借阅确认邮件失败: {str(e)}")
        
        # 记录借阅日志
        if request.user.is_admin:
            messages.success(request, f'管理员借阅《{book.title}》成功，请于{borrow_record.due_date.strftime("%Y-%m-%d")}前归还。')
        else:
            messages.success(request, f'成功借阅《{book.title}》，请于{borrow_record.due_date.strftime("%Y-%m-%d")}前归还。')
        
        logger.info(f"用户{request.user.username}成功借阅图书{book.title}(ID:{book.id})")

        # 在事务内部处理缓存清理
        try:
            cache.delete(CACHE_KEY_HOME_STATS, namespace='books')
            cache.delete(CACHE_KEY_BOOK_LIST, namespace='books')
            cache.delete(CACHE_KEY_CATEGORIES, namespace='books')
            # 清除所有分页缓存
            cache.clear('books')
        except Exception as cache_error:
            logger.warning(f"缓存清理失败: {str(cache_error)}")

        # 检查用户选择的重定向目标
        redirect_to = request.POST.get('redirect_to', 'my_records')
        if redirect_to == 'book_detail':
            return redirect('books:book_detail', book_id=book.id)
        else:
            return redirect('borrowing:my_records')

    except Book.DoesNotExist:
        messages.error(request, '图书不存在。')
        logger.warning(f"用户{request.user.username}尝试借阅不存在的图书(ID:{book_id})")
        return redirect('books:book_list')
    except Exception as e:
        # 更详细的错误处理和日志记录
        error_msg = f'借阅过程中出现错误：{str(e)}'
        messages.error(request, error_msg)
        logger.error(f"用户{request.user.username}借阅图书(ID:{book_id})过程中出错: {str(e)}", exc_info=True)
        return redirect('books:book_detail', book_id=book_id)

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
            logger.warning(f"用户{request.user.username}尝试归还不属于自己的图书记录(ID:{record_id})")
            return redirect('borrowing:my_records')

        # 检查图书状态
        if record.status not in ['borrowed', 'overdue']:
            status_display = record.get_status_display()
            messages.warning(request, f'该借阅记录状态为"{status_display}"，无需归还。')
            logger.info(f"尝试归还非借阅状态的记录: {record_id}, 当前状态: {record.status}")
            if request.user.is_admin:
                return redirect('borrowing:record_list')
            else:
                return redirect('borrowing:my_records')

        # 使用select_for_update锁定图书记录
        book = Book.objects.select_for_update().get(id=record.book.id)

        # 原子性地归还图书
        if record.return_book():
            # 确保return_date已经设置后再发送邮件
            # 重新获取记录以确保所有字段都已更新
            record.refresh_from_db()
            
            # 在成功归还后发送邮件
            if record.user.email:
                try:
                    send_return_confirmation_email(record)
                except Exception as e:
                    # 邮件发送失败不应影响归还流程
                    logger.error(f"发送归还确认邮件失败: {str(e)}")
            
            # 根据用户角色显示不同的成功消息
            if request.user.is_admin:
                if record.user != request.user:
                    messages.success(request, f'已为用户{record.user.username}归还《{record.book.title}》。')
                else:
                    messages.success(request, f'管理员归还《{record.book.title}》成功。')
            else:
                messages.success(request, f'《{record.book.title}》归还成功。')
            
            logger.info(f"用户{request.user.username}成功归还图书{record.book.title}(ID:{record.book.id})，记录ID:{record_id}")
        else:
            messages.error(request, '归还失败，请检查图书状态。')
            logger.error(f"归还图书失败，记录ID:{record_id}")
            if request.user.is_admin:
                return redirect('borrowing:record_list')
            else:
                return redirect('borrowing:my_records')

        # 重定向到相应的页面
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')

    except BorrowRecord.DoesNotExist:
        messages.error(request, '借阅记录不存在。')
        logger.warning(f"用户{request.user.username}尝试归还不存在的借阅记录(ID:{record_id})")
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')
    except Book.DoesNotExist:
        messages.error(request, '图书不存在。')
        logger.error(f"归还过程中发现图书不存在，记录ID:{record_id}")
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')
    except Exception as e:
        # 更详细的错误处理和日志记录
        error_msg = f'归还过程中出现错误：{str(e)}'
        messages.error(request, error_msg)
        logger.error(f"用户{request.user.username}归还图书记录(ID:{record_id})过程中出错: {str(e)}", exc_info=True)
        if request.user.is_admin:
            return redirect('borrowing:record_list')
        else:
            return redirect('borrowing:my_records')

@user_passes_test(is_admin)
@transaction.atomic
def create_borrow_record(request):
    """管理员创建借阅记录，使用事务确保原子性"""
    if request.method == 'POST':
        form = BorrowRecordForm(request.POST)
        if form.is_valid():
            try:
                # 获取表单数据但不保存
                record = form.save(commit=False)
                
                # 锁定图书记录
                book = Book.objects.select_for_update().get(id=record.book.id)
                
                if book.can_borrow():
                    # 先更新图书状态
                    if book.borrow_book():
                        # 再保存借阅记录
                        record.save()
                        messages.success(request, '借阅记录创建成功！')
                        logger.info(f"管理员{request.user.username}成功创建借阅记录，用户:{record.user.username}，图书:{record.book.title}")
                        return redirect('borrowing:record_list')
                    else:
                        messages.error(request, '创建借阅记录失败，图书状态更新失败。')
                        logger.error(f"管理员{request.user.username}创建借阅记录失败，图书状态更新失败")
                else:
                    messages.error(request, '该图书当前不可借阅。')
                    logger.warning(f"管理员{request.user.username}尝试为不可借阅的图书创建记录")
            except Exception as e:
                # 更详细的错误处理和日志记录
                error_msg = f'创建借阅记录过程中出错: {str(e)}'
                messages.error(request, error_msg)
                logger.error(f"管理员{request.user.username}创建借阅记录过程中出错: {str(e)}", exc_info=True)
                # 事务会自动回滚
    else:
        form = BorrowRecordForm()
    return render(request, 'borrowing/record_form.html', {
        'form': form,
        'title': '创建借阅记录'
    })

@user_passes_test(is_admin)
@transaction.atomic
def update_borrow_record(request, record_id):
    """管理员更新借阅记录，添加事务保护"""
    record = get_object_or_404(BorrowRecord, id=record_id)
    if request.method == 'POST':
        try:
            form = BorrowRecordForm(request.POST, instance=record)
            if form.is_valid():
                # 检查是否修改了图书或用户，如果是需要额外验证
                old_book_id = record.book.id
                new_book = form.cleaned_data['book']
                
                if old_book_id != new_book.id:
                    # 如果修改了图书，需要检查新图书是否可借
                    if not new_book.can_borrow():
                        messages.error(request, '更新失败，新选择的图书当前不可借阅。')
                        logger.warning(f"管理员{request.user.username}尝试更新借阅记录到不可借阅的图书")
                        return redirect('borrowing:update_record', record_id=record_id)
                
                form.save()
                messages.success(request, '借阅记录更新成功！')
                logger.info(f"管理员{request.user.username}成功更新借阅记录(ID:{record_id})")
                return redirect('borrowing:record_list')
            else:
                # 显示表单验证错误
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{form.fields[field].label}: {error}')
        except Exception as e:
            # 更详细的错误处理和日志记录
            error_msg = f'更新借阅记录过程中出错: {str(e)}'
            messages.error(request, error_msg)
            logger.error(f"管理员{request.user.username}更新借阅记录(ID:{record_id})过程中出错: {str(e)}", exc_info=True)
            # 事务会自动回滚
    else:
        form = BorrowRecordForm(instance=record)
    return render(request, 'borrowing/record_form.html', {
        'form': form,
        'title': '编辑借阅记录',
        'record': record
    })

@user_passes_test(is_admin)
@transaction.atomic
def delete_borrow_record(request, record_id):
    """管理员删除借阅记录，添加事务保护"""
    record = get_object_or_404(BorrowRecord, id=record_id)
    if request.method == 'POST':
        try:
            # 如果记录状态为借阅中，需要先归还图书
            if record.status in ['borrowed', 'overdue']:
                if not record.return_book():
                    messages.error(request, '删除失败，无法归还关联的图书。')
                    logger.error(f"管理员{request.user.username}删除借阅记录失败，无法归还关联图书")
                    return redirect('borrowing:record_list')
            
            record.delete()
            messages.success(request, '借阅记录删除成功！')
            logger.info(f"管理员{request.user.username}成功删除借阅记录(ID:{record_id})")
            return redirect('borrowing:record_list')
        except Exception as e:
            # 更详细的错误处理和日志记录
            error_msg = f'删除借阅记录过程中出错: {str(e)}'
            messages.error(request, error_msg)
            logger.error(f"管理员{request.user.username}删除借阅记录(ID:{record_id})过程中出错: {str(e)}", exc_info=True)
            # 事务会自动回滚
    return render(request, 'borrowing/record_delete.html', {'record': record})

@login_required
@user_passes_test(is_admin)
def export_borrow_records(request):
    """导出所有借阅记录为Excel文件"""
    try:
        # 导出前更新所有记录的逾期状态
        BorrowRecord.check_and_update_overdue_status()
        
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
        
        logger.info(f"管理员{request.user.username}成功导出所有借阅记录")
        return response
    except Exception as e:
        messages.error(request, f'导出过程中出现错误：{str(e)}')
        logger.error(f"管理员{request.user.username}导出借阅记录失败: {str(e)}", exc_info=True)
        return redirect('borrowing:record_list')

@login_required
def export_my_borrow_records(request):
    """导出个人借阅记录为Excel文件"""
    try:
        # 导出前更新当前用户的记录逾期状态
        BorrowRecord.check_and_update_overdue_status(user=request.user)
        
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
        
        logger.info(f"用户{request.user.username}成功导出个人借阅记录")
        return response
    except Exception as e:
        messages.error(request, f'导出过程中出现错误：{str(e)}')
        logger.error(f"用户{request.user.username}导出个人借阅记录失败: {str(e)}", exc_info=True)
        return redirect('borrowing:my_records')