# Generated by Django 3.2.18 on 2023-07-14 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_auto_20230613_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='id',
            field=models.IntegerField(editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together={('shop', 'handle')},
        ),
    ]
