# Generated by Django 5.1.7 on 2025-04-16 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bike_buy_and_sell', '0007_chatmessage_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bikebuyandsell',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='bikebuyandsellimage',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
