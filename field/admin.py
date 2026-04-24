from django.contrib import admin
from .models import *


class FieldManagementAdmin(admin.ModelAdmin):
    list_display = [field.name for field in FieldManagement._meta.fields]
    ordering = ("-created_at",)

admin.site.register(FieldManagement, FieldManagementAdmin)


class AgentManagement(admin.ModelAdmin):
    list_display = [field.name for field in Agents._meta.fields]
    ordering = ("-created_at",)

admin.site.register(Agents, AgentManagement)
