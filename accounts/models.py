from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('user', '普通用户'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name='角色')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='电话')
    address = models.TextField(blank=True, null=True, verbose_name='地址')
    birth_date = models.DateField(blank=True, null=True, verbose_name='出生日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'