from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('book/<int:book_id>/', views.book_reviews, name='book_reviews'),
    path('create/<int:book_id>/', views.create_review, name='create_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),

    # 管理员功能
    path('list/', views.review_list, name='review_list'),
    path('<int:review_id>/approve/', views.approve_review, name='approve_review'),
    path('<int:review_id>/delete-admin/', views.delete_review_admin, name='delete_review_admin'),
]