from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from borrowing.models import BorrowRecord

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'账户 {username} 创建成功！')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')
                return redirect('home')
            else:
                messages.error(request, '用户名或密码错误。')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def profile(request):
    borrow_records = BorrowRecord.objects.filter(user=request.user).order_by('-borrow_date')[:10]
    return render(request, 'accounts/profile.html', {
        'borrow_records': borrow_records
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息更新成功！')
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout

def is_admin(user):
    return user.is_authenticated and user.is_admin

@user_passes_test(is_admin)
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})

@user_passes_test(is_admin)
def user_detail(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    borrow_records = BorrowRecord.objects.filter(user=user).order_by('-borrow_date')
    return render(request, 'accounts/user_detail.html', {
        'user_obj': user,
        'borrow_records': borrow_records
    })

def logout_view(request):
    """自定义登出视图，支持GET请求"""
    if request.method == 'GET' or request.method == 'POST':
        logout(request)
        messages.success(request, '您已成功登出！')
        return redirect('welcome')
    else:
        # 如果不是GET或POST请求，显示错误
        messages.error(request, '登出请求方法不被允许。')
        return redirect('home')

@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f'用户 {user.username} 状态已更新。')
    return redirect('accounts:user_list')