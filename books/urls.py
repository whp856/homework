from django.urls import path
from . import views
from django.contrib.auth.decorators import user_passes_test

app_name = 'books'

urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.book_list, name='book_list'),
    path('<int:book_id>/', views.book_detail, name='book_detail'),
    path('create/', views.book_create, name='book_create'),
    path('<int:book_id>/update/', views.book_update, name='book_update'),
    path('<int:book_id>/delete/', views.book_delete, name='book_delete'),
    path('export/', views.export_books, name='export_books'),  # 添加导出功能URL
    path('export/statistics/', views.export_statistics, name='export_statistics'),  # 添加统计导出功能URL
]