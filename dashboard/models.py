from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CONTENT_SUPERVISOR = "CONTENT_SUPERVISOR", "Content Supervisor"
        TECH_SUPERVISOR = "TECH_SUPERVISOR", "Tech Supervisor"
        CONTENT_INTERN = "CONTENT_INTERN", "Content Intern"
        TECH_INTERN = "TECH_INTERN", "Tech Intern"

    class Department(models.TextChoices):
        CONTENT = "CONTENT", "Content"
        TECH = "TECH", "Tech"

    YEAR_CHOICES = [
        (1, "1st Year"),
        (2, "2nd Year"),
        (3, "3rd Year"),
        (4, "4th Year"),
    ]

    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ADMIN)
    college_name = models.CharField(max_length=150, blank=True)
    date_of_joining = models.DateField(auto_now_add=True)
    department = models.CharField(max_length=20, choices=Department.choices, blank=True, null=True)
    year = models.IntegerField(choices=YEAR_CHOICES, blank=True, null=True)
    intern_id = models.CharField(max_length=40, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.role in {self.Role.CONTENT_INTERN, self.Role.TECH_INTERN} and not self.intern_id:
            self.intern_id = self._generate_intern_id(self.role)
        super().save(*args, **kwargs)

    @classmethod
    def _generate_intern_id(cls, role):
        dept_prefix = "CNT" if role == cls.Role.CONTENT_INTERN else "TECH"
        date_part = timezone.localdate().strftime("%d%m%y")
        prefix_search = f"{dept_prefix}-INTERN-"
        last_number = 0
        for intern_id in cls.objects.filter(intern_id__startswith=prefix_search).values_list("intern_id", flat=True):
            try:
                last_number = max(last_number, int(intern_id.rsplit("-", 1)[1]))
            except (ValueError, IndexError):
                continue
        return f"{dept_prefix}-INTERN-{date_part}-{last_number + 1:03d}"


class AssignedTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUBMITTED = "SUBMITTED", "Submitted"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    task_id = models.CharField(max_length=60, unique=True, db_index=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_link = models.TextField(blank=True, help_text="Link to full task details (any URL)")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_tasks"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks_given"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_id} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.task_id:
            self.task_id = self._generate_task_id(self.assigned_to.department)
        super().save(*args, **kwargs)

    @classmethod
    def _generate_task_id(cls, department):
        # Determine dept from assigned_to at call site — we derive from existing count
        date_part = timezone.localdate().strftime("%Y%m%d")
        dept_prefix = "TCH" if department == CustomUser.Department.TECH else "CNT"
        prefix = f"TSK-{dept_prefix}-{date_part}-"
        last = cls.objects.filter(task_id__startswith=prefix).order_by("-task_id").first()
        next_num = 1
        if last:
            try:
                next_num = int(last.task_id.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                pass
        return f"{prefix}{next_num:03d}"


class Submission(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    task = models.OneToOneField(AssignedTask, on_delete=models.CASCADE, related_name="submission")
    intern = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )
    token_id = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    submission_link = models.TextField()
    note = models.TextField(blank=True, help_text="Optional note to supervisor")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    supervisor_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.token_id} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.token_id:
            self.token_id = self._generate_token(self.task.assigned_to.department)
        super().save(*args, **kwargs)

    @classmethod
    def _generate_token(cls, department):
        date_part = timezone.localdate().strftime("%Y%m%d")
        dept_prefix = "TCH" if department == CustomUser.Department.TECH else "CNT"
        prefix = f"SUB-{dept_prefix}-{date_part}-"
        last = cls.objects.filter(token_id__startswith=prefix).order_by("-token_id").first()
        next_num = 1
        if last:
            try:
                next_num = int(last.token_id.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                pass
        return f"{prefix}{next_num:03d}"


class AttendanceLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_logs")
    login_date = models.DateField(db_index=True)
    first_login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "login_date"], name="unique_daily_attendance")
        ]
        ordering = ["-login_date", "user__username"]

    def __str__(self):
        return f"{self.user.username} present on {self.login_date}"

    @property
    def duration(self):
        if self.logout_time and self.first_login_time:
            return self.logout_time - self.first_login_time
        return None


class Ticket(models.Model):
    class Department(models.TextChoices):
        CONTENT = "CONTENT", "Content"
        TECH = "TECH", "Tech"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"

    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets"
    )
    token_id = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    department = models.CharField(max_length=16, choices=Department.choices, db_index=True)
    subject = models.CharField(max_length=180)
    description = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
    supervisor_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.token_id} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.token_id:
            self.token_id = self._generate_token(self.department)
        super().save(*args, **kwargs)

    @classmethod
    def _generate_token(cls, department):
        dept_prefix = "CNT" if department == cls.Department.CONTENT else "TCH"
        date_part = timezone.localdate().strftime("%Y%m%d")
        prefix = f"TKT-{dept_prefix}-{date_part}-"
        last = cls.objects.filter(token_id__startswith=prefix).order_by("-token_id").first()
        next_num = 1
        if last:
            try:
                next_num = int(last.token_id.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                pass
        return f"{prefix}{next_num:03d}"


class Announcement(models.Model):
    ann_id = models.CharField(max_length=30, unique=True, db_index=True, blank=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcements"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ann_id} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.ann_id:
            self.ann_id = self._generate_ann_id()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_ann_id(cls):
        date_part = timezone.localdate().strftime("%Y%m%d")
        prefix = f"ANN-{date_part}-"
        last = cls.objects.filter(ann_id__startswith=prefix).order_by("-ann_id").first()
        next_num = 1
        if last:
            try:
                next_num = int(last.ann_id.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                pass
        return f"{prefix}{next_num:03d}"


class AnnouncementRead(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcement_reads")
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "announcement"], name="unique_ann_read")
        ]


class TaskRead(models.Model):
    """Tracks when an intern has seen their newly assigned task (for red dot)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_reads")
    task = models.ForeignKey(AssignedTask, on_delete=models.CASCADE, related_name="reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "task"], name="unique_task_read")
        ]


class SubmissionRead(models.Model):
    """Tracks when a supervisor has seen a new submission (for red dot)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submission_reads")
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "submission"], name="unique_submission_read")
        ]


class TicketRead(models.Model):
    """Tracks when a supervisor has seen a new ticket."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ticket_reads")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "ticket"], name="unique_ticket_read")
        ]


class InternAccountRead(models.Model):
    """Tracks when an admin has seen a newly created intern account."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intern_account_reads")
    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_read_marks")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "intern"], name="unique_intern_account_read")
        ]