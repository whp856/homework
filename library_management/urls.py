from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from books import views as books_views  # 添加这行导入
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def welcome(request):
    """公开的欢迎页面，展示系统介绍"""
    return render(request, 'welcome.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('books/', include('books.urls')),
    path('categories/', include('categories.urls')),
    path('borrowing/', include('borrowing.urls')),
    path('reviews/', include('reviews.urls')),
    path('', welcome, name='welcome'),  # 新的欢迎页面
    path('home/', login_required(books_views.home), name='home'),  # 需要登录的主页
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)