from django.urls import path
from . import views

app_name = 'borrowing'

urlpatterns = [
    path('my-records/', views.my_borrow_records, name='my_records'),
    path('records/', views.borrow_record_list, name='record_list'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:record_id>/', views.return_book, name='return_book'),
    path('create/', views.create_borrow_record, name='create_record'),
    path('<int:record_id>/update/', views.update_borrow_record, name='update_record'),
    path('<int:record_id>/delete/', views.delete_borrow_record, name='delete_record'),
    path('export/all/', views.export_borrow_records, name='export_all_records'),  # 添加所有记录导出URL
    path('export/my/', views.export_my_borrow_records, name='export_my_records'),  # 添加个人记录导出URL
]