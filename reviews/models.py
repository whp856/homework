from django.db import models
from django.contrib.auth import get_user_model
from books.models import Book

User = get_user_model()

class Review(models.Model):
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (3, '⭐⭐⭐'),
        (2, '⭐⭐'),
        (1, '⭐'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='评论用户')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='评论图书')
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name='评分')
    comment = models.TextField(verbose_name='评论内容')
    is_approved = models.BooleanField(default=True, verbose_name='是否审核通过')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '书评'
        verbose_name_plural = '书评'
        ordering = ['-created_at']
        unique_together = ['user', 'book']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating}星)"

    @property
    def rating_stars(self):
        return dict(self.RATING_CHOICES).get(self.rating, '')

    def get_rating_display(self):
        return self.rating_stars