from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CONTENT_SUPERVISOR = "CONTENT_SUPERVISOR", "Content Supervisor"
        TECH_SUPERVISOR = "TECH_SUPERVISOR", "Tech Supervisor"
        CONTENT_INTERN = "CONTENT_INTERN", "Content Intern"
        TECH_INTERN = "TECH_INTERN", "Tech Intern"

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ADMIN)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Submission(models.Model):
    class TaskType(models.TextChoices):
        CONTENT = "CONTENT", "Content"
        TECH = "TECH", "Tech"

    class MaterialType(models.TextChoices):
        NOTES = "NOTES", "Notes"
        PYQ = "PYQ", "PYQ"
        BOOK = "BOOK", "Book"
        CODE_FIX = "CODE_FIX", "Code Fix"
        FEATURE_DEV = "FEATURE_DEV", "Feature Development"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    SEMESTER_CHOICES = [(value, f"Semester {value}") for value in range(1, 9)]

    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    task_type = models.CharField(max_length=16, choices=TaskType.choices, db_index=True)
    material_type = models.CharField(max_length=24, choices=MaterialType.choices, db_index=True)
    subject_code_or_task_title = models.CharField(max_length=180)
    semester = models.IntegerField(choices=SEMESTER_CHOICES, blank=True, null=True, db_index=True)
    submission_link = models.URLField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    supervisor_remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["task_type", "status"]),
            models.Index(fields=["intern", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject_code_or_task_title} - {self.status}"


class AttendanceLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_logs")
    login_date = models.DateField(db_index=True)
    first_login_time = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "login_date"], name="unique_daily_attendance")
        ]
        indexes = [
            models.Index(fields=["login_date", "user"]),
        ]
        ordering = ["-login_date", "user__username"]

    def __str__(self):
        return f"{self.user.username} present on {self.login_date}"


class Ticket(models.Model):
    class Department(models.TextChoices):
        CONTENT = "CONTENT", "Content"
        TECH = "TECH", "Tech"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"

    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    department = models.CharField(max_length=16, choices=Department.choices, db_index=True)
    subject = models.CharField(max_length=180)
    description = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["department", "status"]),
            models.Index(fields=["raised_by", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} - {self.status}"

# Create your models here.
