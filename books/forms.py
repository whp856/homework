from django import forms
from django.core.exceptions import ValidationError
from .models import Book
from categories.models import Category

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'publisher', 'publication_date',
            'category', 'description', 'cover_image', 'total_copies',
            'available_copies', 'location', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'publication_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            # 检查文件大小（最大5MB）
            if cover_image.size > 5 * 1024 * 1024:
                raise ValidationError('封面图片大小不能超过5MB')

            # 检查文件类型
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if cover_image.content_type not in allowed_types:
                raise ValidationError('只支持 JPG、PNG、GIF、WebP 格式的图片')

            # 检查文件扩展名
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = cover_image.name.lower().split('.')[-1] if '.' in cover_image.name else ''
            if f'.{file_extension}' not in allowed_extensions:
                raise ValidationError('文件扩展名不正确')

        return cover_image

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if isbn:
            # 验证ISBN格式（简单验证）
            import re
            if not re.match(r'^[\d-]{10,17}$', isbn.replace('-', '')):
                raise ValidationError('ISBN格式不正确')
        return isbn

    def clean(self):
        cleaned_data = super().clean()
        total_copies = cleaned_data.get('total_copies')
        available_copies = cleaned_data.get('available_copies')

        if total_copies and available_copies:
            if available_copies > total_copies:
                raise ValidationError('可借册数不能大于总册数')

        return cleaned_data