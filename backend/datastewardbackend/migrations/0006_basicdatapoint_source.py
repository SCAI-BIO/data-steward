# Generated by Django 2.2.10 on 2021-09-29 08:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0005_datamodelattribute_iri'),
        ('datastewardbackend', '0005_auto_20210811_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='basicdatapoint',
            name='source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='upload.DatamodelSource'),
        ),
    ]
