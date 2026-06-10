import datetime

from django.db import migrations, models


def backfill_tracking_fields(apps, schema_editor):
    CustomUser = apps.get_model("dashboard", "CustomUser")
    Submission = apps.get_model("dashboard", "Submission")
    Ticket = apps.get_model("dashboard", "Ticket")

    current_year = datetime.date.today().year
    intern_prefix = f"BPUT-{current_year}-"
    intern_counter = 1
    for user in CustomUser.objects.filter(role__in=["CONTENT_INTERN", "TECH_INTERN"]).order_by("id"):
        if not user.intern_id:
            user.intern_id = f"{intern_prefix}{intern_counter:04d}"
            intern_counter += 1
        if not user.department:
            user.department = "CONTENT" if user.role == "CONTENT_INTERN" else "TECH"
        user.save(update_fields=["intern_id", "department"])

    submission_counters = {}
    for submission in Submission.objects.order_by("created_at", "id"):
        if submission.token_id:
            continue
        token_prefix = "TECH" if submission.task_type == "TECH" else "CNT"
        created_date = submission.created_at.date() if submission.created_at else datetime.date.today()
        date_part = created_date.strftime("%Y%m%d")
        counter_key = f"{token_prefix}-{date_part}"
        submission_counters[counter_key] = submission_counters.get(counter_key, 0) + 1
        submission.token_id = f"{counter_key}-{submission_counters[counter_key]:03d}"
        submission.save(update_fields=["token_id"])

    ticket_counters = {}
    for ticket in Ticket.objects.order_by("created_at", "id"):
        if ticket.token_id:
            continue
        created_date = ticket.created_at.date() if ticket.created_at else datetime.date.today()
        date_part = created_date.strftime("%Y%m%d")
        counter_key = f"TKT-{date_part}"
        ticket_counters[counter_key] = ticket_counters.get(counter_key, 0) + 1
        ticket.token_id = f"{counter_key}-{ticket_counters[counter_key]:03d}"
        ticket.save(update_fields=["token_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0002_alter_customuser_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="first_name",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="last_name",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="customuser",
            name="college_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="customuser",
            name="date_of_joining",
            field=models.DateField(auto_now_add=True, default=datetime.date(2026, 6, 10)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customuser",
            name="department",
            field=models.CharField(
                blank=True,
                choices=[("CONTENT", "Content"), ("TECH", "Tech")],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="intern_id",
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="year",
            field=models.IntegerField(
                blank=True,
                choices=[(1, "1st Year"), (2, "2nd Year"), (3, "3rd Year"), (4, "4th Year")],
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="submission",
            name="token_id",
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="submission",
            name="submission_link",
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name="ticket",
            name="token_id",
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True, unique=True),
        ),
        migrations.RunPython(backfill_tracking_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="submission",
            name="token_id",
            field=models.CharField(blank=True, db_index=True, max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="token_id",
            field=models.CharField(blank=True, db_index=True, max_length=50, unique=True),
        ),
    ]
