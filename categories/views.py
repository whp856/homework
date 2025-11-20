from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from accounts.models import CustomUser
from .models import Category
from .forms import CategoryForm

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'categories/category_list.html', {'page_obj': page_obj})

@login_required
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    books = category.book_set.all().order_by('title')
    return render(request, 'categories/category_detail.html', {
        'category': category,
        'books': books
    })

@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '分类创建成功！')
            return redirect('categories:category_list')
    else:
        form = CategoryForm()
    return render(request, 'categories/category_form.html', {
        'form': form,
        'title': '创建分类'
    })

@user_passes_test(is_admin)
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '分类更新成功！')
            return redirect('categories:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'categories/category_form.html', {
        'form': form,
        'title': '编辑分类',
        'category': category
    })

@user_passes_test(is_admin)
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, '分类删除成功！')
        return redirect('categories:category_list')
    return render(request, 'categories/category_delete.html', {'category': category})