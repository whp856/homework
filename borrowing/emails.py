from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.core.mail import get_connection
from django.conf import settings
import time
import logging
from .models import BorrowRecord

logger = logging.getLogger(__name__)

def send_borrow_confirmation_email(borrow_record, retry_count=3):
    """发送借阅确认邮件，支持重试机制"""
    if not borrow_record.user.email:
        logger.warning(f"用户{borrow_record.user.username}没有邮箱地址，跳过借阅确认邮件")
        return False

    subject = f'图书借阅确认 - 《{borrow_record.book.title}》'
    context = {
        'user': borrow_record.user,
        'book': borrow_record.book,
        'borrow_date': borrow_record.borrow_date.strftime('%Y-%m-%d'),
        'due_date': borrow_record.due_date.strftime('%Y-%m-%d'),
    }
    html_message = render_to_string('emails/borrow_confirmation.html', context)
    plain_message = strip_tags(html_message)

    for attempt in range(retry_count):
        try:
            # 使用连接池发送邮件
            with get_connection(fail_silently=False) as connection:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [borrow_record.user.email],
                    html_message=html_message,
                    connection=connection
                )

            logger.info(f"借阅确认邮件发送成功: {borrow_record.user.email}")
            return True

        except Exception as e:
            logger.warning(f"借阅确认邮件发送失败 (尝试{attempt+1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(2 * (attempt + 1))  # 指数退避

    logger.error(f"借阅确认邮件发送最终失败: {borrow_record.user.email}")
    return False


def send_return_confirmation_email(borrow_record, retry_count=3):
    """发送归还确认邮件，支持重试机制"""
    if not borrow_record.user.email:
        logger.warning(f"用户{borrow_record.user.username}没有邮箱地址，跳过归还确认邮件")
        return False

    subject = f'图书归还确认 - 《{borrow_record.book.title}》'
    # 获取归还日期，处理可能为None的情况
    return_date_str = borrow_record.return_date.strftime('%Y-%m-%d') if borrow_record.return_date else timezone.now().strftime('%Y-%m-%d')
    context = {
        'user': borrow_record.user,
        'book': borrow_record.book,
        'borrow_date': borrow_record.borrow_date.strftime('%Y-%m-%d'),
        'return_date': return_date_str,
    }
    html_message = render_to_string('emails/return_confirmation.html', context)
    plain_message = strip_tags(html_message)

    for attempt in range(retry_count):
        try:
            # 使用连接池发送邮件
            with get_connection(fail_silently=False) as connection:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [borrow_record.user.email],
                    html_message=html_message,
                    connection=connection
                )

            logger.info(f"归还确认邮件发送成功: {borrow_record.user.email}")
            return True

        except Exception as e:
            logger.warning(f"归还确认邮件发送失败 (尝试{attempt+1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(2 * (attempt + 1))

    logger.error(f"归还确认邮件发送最终失败: {borrow_record.user.email}")
    return False


def send_overdue_reminder_email(borrow_record):
    """发送逾期提醒邮件"""
    days_overdue = borrow_record.days_overdue
    subject = f'【逾期提醒】图书《{borrow_record.book.title}》已逾期{days_overdue}天'
    context = {
        'user': borrow_record.user,
        'book': borrow_record.book,
        'due_date': borrow_record.due_date.strftime('%Y-%m-%d'),
        'days_overdue': days_overdue,
    }
    html_message = render_to_string('emails/overdue_reminder.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        None,
        [borrow_record.user.email],
        html_message=html_message
    )


def send_due_soon_reminder_email(borrow_record, days_left=3):
    """发送即将到期提醒邮件"""
    subject = f'【即将到期】图书《{borrow_record.book.title}》还有{days_left}天到期'
    context = {
        'user': borrow_record.user,
        'book': borrow_record.book,
        'due_date': borrow_record.due_date.strftime('%Y-%m-%d'),
        'days_left': days_left,
    }
    html_message = render_to_string('emails/due_soon_reminder.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        None,
        [borrow_record.user.email],
        html_message=html_message
    )


def check_and_send_reminders():
    """检查并发送各类提醒邮件"""
    today = timezone.now().date()
    tomorrow = today + timezone.timedelta(days=1)
    three_days_later = today + timezone.timedelta(days=3)
    
    # 获取所有借阅中且未过期的记录
    active_records = BorrowRecord.objects.filter(status='borrowed')
    
    for record in active_records:
        due_date = record.due_date.date()
        
        # 检查是否已逾期
        if record.is_overdue:
            # 只在首次逾期或逾期天数是3的倍数时发送提醒
            if record.days_overdue == 1 or record.days_overdue % 3 == 0:
                send_overdue_reminder_email(record)
        else:
            # 检查是否即将到期（今天、明天或3天后到期）
            if due_date == today or due_date == tomorrow or due_date == three_days_later:
                days_left = (due_date - today).days
                send_due_soon_reminder_email(record, days_left)