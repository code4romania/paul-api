# Generated by Django 3.1.2 on 2020-10-26 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0038_card'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='dashboard_cards',
            field=models.ManyToManyField(blank=True, to='api.Card'),
        ),
    ]