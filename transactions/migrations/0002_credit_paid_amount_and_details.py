from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='credit',
            name='details',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='credit',
            name='paid_amount',
            field=models.FloatField(default=0),
        ),
    ]
