# Generated by Django 2.2.10 on 2021-02-26 14:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LiteralModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=1024)),
                ('description', models.TextField(blank=True, null=True)),
                ('synonyms', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SemanticAsset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1028)),
                ('description', models.TextField()),
                ('provenenace', models.CharField(blank=True, max_length=1028, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MeasurementLocation',
            fields=[
                ('literalmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='datastewardbackend.LiteralModel')),
            ],
            bases=('datastewardbackend.literalmodel',),
        ),
        migrations.CreateModel(
            name='MeasurementMethod',
            fields=[
                ('literalmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='datastewardbackend.LiteralModel')),
            ],
            bases=('datastewardbackend.literalmodel',),
        ),
        migrations.CreateModel(
            name='MeasurementObject',
            fields=[
                ('literalmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='datastewardbackend.LiteralModel')),
            ],
            bases=('datastewardbackend.literalmodel',),
        ),
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_of_measurement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='datastewardbackend.MeasurementLocation')),
                ('method_of_measurement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='datastewardbackend.MeasurementMethod')),
                ('object_of_measurement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datastewardbackend.MeasurementObject')),
            ],
        ),
    ]
