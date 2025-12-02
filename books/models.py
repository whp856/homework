from django.db import models, transaction
from django.db.models import F
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

    @transaction.atomic
    def borrow_book(self):
        """原子性地借阅图书，防止并发问题"""
        try:
            # 使用select_for_update来锁定记录，防止并发借阅
            book = Book.objects.select_for_update().filter(id=self.id).first()

            if book.available_copies <= 0:
                return False

            # 使用F()原子性更新
            Book.objects.filter(id=self.id).update(
                available_copies=F('available_copies') - 1
            )

            # 更新状态
            updated_book = Book.objects.get(id=self.id)
            if updated_book.available_copies == 0:
                updated_book.status = 'borrowed'
                updated_book.save()

            return True
        except Exception:
            return False

    @transaction.atomic
    def return_book(self):
        """原子性地归还图书，防止并发问题"""
        try:
            # 使用select_for_update来锁定记录，防止并发归还
            book = Book.objects.select_for_update().filter(id=self.id).first()

            if book.available_copies >= book.total_copies:
                return False

            # 使用F()原子性更新
            Book.objects.filter(id=self.id).update(
                available_copies=F('available_copies') + 1
            )

            # 更新状态
            updated_book = Book.objects.get(id=self.id)
            if updated_book.available_copies > 0:
                updated_book.status = 'available'
                updated_book.save()

            return True
        except Exception:
            return False