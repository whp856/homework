from django.db import models
from django.contrib.auth import get_user_model
from books.models import Book

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

    def return_book(self):
        if self.status == 'borrowed':
            from django.utils import timezone
            self.return_date = timezone.now()
            self.status = 'returned'
            self.save()
            self.book.return_book()
            return True
        return False