# Generated by Django 3.1.2 on 2020-10-09 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugin_woocommerce', '0005_auto_20201009_0620'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='status',
        ),
        migrations.AddField(
            model_name='taskresult',
            name='status',
            field=models.CharField(default='In progress', max_length=20),
        ),
    ]