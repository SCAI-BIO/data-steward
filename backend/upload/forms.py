import calendar
import csv
from datetime import date, datetime
import traceback

import django_excel as excel

# from _compact import JsonResponse
from django import forms
from django.core.cache import cache
from django.core.exceptions import FieldError, EmptyResultSet
from django.db.utils import IntegrityError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from pyexcel_io import save_data
from pyexcel import get_sheet
from pyexcel_io.constants import DB_DJANGO
from pyexcel_io.database.common import DjangoModelImporter, DjangoModelImportAdapter
#from pyexcel import Sheet
from .BulkCreateManager import BulkCreateManager

date_range_global = ["1875-01-01", datetime.today().strftime('%Y-%m-%d')]
ucum_api_url = "http://ucum.nlm.nih.gov/ucum-service/v1"
from pyucum.ucum import *
import urllib
import xml.etree.ElementTree as ET
from collections import Counter

from asgiref.sync import async_to_sync 
from channels.layers import get_channel_layer

from django.conf import settings

from upload.models import (
    DatamodelSource,
    DatamodelUnit,
    DatamodelAttribute,
    DatamodelCode,
    DatamodelAttributeMapping,
    DatamodelCodeMapping,
    UserFile,
)
from upload.models import DataPoints
# from pyexcel import DjangoRenderer
from django.views.decorators.http import require_http_methods
# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages as gui_messages
from django.contrib.messages import get_messages


class DatamodelUploadFileForm(forms.Form):
    write_modes = [("new", "Drop complete datamodel before loading file"),
                   ("add", "Leave existing entries untouched, append your new ones"),
                   ]
    write_mode = forms.ChoiceField(
        choices=write_modes,
        label="Determine strategy for existing datamodel entries",
        required=True,
        initial="unique",
    )
    header_line = forms.IntegerField(
        label="Offset of header line (0 = first line in file)",
        required=True,
        initial=0,
        help_text="Please refrain from putting data above the header line...",
    )
    file = forms.FileField()


class DataUploadFileForm(forms.Form):
    source_choices = [(x.Abbreviation, x.Source) for x in DatamodelSource.objects.all()]
    source = forms.ChoiceField(
        choices=source_choices,
        label="Select the origin of your data (required for using respective mapping)",
        required=True,
        initial="None",
    )
    error_modes = [("strict", "Accept perfect data only"),
                   ("propose", "Propose corrections, but skip imperfect data"),
                   ("sanitize", "Auto-sanitize data where possible"),
                   ]
    error_mode = forms.ChoiceField(
        choices=error_modes,
        label="Determine strategy on how to treat data not perfectly matching datamodel definitions",
        required=True,
        initial="strict",
    )
    write_modes = [("sweep", "Drop complete data before loading file"),
                   ("unique", "Leave existing entries untouched"),
                   ("update", "Modify existing entries"),
                   ("add", "Accept duplicate entries"),
                   ]
    write_mode = forms.ChoiceField(
        choices=write_modes,
        label="Determine strategy for existing attributes of an entity (ID + date)",
        required=True,
        initial="unique",
    )
    min_date = forms.DateField(
        label="Earliest valid date",
        required=True,
        initial=datetime.strptime(date_range_global[0], '%Y-%m-%d'),
        help_text="Earlier date entries will be regarded as invalid",
    )
    max_date = forms.DateField(
        label="Latest valid date",
        required=True,
        initial=datetime.strptime(date_range_global[1], '%Y-%m-%d'),
        help_text="Later date entries will be regarded as invalid",
    )
    #mapping_only = forms.HiddenInput()
    mapping_only = forms.BooleanField(
        label="Use explicitly mapped variables only",
        help_text="Checked = ignore all data with no explicit mapping to datamodel.",
        required=False,
        initial=False
    )
    delim = forms.CharField(
        label="Field delimiter symbol",
        initial=';',
        help_text="Delimiters within quotes are ignored."
    )
    file = forms.FileField(
        label="Data file (EAV++ format)",
        required=True,
    )
