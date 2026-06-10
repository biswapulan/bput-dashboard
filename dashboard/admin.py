from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Announcement, AnnouncementRead, AssignedTask, AttendanceLog, CustomUser, InternAccountRead, Submission, SubmissionRead, TaskRead, Ticket, TicketRead


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "intern_id", "role", "department", "college_name")
    list_filter = ("role", "department")
    fieldsets = UserAdmin.fieldsets + (
        ("BPUT Info", {"fields": ("role", "department", "year", "college_name", "intern_id", "date_of_joining")}),
    )


@admin.register(AssignedTask)
class AssignedTaskAdmin(admin.ModelAdmin):
    list_display = ("task_id", "title", "assigned_to", "assigned_by", "status", "created_at")
    list_filter = ("status",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("token_id", "intern", "task", "status", "created_at")
    list_filter = ("status",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("token_id", "raised_by", "department", "subject", "status", "created_at")
    list_filter = ("department", "status")


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("user", "login_date", "first_login_time")
    list_filter = ("login_date",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("ann_id", "title", "created_by", "created_at")


admin.site.register(AnnouncementRead)
admin.site.register(TaskRead)
admin.site.register(SubmissionRead)
admin.site.register(TicketRead)
admin.site.register(InternAccountRead)
