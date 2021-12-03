# Create your models here.
from django.db import models
from djongo import models as djongo_models
from django.conf import settings


class DatamodelSource(djongo_models.Model):
    Abbreviation      = djongo_models.CharField(   "Abbreviated label, unique in the IDSN clinical datamodel.",
                                            max_length=32,
                                            primary_key=True)
    Source            = djongo_models.CharField(   "Name of the registry/study/source.",
                                            max_length=256)
    PID_colname       = djongo_models.CharField(   "Alternate name of column containing the patient's ID.",
                                            max_length=64,
                                            blank=True,
                                            null=True)
    SITE_colname      = djongo_models.CharField(   "Alternate name of column containing the site's ID (multi-center study data).",
                                            max_length=64,
                                            blank=True,
                                            null=True)
    TIMESTAMP_colname = djongo_models.CharField(   "Alternate name of column containing the measurement's time stamp.",
                                            max_length=64,
                                            blank=True,
                                            null=True)
    Header_offset     = djongo_models.IntegerField("Number of lines to ignore before expecting the first line of the actual data (which is the header).",
                                            default=0)
    Filepath          = djongo_models.CharField(   "Location of the uploaded file.",
                                            max_length=1024,
                                            blank=True,
                                            null=True)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value


class DatamodelUnit(djongo_models.Model):

    Unit        = djongo_models.CharField(      "Unique code expressing unit.",
                                                max_length=1024,
                                                primary_key=True)
    UCUM        = djongo_models.BooleanField(   "Indicates whether code is listed in UCUM.",
                                                default=True)
    Description = djongo_models.CharField(      "Short description of unit.",
                                                max_length=4096)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value


class DatamodelAttribute(djongo_models.Model):
    DATA_TYPES = (
        ("code", "A list of valid choices, referenced in 'domain'. A code might be used as set of choices for multiple variables, but is immutable."),
        ("date", "A date, formatted according to ISO 8601 (YYYY-MM-DD). If undetermined, e.g. due to coarsening, days and/or month might be stored as '00'."),
        ("int", "Classical integer value."),
        ("float", "Classical fractional number."),
        ("string", "Character string (free text)."),
        ("array(date)", "Array of ISO 8601 dates."),
        ("array(int)", "Array of classical integer values."),
        ("array(float)", "Array of classical fractional numbers."),
        ("array(string)", "Array of character strings (free text)."),
        ("array(code)", "Array of encoded values.")
    )

    Active                = djongo_models.BooleanField( "Indicates whether item is in use in the backend's current setup.",
                                                        default=True)
    Topic                 = djongo_models.CharField(    "Topic (= semantic category) the identifier belongs to (e.g. neuropsychology, lab, medication, ...).",
                                                        max_length=64,
                                                        blank=True,
                                                        null=True)
    Topic_Description     = djongo_models.CharField(    "Topic's full text description.",
                                                        max_length=256,
                                                        blank=True,
                                                        null=True)
    Umbrella              = djongo_models.CharField(    "Generalized term wrapping an attribute with further, analogous terms (= semantically highly similar, but not identical).",
                                                        max_length=64,
                                                        default = "Observation")
    Umbrella_Description  = djongo_models.CharField(    "Umbrella's full text description.",
                                                        max_length=256,
                                                        blank=True,
                                                        null=True)
    Attribute             = djongo_models.CharField(    "The unique item's name throughout the overall data model",
                                                        primary_key=True,
                                                        max_length=64)
    Attribute_Description = djongo_models.CharField(    "Unique attribute's fulltext description.",
                                                        max_length=256)
    Attribute_Tooltip     = djongo_models.CharField(    "Very short description, suitable for tooltips or table headings.",
                                                        max_length=64)
    Datatype              = djongo_models.CharField(    "Possible datatype (string, int, float, date, code or arrays of the first three).",
                                                        max_length=16,
                                                        choices=DATA_TYPES )
    Domain                = djongo_models.CharField(    "Accepted range of numeric values (2-items arry in Python notation; empty entry is valid) or name of code (for categorical items).",
                                                        max_length=64,
                                                        blank=True,
                                                        null=True)
    Unit                  = djongo_models.ForeignKey(   DatamodelUnit,
                                                        to_field="Unit",
                                                        on_delete=djongo_models.CASCADE)

    IRI = djongo_models.CharField(max_length=1024, null=True, blank=True)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value

class DatamodelAttibuteSynonym(djongo_models.Model):
    Target_Attribute    = djongo_models.ForeignKey( DatamodelAttribute,
                                                    to_field="Attribute",
                                                    on_delete=djongo_models.CASCADE)
    Synonym = djongo_models.CharField(max_length=1024)
    


class DatamodelCode(djongo_models.Model):              # primary key is implicit
    class Meta:
        unique_together = (('Code','Key'))

    Active           = djongo_models.BooleanField("Indicates whether item is in use in the backend's current setup.",
                                        default=True)
    Code             = djongo_models.CharField("Unique code in the IDSN clinical datamodel.",
                                        max_length=32)
    Code_Description = djongo_models.CharField("Short description on code's scope.",
                                        max_length=256)
    Key              = djongo_models.CharField("Unique key within the referred IDSN clinical datamodel code.",
                                        max_length=32)
    Value            = djongo_models.CharField("Value/meaning encoded by unique key of code.",
                                        max_length=256)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value


class DatamodelAttributeMapping(djongo_models.Model):  # primary key is implicit
    class Meta:
        unique_together = (('Source', 'Source_Attribute', 'Target_Attribute'))

    Active              = djongo_models.BooleanField("Indicates whether item is in use in the backend's current setup.",
                                        default=True)
    Source              = djongo_models.ForeignKey( DatamodelSource,
                                                    to_field="Abbreviation",
                                                    on_delete=djongo_models.CASCADE)
    Source_Attribute    = djongo_models.CharField(  "Unique attribute name in the source datamodel.",
                                                    max_length=64)
    Target_Attribute    = djongo_models.ForeignKey( DatamodelAttribute,
                                                    to_field="Attribute",
                                                    on_delete=djongo_models.CASCADE)
    Transformation      = djongo_models.CharField(  "Operation to be applied, if necessary, when mapping.",
                                                    max_length=1024,
                                                    blank=True,
                                                    null=True)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value


class DatamodelCodeMapping(djongo_models.Model):
    Active                   = djongo_models.BooleanField("Indicates whether item is in use in the backend's current setup.",
                                                default=True)
    Code_Mapping             = djongo_models.CharField("Unique mapping identifier (to be referred in the Attribute Mappings table).",
                                                max_length=32)
    Source_Value             = djongo_models.CharField("Actual value of the source (external) datamodel's, possibly also encoded, attribute.",
                                                max_length=64)
    Source_Value_Description = djongo_models.CharField("Description/meaning of the source (external) datamodel's, possibly also encoded, value.",
                                                max_length=256,
                                                blank=True,
                                                null=True)
    Target_Equivalent        = djongo_models.CharField("Key of the common core datamodel's encoded attribute. The target (core) code is referred in the respective Attribute Mapping Table entry",
                                                max_length=32)
    Remarks                  = djongo_models.CharField("Additional information on the described mapping",
                                                max_length=1024,
                                                blank=True,
                                                null=True)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value


class DatamodelCalculation(djongo_models.Model):
    Active                   = djongo_models.BooleanField("Indicates whether item is in use in the backend's current setup.",
                                                default=True)
    Workbench                = djongo_models.BooleanField("Indicates whether item is intended to appear as variable workbench entry.",
                                                default=True)
    Source                   = djongo_models.ForeignKey(DatamodelSource,
                                                to_field="Abbreviation",
                                                on_delete=djongo_models.CASCADE)
    Attribute                = djongo_models.CharField("Unique code in the source datamodel.",
                                                max_length=64)
    Function                 = djongo_models.CharField("Formal description of function to apply; limited to available, pre-defined functions; contains probably at least one attribute",
                                                max_length=1024)
    Comments                 = djongo_models.CharField("Additional information on the described mapping",
                                                max_length=1024,
                                                blank=True,
                                                null=True)
    Remarks                  = djongo_models.CharField("Remarks from Spreadsheet", max_length=1024, blank=True, null=True)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value


class DataPoints(djongo_models.Model):

    _id         = djongo_models.ObjectIdField()

    PID         = djongo_models.CharField( "Patient ID, unique for SOURCE.",
                                    max_length=128)
    DATE        = djongo_models.CharField( "String describing date as 'YYYY-MM-DD' (acc. to ISO 8601). Days and months are optional, but to be indicated by '00'",
                                    max_length=10)
    #ATTRIBUTE   = djongo_models.CharField( "Measured attribute ('observation'), according to datamodel's declarations.",
    #                                max_length=32)
    ATTRIBUTE   = djongo_models.ForeignKey(DatamodelAttribute,
                                    to_field="Attribute",
                                    on_delete=djongo_models.CASCADE)
    VALUE       = djongo_models.CharField( "Value measured for item.",
                                    max_length=2048)
    PROVENANCE  = djongo_models.CharField( "String declaring the origin of data acc. to SOURCE, incl. data locations, extration procedures, conversion techniques etc.",
                                    max_length=1024)
    #SOURCE      = djongo_models.CharField( "Actual data source; legal selection from declared sources in datamodel.",
    #                                max_length=256 )
    SOURCE      = djongo_models.ForeignKey(DatamodelSource,
                                    to_field="Abbreviation",
                                    on_delete=djongo_models.CASCADE)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value

class DataPointsVisit(models.Model):

    _id         = djongo_models.ObjectIdField()

    DATE        = djongo_models.CharField( "String describing date as 'YYYY-MM-DD' (acc. to ISO 8601). Days and months are optional, but to be indicated by '00'",
                                    max_length=10)

    PID         = models.CharField( "Patient ID, unique for SOURCE.",
                                    max_length=128)
    TIMESTAMP        = models.CharField( "String describing date as 'YYYY-MM-DD' (acc. to ISO 8601). Days and months are optional, but to be indicated by '00'",
                                    max_length=10)
    ATTRIBUTE   = models.CharField( "Measured attribute ('observation'), according to datamodel's declarations.",
                                    max_length=32)
    #ATTRIBUTE   = djongo_models.ForeignKey(DatamodelAttribute,
     #                               to_field="Attribute",
      #                              on_delete=djongo_models.PROTECT)

    VISIT       = models.CharField( "Visit",
                                    max_length=128,
                                    blank = True,
                                    null = True)

    VALUE       = models.CharField( "Value measured for item.",
                                    max_length=2048)
    PROVENANCE  = models.CharField( "String declaring the origin of data acc. to SOURCE, incl. data locations, extration procedures, conversion techniques etc.",
                                    max_length=1024,
                                    blank=True,
                                    null=True)
    SOURCE = djongo_models.ForeignKey(DatamodelSource,
                                      to_field="Abbreviation",
                                      on_delete=djongo_models.CASCADE)
    #SOURCE = djongo_models.CharField(max_length=1024)

    def attrs(self):
        """Dictionary with instance attributes."""
        for attr, value in self.__dict__.items():
            yield attr, value

    #SOURCE      = djongo_models.ForeignKey(DatamodelSource,
    #                                to_field="Abbreviation",
            #                               on_delete=djongo_models.PROTECT)


class VisitsDataSet(models.Model):
    data_json = models.TextField()
    timestamp = models.DateField(auto_now_add=True)

# class DataPointsF(djongo_models.Model):
#
#     _id          = djongo_models.ObjectIdField()
#
#     PID          = djongo_models.CharField(   "Patient ID, unique for SOURCE.",
#                                        max_length=128 )
#     #DATE         = djongo_models.DateField(   _("Date"),
#     DATE         = djongo_models.DateField(   "Actual date of measurement",
#                                        blank=True,
#                                        null=True )
#     ATTRIBUTE    = djongo_models.ForeignKey(  DatamodelAttribute,
#                                        to_field="Attribute",
#                                        on_delete=djongo_models.PROTECT )
#     VALUE_STR    = djongo_models.CharField(   "String value measured for item, including code key.",
#                                        max_length=256,
#                                        blank=True,
#                                        null=True )
#     VALUE_INT    = djongo_models.IntegerField("Integer value measured for item.",
#                                        blank=True,
#                                        null=True )
#     VALUE_DATE_Y = djongo_models.IntegerField("Integer value measured for item, encoding date year.",
#                                        blank=True,
#                                        null=True )
#     VALUE_DATE_M = djongo_models.IntegerField("Integer value measured for item, encoding date month.",
#                                        blank=True,
#                                        null=True)
#     VALUE_DATE_D = djongo_models.IntegerField("Integer value measured for item, encoding date day.",
#                                        blank=True,
#                                        null=True)
#     VALUE_FLOAT  = djongo_models.FloatField(   "Float value measured for item.",
#                                        blank=True,
#                                        null=True)
#     # ArrayFields (from djongo) for string, integer and float
#
#     VALUE_ARRAY_STRING = djongo_models.ArrayField(model_container=VALUE_STR)
#     VALUE_ARRAY_INT    = djongo_models.ArrayField(model_container=VALUE_INT)
#     VALUE_ARRAY_FLOAT  = djongo_models.ArrayField(model_container=VALUE_FLOAT)
#
#     PROVENANCE  = models.CharField( "String declaring the origin of data acc. to SOURCE, incl. data locations, extration procedures, conversion techniques etc.",
#                                     max_length=256 )
#     #SOURCE      = djongo_models.CharField( "Actual data source; legal selection from declared sources in datamodel.",
#     #                                max_length=256 )
#     SOURCE      = djongo_models.ForeignKey(DatamodelSource,
#                                     to_field="Abbreviation",
#                                     on_delete=djongo_models.PROTECT )
#
#     def attrs(self):
#         """Dictionary with instance attributes."""
#         for attr, value in self.__dict__.items():
#             yield attr, value

class GeneticJson(djongo_models.Model):
    _id = djongo_models.ObjectIdField()
    data_id = djongo_models.CharField(max_length=128, unique=True)
    json_string = djongo_models.TextField()

class UserFile(models.Model):
    file = models.FileField(upload_to=settings.DATA_LOCATION)
    name = models.CharField(max_length=100)
