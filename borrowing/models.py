from django.db import models, transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from books.models import Book
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', '借阅中'),
        ('returned', '已归还'),
        ('overdue', '逾期'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='借阅用户')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='借阅图书')
    borrow_date = models.DateTimeField(auto_now_add=True, verbose_name='借阅时间')
    due_date = models.DateTimeField(verbose_name='应还时间')
    return_date = models.DateTimeField(null=True, blank=True, verbose_name='归还时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed', verbose_name='状态')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '借阅记录'
        verbose_name_plural = '借阅记录'
        ordering = ['-borrow_date']

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.status == 'borrowed' and timezone.now() > self.due_date

    @property
    def days_overdue(self):
        from django.utils import timezone
        if self.is_overdue:
            return (timezone.now() - self.due_date).days
        return 0
    
    @classmethod
    @transaction.atomic
    def check_and_update_overdue_status(cls, user=None):
        """检查并更新逾期的借阅记录，可选择只更新特定用户的记录"""
        from django.utils import timezone
        now = timezone.now()
        
        # 构建查询集
        query = cls.objects.filter(
            status='borrowed',
            due_date__lt=now
        )
        
        # 如果指定了用户，只更新该用户的记录
        if user:
            query = query.filter(user=user)
        
        # 批量更新逾期但状态仍为borrowed的记录
        updated = query.update(status='overdue')
        if updated > 0:
            user_info = f"用户{user.username}的" if user else "所有"
            logger.info(f"更新了{updated}条{user_info}逾期记录的状态")
        return updated

    @transaction.atomic
    def return_book(self):
        """原子性地归还图书，更新借阅记录和图书状态"""
        if self.status not in ['borrowed', 'overdue']:
            logger.warning(f"尝试归还非借阅状态的记录: {self.id}, 当前状态: {self.status}")
            return False

        try:
            from django.utils import timezone

            # 使用select_for_update锁定借阅记录和图书记录
            record = BorrowRecord.objects.select_for_update().get(id=self.id)
            book = Book.objects.select_for_update().get(id=record.book.id)

            # 更新借阅记录状态
            BorrowRecord.objects.filter(id=self.id).update(
                return_date=timezone.now(),
                status='returned'
            )

            # 更新图书状态
            if not book.return_book():
                # 如果图书状态更新失败，回滚借阅记录
                BorrowRecord.objects.filter(id=self.id).update(
                    return_date=None,
                    status='borrowed' if record.status == 'borrowed' else 'overdue'
                )
                logger.error(f"图书归还失败: {record.book.title} (ID: {record.book.id})")
                return False

            logger.info(f"图书归还成功: {record.book.title} (ID: {record.book.id}), 用户: {record.user.username}")
            return True
        except Exception as e:
            logger.error(f"归还图书过程中出错: {str(e)}", exc_info=True)
            return False


class BookReservation(models.Model):
    """图书预约排队模型"""

    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('available', '可借阅'),
        ('cancelled', '已取消'),
        ('completed', '已完成'),
        ('expired', '已过期'),
    ]

    PRIORITY_CHOICES = [
        (1, '普通'),
        (2, '优先'),
        (3, '高优先级'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='用户'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        verbose_name='图书'
    )
    reservation_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='预约时间'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='预约状态'
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=1,
        verbose_name='优先级'
    )
    notification_sent = models.BooleanField(
        default=False,
        verbose_name='是否已发送通知'
    )
    notification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='通知时间'
    )
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='预约过期时间'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        verbose_name = '图书预约'
        verbose_name_plural = '图书预约'
        ordering = ['priority', 'reservation_date']  # 按优先级和预约时间排序
        unique_together = ['user', 'book']  # 同一用户对同一本书只能有一个预约
        indexes = [
            models.Index(fields=['book', 'status', 'priority']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reservation_date']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # 检查用户是否已有该书的预约
        if not self.pk:  # 如果是新预约
            existing_reservation = BookReservation.objects.filter(
                user=self.user,
                book=self.book,
                status='pending'
            ).exists()

            if existing_reservation:
                raise ValidationError('您已经预约了这本图书，请勿重复预约。')

        # 检查图书是否当前可借阅
        if not self.pk and self.book.available_copies > 0:
            raise ValidationError('该图书当前可借阅，请直接借阅，无需预约。')

        # 设置预约过期时间（7天后过期）
        if not self.expiry_date:
            from datetime import timedelta
            self.expiry_date = timezone.now() + timedelta(days=7)

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """检查预约是否过期"""
        if not self.expiry_date:
            return False
        return timezone.now() > self.expiry_date

    @property
    def queue_position(self):
        """获取在预约队列中的位置"""
        if self.status != 'pending':
            return None

        pending_reservations = BookReservation.objects.filter(
            book=self.book,
            status='pending',
            priority__gte=self.priority,
            reservation_date__lte=self.reservation_date
        ).order_by('priority', 'reservation_date')

        return list(pending_reservations).index(self) + 1

    @property
    def days_in_queue(self):
        """计算已在队列中的天数"""
        return (timezone.now() - self.reservation_date).days

    @classmethod
    def get_next_reservation(cls, book):
        """获取指定图书的下一个预约"""
        return cls.objects.filter(
            book=book,
            status='pending'
        ).order_by('priority', 'reservation_date').first()

    @classmethod
    def process_available_book(cls, book):
        """处理图书可用时的预约通知"""
        next_reservation = cls.get_next_reservation(book)
        if next_reservation and not next_reservation.notification_sent:
            # 标记为可借阅
            next_reservation.status = 'available'
            next_reservation.notification_date = timezone.now()
            next_reservation.save()

            # 发送通知邮件
            try:
                from .emails import send_reservation_available_email
                send_reservation_available_email(next_reservation)
                logger.info(f"已发送预约可用通知: {next_reservation.user.email}")
                return True
            except Exception as e:
                logger.error(f"发送预约可用通知失败: {str(e)}", exc_info=True)
                return False
        return False

    @classmethod
    def cancel_expired_reservations(cls):
        """取消过期的预约"""
        expired_reservations = cls.objects.filter(
            status='pending',
            expiry_date__lt=timezone.now()
        )

        count = 0
        for reservation in expired_reservations:
            reservation.status = 'expired'
            reservation.save()
            count += 1
            logger.info(f"预约已过期取消: {reservation}")

        return count

    def cancel_reservation(self):
        """取消预约"""
        self.status = 'cancelled'
        self.save()

        # 尝试通知下一个等待的用户
        BookReservation.process_available_book(self.book)

        return True