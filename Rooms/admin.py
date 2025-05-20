from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StorageUnit, Booking, Payment, Notification

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_customer', 'is_employee', 'is_admin', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_customer', 'is_employee', 'is_admin')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('is_customer', 'is_employee', 'is_admin')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(StorageUnit)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Notification)
