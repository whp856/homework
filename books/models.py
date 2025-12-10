from django.db import models, transaction
from django.db.models import F
from categories.models import Category
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from library_management.cache import (
    cache, CACHE_KEY_HOME_STATS, CACHE_KEY_CATEGORIES, CACHE_KEY_BOOK_LIST,
    CACHE_KEY_POPULAR_BOOKS, CACHE_KEY_RECENT_BOOKS, CACHE_KEY_SEARCH_RESULTS,
    invalidate_book_cache
)
from django.templatetags.static import static
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
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True, verbose_name='分类')
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

    # 在文件顶部添加导入
    
    
    # 然后在cover_image_url方法中使用
    @property
    def cover_image_url(self):
        """返回图书封面图片URL，如果没有则返回默认图片"""
        if self.cover_image and hasattr(self.cover_image, 'url'):
            try:
                # 尝试检查文件是否存在
                import os
                from django.conf import settings
                image_path = os.path.join(settings.MEDIA_ROOT, self.cover_image.name)
                if os.path.exists(image_path):
                    return self.cover_image.url
            except:
                # 如果检查失败，默认使用默认图片
                pass
        # 返回默认图片URL
        return static('images/default-book-cover.png')
    
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
    
            # 更新状态 - 修改部分
            updated_book = Book.objects.get(id=self.id)
            # 当没有可借册数时，更新为已借出状态
            if updated_book.available_copies == 0:
                updated_book.status = 'borrowed'
                updated_book.save()
            # 当还有可借册数但不是全部可借时，也应该反映出部分借出状态
            # 注意：这里保持status为'available'，因为还有可借册数
            # 但在前端显示时，应该根据available_copies和total_copies来显示实际可借状态
    
            # 清除缓存
            cache.delete(CACHE_KEY_HOME_STATS)
            cache.delete(CACHE_KEY_BOOK_LIST)
            
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
            
            # 清除缓存
            cache.delete(CACHE_KEY_HOME_STATS)
            cache.delete(CACHE_KEY_BOOK_LIST)
            
            return True
        except Exception:
            return False

# 图书保存后清除相关缓存
@receiver(post_save, sender=Book)
def clear_book_cache_on_save(sender, instance, **kwargs):
    """图书保存后清除相关缓存"""
    try:
        # 使用新的缓存失效函数
        invalidate_book_cache(instance.id)

        # 清除特定的缓存键
        cache.delete(CACHE_KEY_HOME_STATS, namespace='books')
        cache.delete(CACHE_KEY_CATEGORIES, namespace='books')
        cache.delete(CACHE_KEY_BOOK_LIST, namespace='books')
        cache.delete(CACHE_KEY_POPULAR_BOOKS, namespace='books')
        cache.delete(CACHE_KEY_RECENT_BOOKS, namespace='books')

        # 清除所有搜索结果缓存
        cache.clear(namespace='books:search')

    except Exception:
        pass  # 如果缓存删除失败，忽略

# 图书删除后清除相关缓存
@receiver(post_delete, sender=Book)
def clear_book_cache_on_delete(sender, instance, **kwargs):
    """图书删除后清除相关缓存"""
    try:
        # 使用新的缓存失效函数
        invalidate_book_cache(instance.id)

        # 清除特定的缓存键
        cache.delete(CACHE_KEY_HOME_STATS, namespace='books')
        cache.delete(CACHE_KEY_CATEGORIES, namespace='books')
        cache.delete(CACHE_KEY_BOOK_LIST, namespace='books')
        cache.delete(CACHE_KEY_POPULAR_BOOKS, namespace='books')
        cache.delete(CACHE_KEY_RECENT_BOOKS, namespace='books')

        # 清除所有搜索结果缓存
        cache.clear(namespace='books:search')

    except Exception:
        pass  # 如果缓存删除失败，忽略