import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0005_ticketread_require_task_submission"),
    ]

    operations = [
        migrations.CreateModel(
            name="InternAccountRead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("read_at", models.DateTimeField(auto_now_add=True)),
                (
                    "intern",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="admin_read_marks", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="intern_account_reads", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="internaccountread",
            constraint=models.UniqueConstraint(fields=("user", "intern"), name="unique_intern_account_read"),
        ),
    ]
