from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import BorrowRecord
from books.models import Book

User = get_user_model()

class BorrowRecordForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['user', 'book', 'due_date', 'notes']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'book': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean_book(self):
        """验证图书库存，防止并发问题"""
        book = self.cleaned_data.get('book')
        if book:
            # 检查库存但不锁定（表单验证阶段）
            if book.available_copies <= 0:
                raise ValidationError('所选图书当前不可借阅')
        return book

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['book'].queryset = Book.objects.filter(available_copies__gt=0)