from django.db import models, transaction
from django.db.models import F
from django.contrib.auth import get_user_model
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