# Generated by Django 2.2.10 on 2022-08-31 10:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0009_auto_20220831_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='datamodelsource',
            name='Active',
            field=models.BooleanField(default=True, verbose_name="Indicates whether item is in use in the backend's current setup."),
        ),
        migrations.AlterField(
            model_name='datamodelattribute',
            name='Unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='upload.DatamodelUnit'),
        ),
    ]
