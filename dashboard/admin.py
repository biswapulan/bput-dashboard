from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AttendanceLog, CustomUser, Submission, Ticket


def superuser_only_has_permission(request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = superuser_only_has_permission


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Dashboard Role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Dashboard Role", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("subject_code_or_task_title", "intern", "task_type", "status", "created_at")
    list_filter = ("task_type", "material_type", "status", "semester")
    search_fields = ("subject_code_or_task_title", "intern__username", "submission_link")


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("user", "login_date", "first_login_time")
    list_filter = ("login_date",)
    search_fields = ("user__username",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "raised_by", "department", "status", "created_at")
    list_filter = ("department", "status")
    search_fields = ("subject", "description", "raised_by__username")

# Register your models here.
