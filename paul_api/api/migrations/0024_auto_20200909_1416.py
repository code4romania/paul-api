# Generated by Django 3.1.1 on 2020-09-09 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_auto_20200909_1114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='dashboard_filters',
            field=models.ManyToManyField(blank=True, null=True, to='api.Filter'),
        ),
    ]
