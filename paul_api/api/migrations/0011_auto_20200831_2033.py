# Generated by Django 3.1 on 2020-08-31 20:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_auto_20200827_0729"),
    ]

    operations = [
        migrations.RenameField(
            model_name="csvimport",
            old_name="errors",
            new_name="errors_count",
        ),
        migrations.RenameField(
            model_name="csvimport",
            old_name="imported",
            new_name="imported_count",
        ),
        migrations.RemoveField(
            model_name="csvimport",
            name="success",
        ),
    ]
