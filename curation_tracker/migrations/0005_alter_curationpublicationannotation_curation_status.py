# Generated by Django 4.2.10 on 2024-04-19 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curation_tracker', '0004_emailtemplate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='curationpublicationannotation',
            name='curation_status',
            field=models.CharField(blank=True, choices=[('Abandoned/Ineligible', 'Abandoned/Ineligible'), ('Pending author response', 'Pending author response'), ('Awaiting L1', 'Awaiting L1'), ('Awaiting L2', 'Awaiting L2'), ('Curated - Awaiting Import', 'Curated - Awaiting Import'), ('Imported - Awaiting Release', 'Imported - Awaiting Release'), ('Released', 'Released'), ('Embargo Curated - Awaiting Import', 'Embargo Curated - Awaiting Import'), ('Embargo Imported - Awaiting Publication', 'Embargo Imported - Awaiting Publication'), ('Embargo Lifted - Awaiting Release', 'Embargo Lifted - Awaiting Release'), ('Retired', 'Retired')], default='Awaiting L1', max_length=50, null=True, verbose_name='Curation Status'),
        ),
    ]