# Generated by Django 3.1.1 on 2020-09-28 21:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_auto_20200924_1317'),
    ]

    operations = [
        migrations.AddField(
            model_name='chart',
            name='x_axis_field_2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='charts_x_axis_fields_group', to='api.tablecolumn'),
        ),
    ]
