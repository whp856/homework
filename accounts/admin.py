from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('额外信息', {'fields': ('role', 'phone', 'address', 'birth_date')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('额外信息', {'fields': ('role', 'phone', 'address', 'birth_date')}),
    )