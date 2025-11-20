from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.category_list, name='category_list'),
    path('<int:category_id>/', views.category_detail, name='category_detail'),
    path('create/', views.category_create, name='category_create'),
    path('<int:category_id>/update/', views.category_update, name='category_update'),
    path('<int:category_id>/delete/', views.category_delete, name='category_delete'),
]