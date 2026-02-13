from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Add the 'role' and 'phone_number' to the list view
    list_display = ('username', 'email', 'role', 'phone_number', 'is_staff')
    
    # Add filters so you can quickly see all "Students" or all "Teachers"
    list_filter = ('role', 'is_staff', 'is_superuser')
    
    # Fieldsets control how the "Edit User" page looks
    fieldsets = UserAdmin.fieldsets + (
        ('Shreeji GyanSetu Profile', {'fields': ('role', 'phone_number', 'profile_picture')}),
    )
    
    # Add fields for the "Create User" page
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Shreeji GyanSetu Profile', {'fields': ('role', 'phone_number')}),
    )

admin.site.register(User, CustomUserAdmin)