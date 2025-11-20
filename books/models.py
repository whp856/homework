from django.db import models
from categories.models import Category

class Book(models.Model):
    STATUS_CHOICES = [
        ('available', '可借阅'),
        ('borrowed', '已借出'),
        ('maintenance', '维护中'),
        ('lost', '丢失'),
    ]

    title = models.CharField(max_length=200, verbose_name='书名')
    author = models.CharField(max_length=100, verbose_name='作者')
    isbn = models.CharField(max_length=20, unique=True, verbose_name='ISBN')
    publisher = models.CharField(max_length=100, blank=True, null=True, verbose_name='出版社')
    publication_date = models.DateField(blank=True, null=True, verbose_name='出版日期')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='分类')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, verbose_name='封面图片')
    total_copies = models.PositiveIntegerField(default=1, verbose_name='总册数')
    available_copies = models.PositiveIntegerField(default=1, verbose_name='可借册数')
    location = models.CharField(max_length=50, blank=True, null=True, verbose_name='书架位置')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '图书'
        verbose_name_plural = '图书'

    def __str__(self):
        return f"{self.title} - {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0 and self.status == 'available'

    @property
    def borrowed_copies(self):
        return self.total_copies - self.available_copies

    def can_borrow(self):
        return self.is_available

    def borrow_book(self):
        if self.can_borrow():
            self.available_copies -= 1
            if self.available_copies == 0:
                self.status = 'borrowed'
            self.save()
            return True
        return False

    def return_book(self):
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            if self.available_copies > 0:
                self.status = 'available'
            self.save()
            return True
        return False