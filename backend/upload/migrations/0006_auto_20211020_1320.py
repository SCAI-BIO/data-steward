# Generated by Django 2.2.10 on 2021-10-20 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0005_datamodelattribute_iri'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datamodelattribute',
            name='Umbrella',
            field=models.CharField(default='Observation', max_length=64, verbose_name='Generalized term wrapping an attribute with further, analogous terms (= semantically highly similar, but not identical).'),
        ),
    ]