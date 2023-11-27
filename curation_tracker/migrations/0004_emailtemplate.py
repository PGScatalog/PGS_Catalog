# Generated by Django 4.2.6 on 2023-11-27 20:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('curation_tracker', '0003_alter_curationpublicationannotation_curation_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_type', models.CharField(choices=[('author_data_request', 'Author Data Request')], default='author_data_request', verbose_name='Template Purpose')),
                ('subject', models.TextField(verbose_name='Email Subject')),
                ('body', models.TextField(verbose_name='Email Body')),
                ('is_default', models.BooleanField(default=True, verbose_name='Default Template')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created On')),
                ('last_modified_on', models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name='Last Modified On')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('last_modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_last_modified_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
            ],
        ),
    ]