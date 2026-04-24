from django.contrib import admin

from .models import *

class RoleAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Role._meta.fields]
    search_fields = ("role_name", "category")
    ordering = ("-created_at",)

admin.site.register(Role, RoleAdmin)

class UserAdmin(admin.ModelAdmin):
    list_display = [field.name for field in User._meta.fields]
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)

admin.site.register(User, UserAdmin)