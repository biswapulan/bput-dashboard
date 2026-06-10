import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def delete_orphan_submissions(apps, schema_editor):
    Submission = apps.get_model("dashboard", "Submission")
    Submission.objects.filter(task__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0004_announcement_announcementread_assignedtask_and_more"),
    ]

    operations = [
        migrations.RunPython(delete_orphan_submissions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="submission",
            name="task",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="submission",
                to="dashboard.assignedtask",
            ),
        ),
        migrations.CreateModel(
            name="TicketRead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("read_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ticket",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reads", to="dashboard.ticket"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_reads", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="ticketread",
            constraint=models.UniqueConstraint(fields=("user", "ticket"), name="unique_ticket_read"),
        ),
    ]
