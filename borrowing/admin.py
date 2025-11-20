from django.contrib import admin
from .models import BorrowRecord

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'borrow_date', 'due_date', 'return_date', 'status']
    list_filter = ['status', 'borrow_date', 'due_date']
    search_fields = ['user__username', 'book__title', 'book__author']
    readonly_fields = ['created_at', 'updated_at']