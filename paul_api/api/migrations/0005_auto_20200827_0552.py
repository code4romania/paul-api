# Generated by Django 3.1 on 2020-08-27 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_auto_20200827_0511"),
    ]

    operations = [
        migrations.AlterField(
            model_name="csvimport",
            name="file",
            field=models.FileField(upload_to="csvs/"),
        ),
    ]
