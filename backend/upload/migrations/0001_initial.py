# Generated by Django 2.2.10 on 2021-02-26 14:31

from django.db import migrations, models
import django.db.models.deletion
import djongo.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DatamodelAttribute',
            fields=[
                ('Active', models.BooleanField(default=True, verbose_name="Indicates whether item is in use in the backend's current setup.")),
                ('Topic', models.CharField(blank=True, max_length=64, null=True, verbose_name='Topic (= semantic category) the identifier belongs to (e.g. neuropsychology, lab, medication, ...).')),
                ('Topic_Description', models.CharField(blank=True, max_length=256, null=True, verbose_name="Topic's full text description.")),
                ('Umbrella', models.CharField(blank=True, max_length=64, null=True, verbose_name='Generalized term wrapping an attribute with further, analogous terms (= semantically highly similar, but not identical).')),
                ('Umbrella_Description', models.CharField(blank=True, max_length=256, null=True, verbose_name="Umbrella's full text description.")),
                ('Attribute', models.CharField(max_length=64, primary_key=True, serialize=False, verbose_name="The unique item's name throughout the overall data model")),
                ('Attribute_Description', models.CharField(max_length=256, verbose_name="Unique attribute's fulltext description.")),
                ('Attribute_Tooltip', models.CharField(max_length=64, verbose_name='Very short description, suitable for tooltips or table headings.')),
                ('Datatype', models.CharField(choices=[('code', "A list of valid choices, referenced in 'domain'. A code might be used as set of choices for multiple variables, but is immutable."), ('date', "A date, formatted according to ISO 8601 (YYYY-MM-DD). If undetermined, e.g. due to coarsening, days and/or month might be stored as '00'."), ('int', 'Classical integer value.'), ('float', 'Classical fractional number.'), ('string', 'Character string (free text).'), ('array(date)', 'Array of ISO 8601 dates.'), ('array(int)', 'Array of classical integer values.'), ('array(float)', 'Array of classical fractional numbers.'), ('array(string)', 'Array of character strings (free text).'), ('array(code)', 'Array of encoded values.')], max_length=16, verbose_name='Possible datatype (string, int, float, date, code or arrays of the first three).')),
                ('Domain', models.CharField(blank=True, max_length=64, null=True, verbose_name='Accepted range of numeric values (2-items arry in Python notation; empty entry is valid) or name of code (for categorical items).')),
            ],
        ),
        migrations.CreateModel(
            name='DatamodelCodeMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Active', models.BooleanField(default=True, verbose_name="Indicates whether item is in use in the backend's current setup.")),
                ('Code_Mapping', models.CharField(max_length=32, verbose_name='Unique mapping identifier (to be referred in the Attribute Mappings table).')),
                ('Source_Value', models.CharField(max_length=64, verbose_name="Actual value of the source (external) datamodel's, possibly also encoded, attribute.")),
                ('Source_Value_Description', models.CharField(blank=True, max_length=256, null=True, verbose_name="Description/meaning of the source (external) datamodel's, possibly also encoded, value.")),
                ('Target_Equivalent', models.CharField(max_length=32, verbose_name="Key of the common core datamodel's encoded attribute. The target (core) code is referred in the respective Attribute Mapping Table entry")),
                ('Remarks', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Additional information on the described mapping')),
            ],
        ),
        migrations.CreateModel(
            name='DatamodelSource',
            fields=[
                ('Abbreviation', models.CharField(max_length=32, primary_key=True, serialize=False, verbose_name='Abbreviated label, unique in the IDSN clinical datamodel.')),
                ('Source', models.CharField(max_length=256, verbose_name='Name of the registry/study/source.')),
                ('PID_colname', models.CharField(blank=True, max_length=64, null=True, verbose_name="Alternate name of column containing the patient's ID.")),
                ('SITE_colname', models.CharField(blank=True, max_length=64, null=True, verbose_name="Alternate name of column containing the site's ID (multi-center study data).")),
                ('TIMESTAMP_colname', models.CharField(blank=True, max_length=64, null=True, verbose_name="Alternate name of column containing the measurement's time stamp.")),
                ('Header_offset', models.IntegerField(default=0, verbose_name='Number of lines to ignore before expecting the first line of the actual data (which is the header).')),
                ('Filepath', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Location of the uploaded file.')),
            ],
        ),
        migrations.CreateModel(
            name='DatamodelUnit',
            fields=[
                ('Unit', models.CharField(max_length=16, primary_key=True, serialize=False, verbose_name='Unique code expressing unit.')),
                ('UCUM', models.BooleanField(default=True, verbose_name='Indicates whether code is listed in UCUM.')),
                ('Description', models.CharField(max_length=256, verbose_name='Short description of unit.')),
            ],
        ),
        migrations.CreateModel(
            name='DataPointsVisit',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('DATE', models.CharField(max_length=10, verbose_name="String describing date as 'YYYY-MM-DD' (acc. to ISO 8601). Days and months are optional, but to be indicated by '00'")),
                ('PID', models.CharField(max_length=128, verbose_name='Patient ID, unique for SOURCE.')),
                ('TIMESTAMP', models.CharField(max_length=10, verbose_name="String describing date as 'YYYY-MM-DD' (acc. to ISO 8601). Days and months are optional, but to be indicated by '00'")),
                ('ATTRIBUTE', models.CharField(max_length=32, verbose_name="Measured attribute ('observation'), according to datamodel's declarations.")),
                ('VISIT', models.CharField(blank=True, max_length=128, null=True, verbose_name='Visit')),
                ('VALUE', models.CharField(max_length=2048, verbose_name='Value measured for item.')),
                ('PROVENANCE', models.CharField(blank=True, max_length=1024, null=True, verbose_name='String declaring the origin of data acc. to SOURCE, incl. data locations, extration procedures, conversion techniques etc.')),
                ('SOURCE', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='GeneticJson',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('data_id', models.CharField(max_length=128, unique=True)),
                ('json_string', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='UserFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploaded_data')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='VisitsDataSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_json', models.TextField()),
                ('timestamp', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='DataPoints',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('PID', models.CharField(max_length=128, verbose_name='Patient ID, unique for SOURCE.')),
                ('DATE', models.CharField(max_length=10, verbose_name="String describing date as 'YYYY-MM-DD' (acc. to ISO 8601). Days and months are optional, but to be indicated by '00'")),
                ('VALUE', models.CharField(max_length=2048, verbose_name='Value measured for item.')),
                ('PROVENANCE', models.CharField(max_length=1024, verbose_name='String declaring the origin of data acc. to SOURCE, incl. data locations, extration procedures, conversion techniques etc.')),
                ('ATTRIBUTE', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='upload.DatamodelAttribute')),
                ('SOURCE', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='upload.DatamodelSource')),
            ],
        ),
        migrations.CreateModel(
            name='DatamodelCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Active', models.BooleanField(default=True, verbose_name="Indicates whether item is in use in the backend's current setup.")),
                ('Code', models.CharField(max_length=32, verbose_name='Unique code in the IDSN clinical datamodel.')),
                ('Code_Description', models.CharField(max_length=256, verbose_name="Short description on code's scope.")),
                ('Key', models.CharField(max_length=32, verbose_name='Unique key within the referred IDSN clinical datamodel code.')),
                ('Value', models.CharField(max_length=256, verbose_name='Value/meaning encoded by unique key of code.')),
            ],
            options={
                'unique_together': {('Code', 'Key')},
            },
        ),
        migrations.CreateModel(
            name='DatamodelCalculation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Active', models.BooleanField(default=True, verbose_name="Indicates whether item is in use in the backend's current setup.")),
                ('Workbench', models.BooleanField(default=True, verbose_name='Indicates whether item is intended to appear as variable workbench entry.')),
                ('Attribute', models.CharField(max_length=64, verbose_name='Unique code in the source datamodel.')),
                ('Function', models.CharField(max_length=1024, verbose_name='Formal description of function to apply; limited to available, pre-defined functions; contains probably at least one attribute')),
                ('Comments', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Additional information on the described mapping')),
                ('Remarks', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Remarks from Spreadsheet')),
                ('Source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='upload.DatamodelSource')),
            ],
        ),
        migrations.AddField(
            model_name='datamodelattribute',
            name='Unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='upload.DatamodelUnit'),
        ),
        migrations.CreateModel(
            name='DatamodelAttributeMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Active', models.BooleanField(default=True, verbose_name="Indicates whether item is in use in the backend's current setup.")),
                ('Source_Attribute', models.CharField(max_length=64, verbose_name='Unique attribute name in the source datamodel.')),
                ('Transformation', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Operation to be applied, if necessary, when mapping.')),
                ('Source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='upload.DatamodelSource')),
                ('Target_Attribute', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='upload.DatamodelAttribute')),
            ],
            options={
                'unique_together': {('Source', 'Source_Attribute', 'Target_Attribute')},
            },
        ),
    ]
