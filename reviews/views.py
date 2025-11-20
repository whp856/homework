from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from accounts.models import CustomUser
from .models import Review
from .forms import ReviewForm

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
def my_reviews(request):
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'reviews/my_reviews.html', {'page_obj': page_obj})

def book_reviews(request, book_id):
    from books.models import Book
    book = get_object_or_404(Book, id=book_id)
    reviews = Review.objects.filter(book=book, is_approved=True).order_by('-created_at')

    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(book=book, user=request.user).first()

    return render(request, 'reviews/book_reviews.html', {
        'book': book,
        'page_obj': page_obj,
        'user_review': user_review
    })

@login_required
def create_review(request, book_id):
    from books.models import Book
    book = get_object_or_404(Book, id=book_id)

    existing_review = Review.objects.filter(book=book, user=request.user).first()
    if existing_review:
        messages.error(request, '您已经评论过这本书了。')
        return redirect('reviews:book_reviews', book_id=book.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book = book
            review.save()
            messages.success(request, '评论提交成功！')
            return redirect('reviews:book_reviews', book_id=book.id)
    else:
        form = ReviewForm()

    return render(request, 'reviews/review_form.html', {
        'form': form,
        'book': book,
        'title': '添加评论'
    })

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, '评论更新成功！')
            return redirect('reviews:book_reviews', book_id=review.book.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'reviews/review_form.html', {
        'form': form,
        'book': review.book,
        'title': '编辑评论',
        'review': review
    })

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        book_id = review.book.id
        review.delete()
        messages.success(request, '评论删除成功！')
        return redirect('reviews:book_reviews', book_id=book_id)

    return render(request, 'reviews/review_delete.html', {'review': review})

@user_passes_test(is_admin)
def review_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'reviews/review_list.html', {'page_obj': page_obj})

@user_passes_test(is_admin)
def approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = not review.is_approved
    review.save()
    status = "审核通过" if review.is_approved else "取消审核"
    messages.success(request, f'评论{status}成功！')
    return redirect('reviews:review_list')

@user_passes_test(is_admin)
def delete_review_admin(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        review.delete()
        messages.success(request, '评论删除成功！')
        return redirect('reviews:review_list')
    return render(request, 'reviews/review_delete_admin.html', {'review': review})