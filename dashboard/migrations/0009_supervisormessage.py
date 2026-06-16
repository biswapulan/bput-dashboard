from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_attendancelog_logout_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupervisorMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('msg_id', models.CharField(blank=True, db_index=True, max_length=30, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('sent_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sent_supervisor_messages',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('sent_to', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='received_supervisor_messages',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
