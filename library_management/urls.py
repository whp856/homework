from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from books import views as books_views  # 添加这行导入

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('books/', include('books.urls')),
    path('categories/', include('categories.urls')),
    path('borrowing/', include('borrowing.urls')),
    path('reviews/', include('reviews.urls')),
    path('', books_views.home, name='home'),  # 修改这行为使用导入的视图
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)