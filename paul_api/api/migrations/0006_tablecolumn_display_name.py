# Generated by Django 3.1 on 2020-08-27 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_auto_20200827_0552"),
    ]

    operations = [
        migrations.AddField(
            model_name="tablecolumn",
            name="display_name",
            field=models.CharField(max_length=50, null=True),
        ),
    ]
