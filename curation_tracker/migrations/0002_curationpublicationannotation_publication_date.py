# Generated by Django 4.2.6 on 2023-10-24 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curation_tracker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='curationpublicationannotation',
            name='publication_date',
            field=models.DateField(blank=True, null=True, verbose_name='Publication Date'),
        ),
    ]