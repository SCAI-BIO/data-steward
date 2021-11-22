import csv
import threading
from .serializers import DataPointsVisitSerializer_light



from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated
from djongo import models as djongo_models
from django.conf import settings

from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view,  permission_classes
from rest_framework.permissions import IsAuthenticated

from random import seed
import random

from django.contrib import messages as gui_messages
from django.contrib.messages import get_messages
from django.core.files.base import ContentFile
from django.core.cache import cache

from upload.models import DataPoints, DataPointsVisit,DatamodelAttribute, DatamodelAttributeMapping, DatamodelCalculation, DatamodelCode, DatamodelCodeMapping, DatamodelSource, DatamodelUnit, UserFile

# simple libraries
import calendar
from datetime import datetime as _datetime
from datetime import date
from collections import Counter

from django.core import serializers
# custom import
from upload.BulkCreateManager import BulkCreateManager
from owlready2 import *

from django.utils.timezone import make_aware


# PyExcel
from pyexcel_io import save_data
from pyexcel import get_book
from pyexcel import get_sheet
from pyexcel_io.constants import DB_DJANGO
from pyexcel_io.database.common import DjangoModelImporter, DjangoModelImportAdapter

# UCUM
from pyucum.ucum import *
import urllib
import xml.etree.ElementTree as ET
from django.db import IntegrityError
import re
import time
import os
import traceback
import requests
#from api.views import use_token_auth, custom_permission_classes
from .models import BasicDataPoint, SemanticAsset, Measurement, MeasurementLocation, MeasurementMethod, MeasurementObject



from urllib.parse import urlencode

import pandas as pd
import editdistance

'''
Decorators for authentification

'''

WITH_AUTH = settings.WITH_AUTH

def custom_permission_classes(permission_classes):
    def decorator(func):
        if WITH_AUTH:
            func.permission_classes = permission_classes
        return func
    return decorator

def use_token_auth(func):
    def wrapper(request, *args, **kwargs):
        if WITH_AUTH:
            t = request.COOKIES.get('idsn_access_token')
            if t is None:
                print("No token found")
                return HttpResponseForbidden()
            request.META['Authorization'] = "Token " + t
        return func(request, *args, **kwargs)
    return wrapper

    


# GLOBALS

# global variables
true_replacements = [True, "True", "TRUE", "true"]
false_replacements = [False, "False", "FALSE", "false"]
date_range_global = ["1875-01-01", _datetime.today().strftime('%Y-%m-%d')]
ucum_api_url = "http://ucum.nlm.nih.gov/ucum-service/v1"
colname_map = {'Sources':            ["Abbreviation", "Source", "PID_colname",
                                      "SITE_colname", "TIMESTAMP_colname", "Header_offset"],
               'Units':              ["Unit", "UCUM", "Description"],
               'Attributes':         ["Active", "Topic", "Topic_Description", "Umbrella", "Umbrella_Description",
                                      "Attribute", "Attribute_Description", "Attribute_Tooltip",
                                      "Datatype", "Domain", "Unit"],
               'Codes':              ["Active", "Code", "Code_Description", "Key", "Value"],
               'Attribute_Mappings': ["Active", "Source", "Source_Attribute", "Target_Attribute", "Transformation"],
               'Code_Mappings':      ["Active", "Code_Mapping", "Source_Value", "Source_Value_Description",
                                      "Target_Equivalent", "Remarks"],
               'Calculations':       ["Active", "Workbench", "Source", "Attribute", "Function", "Remarks"]
               }


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# HELPER METHODS
def toe_error(msg, queue=None):
    if queue is not None:
        queue.append("ERROR: " + msg)
        return queue
    raise Exception(msg)


def toe_warning(msg, queue=None):
    if queue is not None:
        queue.append("WARNING: " + msg)
        return queue
    print("WARNING: " + msg)


def toe_info(msg, queue=None):
    if queue is not None:
        queue.append("INFO: " + msg)
        return queue
    print("INFO: " + msg)


def throw_or_enqueue(what, msg, queue=None):
    if what == "error":
        toe_error(msg, queue)
    elif what == "warning":
        toe_warning(msg, queue)
    elif what == "info":
        toe_info(msg, queue)
    else:
        raise Warning("Could not assign '" + msg +
                      "' to a valid message class!")


# helper function for handling exceptions in list comparisons
def catch(func, handle=lambda e: e, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return handle(e)


def drop_tables_data():
    DataPoints.objects.all().delete()


def drop_tables_mapping():
    drop_tables_data()
    DatamodelCalculation.objects.all().delete()
    DatamodelAttributeMapping.objects.all().delete()
    DatamodelCodeMapping.objects.all().delete()
    DatamodelSource.objects.all().delete()


def drop_tables_core():
    drop_tables_mapping()
    DatamodelAttribute.objects.all().delete()
    DatamodelCode.objects.all().delete()
    DatamodelUnit.objects.all().delete()


def get_dependency_levels_core():
    model_dependency_levels = [[DatamodelUnit],
                               [DatamodelCode],
                               [DatamodelAttribute],]
    return model_dependency_levels


def get_dependency_levels_mapping():
    model_dependency_levels = [[DatamodelSource],
                               [DatamodelCodeMapping],
                               [DatamodelAttributeMapping],
                               [DatamodelCalculation],
                               ]
    return model_dependency_levels


def get_header_indices(act_colnames, exp_colnames, main_msg_queue):
    indices = {n: catch(lambda: act_colnames.index(n)) for n in exp_colnames}
    #indices = {n: catch(lambda: act_colnames.index(exp_colnames[n])) for n in exp_colnames}
    misses = [re.findall('\'([^\']*)\'', miss.args[0])[0] for miss in indices.values() if
              miss.__class__ is ValueError]
    if misses:
        msg = "Could not find following column headers (format corrupt?):\n" + "\n".join(
            misses)
        throw_or_enqueue("error", msg, main_msg_queue)
        return False
    return indices


def get_bool_fields(model):
    return [f.name for f in model._meta.fields if f.__class__.__name__ == 'BooleanField']


def get_char_fields(model):
    return [f.name for f in model._meta.fields if f.__class__.__name__ == 'CharField']


def get_relations(model):
    return [f for f in model._meta.fields if f.is_relation]


# checks on numerical values, mainly dedicated to def check_domain

def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def lossless_float2int(numstring, main_msg_queue):
    if numstring.count(".") == 1:
        integer, decimal = numstring.split(".")
        if represents_int(integer):
            if not decimal or (represents_int(decimal) and int(decimal) == 0):
                msg = "Converted '" + numstring + \
                    "' to integer '" + integer + "' (lossless)"
                throw_or_enqueue("warning", msg, main_msg_queue)
                return integer
    msg = "Could not convert float value to integer number: " + numstring
    throw_or_enqueue("error", msg, main_msg_queue)
    return False


def check_int_array_and_sanitize(str_int, main_msg_queue):
    int_range_pattern = re.compile("(^(-?\d)?\d*:(-?\d)?\d*$)|(^(-?\d)?\d*$)")
    elements = str_int.split(",")
    misfits = [i for i in range(len(elements))
               if not int_range_pattern.match(elements[i])]
    for m in misfits:
        x = elements[m].split(":")
        if len(x) > 2:
            return False
        try:
            elements[m] = ":".join([str(f) for f in [lossless_float2int(
                x[i], main_msg_queue) if x[i] else "" for i in range(len(x))]])
        except ValueError:
            return False
    return ",".join(elements)


def check_float_array_and_sanitize(str_float):
    float_range_pattern = re.compile(
        "(^(-\d+)|(\d+)\.\d+$)|(^((-\d+)|(\d+)\.\d+)?:((-\d+)|(\d+)\.\d+)?$)")
    elements = str_float.split(",")
    misfits = [i for i in range(len(elements))
               if not float_range_pattern.match(elements[i])]
    for m in misfits:
        x = elements[m].split(":")
        if len(x) > 2:
            return False
        try:
            elements[m] = ":".join(
                [str(f) for f in [float(x[i]) if x[i] else "" for i in range(len(x))]])
        except ValueError:
            return False
    return ",".join(elements)


# checks on date values

def sanitize_date(d, main_msg_queue):
    # remove time stamp
    old = d
    try:
        d = re.compile("[0-9][0-9]:[0-9][0-9]:[0-9][0-9]").sub("", d)
    except TypeError:
        print(d)
    if not d == old:
        msg = "Removed timestamp from date."
        throw_or_enqueue("warning", msg, main_msg_queue)

    # remove leading/trailing spaces
    old = d
    d = d.strip()
    if not len(old) == len(d):
        msg = "Removed leading/trailing whitespaces."
        throw_or_enqueue("warning", msg, main_msg_queue)

    # if dot "." as separator: apply dash "-"
    old = d
    d = d.replace(".", "-")
    if not d == old:
        pass
        # gui_messages.info(request, "Replaced '.' with correct separators '-'.") ?? TODO SEBASTAIN FRAGEN

    # remove leading/trailing separators
    old = d
    d = d.strip("-")
    if not len(old) == len(d):
        msg = "Removed dangling separators."
        throw_or_enqueue("warning", msg, main_msg_queue)

    # for incomplete dates: add "00" blocks as placeholder
    dash_cnt = d.count("-")
    if dash_cnt == 1:
        # messages.warning("Incomplete date - added day field '00'")
        # trailing month in template (preferred)
        if re.compile("^[0-9][0-9][0-9][0-9]-[0-9][0-9]").match(d):
            msg = "Incomplete date - added day field '00'"
            throw_or_enqueue("warning", msg, main_msg_queue)
            return d + "-00"
        # leading month in template (to be corrected later)
        elif re.compile("^[0-9][0-9]-[0-9][0-9][0-9][0-9]").match(d):
            msg = "Incomplete date - added day field '00'"
            throw_or_enqueue("warning", msg, main_msg_queue)
            return "00-" + d
        else:
            msg = "Invalid partial date pattern: '" + d + "'"
            throw_or_enqueue("error", msg, main_msg_queue)
            return False
    elif dash_cnt == 0:
        msg = "Incomplete date - added day and month fields '00'"
        throw_or_enqueue("warning", msg, main_msg_queue)
        return d + "-00-00"
    elif dash_cnt != 2:
        msg = "Inadequate number of separators (" + str(dash_cnt) + ") found!"
        throw_or_enqueue("error", msg, main_msg_queue)
        return False
    else:
        return d


def reverse_date(d):
    return "-".join(reversed(d.split("-")))


def check_date_pattern(d, sanitize, main_msg_queue):
    pat_msg = "'YYYY-MM-DD' required, with '00' legal for 'DD' and 'MM'"
    pattern = re.compile("^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$")
    if pattern.match(d):
        return d
    elif not sanitize:
        return False

    rev_d = reverse_date(d)
    if pattern.match(rev_d):
        msg = "Reversed date sequence - " + pat_msg
        throw_or_enqueue("warning", msg, main_msg_queue)
        return rev_d

    if re.compile("^[0-9][0-9]-").match(d):
        msg = "No valid date pattern! (presumably two-digit YEAR expression - " + pat_msg + ")"
        throw_or_enqueue("warning", msg, main_msg_queue)
        return False
    elif re.compile("^[0-9][0-9][0-9][0-9]-[0-9]-[0-9][0-9]$").match(d):
        msg = "No valid date pattern! (presumably single-digit MONTH expression - " + pat_msg + ")"
        if not sanitize:
            throw_or_enqueue("error", msg, main_msg_queue)
            return False
    elif re.compile("^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9]$").match(d):
        # gui_messages.info(request, "") ??? TODO SEBASTIAN FRAGEN
        msg = "No valid date pattern! (presumably single-digit DAY expression - " + pat_msg + ")"
        if not sanitize:
            throw_or_enqueue("error", msg, main_msg_queue)
            return False
    elif re.compile("^[0-9][0-9][0-9][0-9]-[0-9]-[0-9]$").match(d):
        msg = "No valid date pattern! (presumably single-digit MONTH and DAY expression - " + pat_msg + ")"
        if not sanitize:
            throw_or_enqueue("error", msg, main_msg_queue)
            return False

    #throw_or_enqueue("warning", msg, main_msg_queue)
    year, month, day = d.split("-")
    if len(month) == 1:
        month = "0" + month
    if len(day) == 1:
        day = "0" + day

    # recursion (effectively single iteration)
    d = check_date_pattern(year + "-" + month + "-" +
                           day, False, main_msg_queue)

    if d:
        msg = "Sanitized invalid date format."
        throw_or_enqueue("warning", msg, main_msg_queue)
        return d
    msg = "No valid date pattern! (attempts to sanitize failed)"
    throw_or_enqueue("error", msg, main_msg_queue)
    return False


def calculate_date_object(d):
    year, month, day = d.split("-")
    return date(int(year), int(month), int(day))


def fit_00_date_vs_range(d, date_range, main_msg_queue):
    year, month, day = d.split("-")  # pattern YYYY-MM-DD ensured here

    msg = "Date '" + d + \
        "' out of accepted range! ('" + "' to '".join(date_range) + "')"
    if int(month) * int(day):  # both values are unequal zero - fully python-valid date format
        if not calculate_date_object(date_range[0]) <= calculate_date_object(d) <= calculate_date_object(date_range[1]):
            throw_or_enqueue("error", msg, main_msg_queue)
            return False
        else:
            return d

    # day and/or month are zero'd - check year match first
    if not int(date_range[0][0:4]) <= int(year) <= int(date_range[1][0:4]):
        throw_or_enqueue("error", msg, main_msg_queue)
        return False

    if not int(month):
        month_min = "12"
        month_max = "01"
    else:
        month_min = month_max = month

    if not int(day):
        date_min = year + "-" + month_min + "-" + \
            str(calendar.monthrange(int(year), int(month_max))[1]).zfill(2)
        date_max = year + "-" + month_max + "-01"
    else:
        date_min = year + "-" + month_min + "-" + day
        date_max = year + "-" + month_max + "-" + day

    if calculate_date_object(date_range[0]) <= calculate_date_object(date_min):
        if calculate_date_object(date_max) <= calculate_date_object(date_range[1]):
            return d

    throw_or_enqueue("error", msg, main_msg_queue)
    return False


# date: central access
def check_date(d, main_msg_queue, sanitize=False, date_range=date_range_global):
    # expected pattern: YYYY-MM-DD

    # sanitize?
    if sanitize:
        d = sanitize_date(d, main_msg_queue)
        if not d:
            return False

    # test character set
    if not re.compile("^(\d+(?:-\d+)*)$").match(d):
        msg = "Illegal characters in date detected."
        throw_or_enqueue("error", msg, main_msg_queue)
        return False

    # check pattern
    d = check_date_pattern(d, sanitize, main_msg_queue)
    if not d:
        return False

    # check plausible ranges
    year, month, day = d.split("-")
    if not 0 <= int(day) <= 31:
        msg = "Invalid day value (" + str(day) + ")!"
        throw_or_enqueue("error", msg, main_msg_queue)
        d = False
    if not 0 <= int(month) <= 12:
        msg = "Invalid month value (" + str(month) + ")!"
        throw_or_enqueue("error", msg, main_msg_queue)
        d = False

    if d:
        d = fit_00_date_vs_range(d, date_range, main_msg_queue)

    return d


def check_date_array_and_sanitize(str_date, main_msg_queue):
    elements = [r.strip() for r in str_date.split(",")]
    # corrected = []
    error_flag = False
    for i in range(len(elements)):
        x = elements[i].split(":")
        if len(x) > 2:
            return False
        try:
            tmp = [str(f) for f in [check_date(x[j], main_msg_queue,  date_range=date_range_global,
                                               sanitize=True) if x[j] else "" for j in range(len(x))]]
            if calculate_date_object(tmp[0]) > calculate_date_object(tmp[1]):
                msg = "'" + str_date + "' => 'from' date greater than 'to' date in date range!"
                throw_or_enqueue("error", msg, main_msg_queue)
                error_flag = True
            elements[i] = ":".join(tmp)
        except ValueError:
            return False
    if error_flag:
        return False
    return ",".join(elements)


def prepare_sheet(sheet, main_msg_queue, sheet_name):

    # Check header (sequence of expected columns might differ)
    indices = get_header_indices(
        sheet.colnames, colname_map[sheet_name], main_msg_queue)
    if not indices:
        msg = "Corrupt header line for '" + sheet_name + \
            "' - please check log for details."
        throw_or_enqueue("error", msg, main_msg_queue)
        return False  # DIESER FALL WIRD NICHT ABGEFANGEN, WENN DIE METHODE GECALLED WIRD

    # Remove unused COLUMNS
    delete_columns = [i for i in range(
        sheet.number_of_columns()) if not sheet.colnames[i] in indices]
    column_mapper = [i for i in range(
        sheet.number_of_columns()) if i not in delete_columns]
    sheet.delete_columns(delete_columns)

    # Index ROWS with Active = FALSE, if given
    inactive_rows = []
    if "Active" in sheet.colnames:
        active_col = sheet.column["Active"]
        inactive_rows = [i for i in range(sheet.number_of_rows()) if active_col[i] in [
            0] + false_replacements]

    # Index blank ROWS
    blank_rows = [i for i in range(
        sheet.number_of_rows()) if blank_row(i, sheet.row[i])]

    # Remove blank and inactive ROWS from sheet
    # ToDo: report inactive lines as infos, blank lines as warnings
    delete_rows = inactive_rows + blank_rows  # no overlap of lists possible...
    row_mapper = [i for i in range(
        sheet.number_of_rows()) if i not in delete_rows]
    sheet.delete_rows(delete_rows)
    # print("HALLOHALLO")
    return sheet, row_mapper, column_mapper

# check column for compliance with model's respective field


def check_regular_field_compliance(colname, sheet, model, fault_collector, main_msg_queue):
    col = sheet.column[colname]
    field = model._meta.get_field(colname)
    bool_fields = get_bool_fields(model)
    char_fields = get_char_fields(model)

    # general: blank AND blank allowed?
    if not (field.blank and field.null) and field._get_default() is None:
        fault_collector[colname]["blank"] = [
            i for i in range(len(col)) if col[i] == ""]

    # boolean fields: convertable?
    if colname in bool_fields:
        msg_base = "Column '" + colname + "' expected to be either TRUE or FALSE - "
        colset = set([str(y) for y in col])
        diff = colset.difference(["0", "1"])
        if diff:  # contents not read from regular Excel bool cells - try adequate values
            throw_or_enqueue("warning", msg_base + "found '" +
                             "', '".join(diff) + "'", main_msg_queue)
            replaced_true = [1 if x in true_replacements else x for x in col]
            replaced_false = [
                0 if x in false_replacements else x for x in replaced_true]
            diff_again = set(replaced_false).difference(["0", "1"])
            if diff_again:  # replacement failed - refuse
                throw_or_enqueue("error", msg_base + "could not sanitize value(s) '" +
                                 "', '".join(diff) + "'", main_msg_queue)
                fault_collector[colname]["bools"] = [i for i in range(len(replaced_false)) if
                                                     replaced_false[i] in diff_again]
            else:  # replacement successful - exchange column
                sheet.column[colname] = replaced_false

    # choices fields: in scope?
    choices = field.choices
    if choices:
        fault_collector[colname]["choices"] = [i for i in range(len(col)) if
                                               col[i] not in [t[0] for t in choices]]
        if fault_collector[colname]["choices"]:
            fields = "\n  ".join([entry[0] + ": " + entry[1]
                                  for entry in field.choices])
            throw_or_enqueue("error", "Values for column '" + colname +
                             "' exceed range of allowed choices:\n" + fields, main_msg_queue)

    # character fields: type casted? Leading/trailing whitespaces? Length?
    if colname in char_fields:
        #print(colname)

        flag = False
        for i in range(len(col)):
            if col[i].__class__.__name__ != "str":
                col[i] = str(col[i])
                flag = True
        if flag:
            sheet.column[colname] = col

        col = [cell.strip(" ") for cell in sheet.column[colname]]
        if not sheet.column[colname] == col:
            sheet.column[colname] = col
            msg = "Removed useless leading/trailing whitespace characters from column '" + colname + "'"
            throw_or_enqueue("warning", msg, main_msg_queue)

        fault_collector[colname]["length"] = [
            i for i in range(len(col)) if len(col[i]) > field.max_length]
        if fault_collector[colname]["length"]:
            msg = "Values for column '" + str(colname) + \
                "' exceed maximum string length of " + str(field.max_length)
            throw_or_enqueue("error", msg, main_msg_queue)


# check column for uniqueness, if required by model's respective field
def check_uniqueness_for_column(colname, sheet, model, fault_collector, main_msg_queue):
    if colname == model._meta.pk.name or model._meta.get_field(colname)._unique:
        # check duplicates locally in column
        col = sheet.column[colname]
        c = Counter(col)
        duplicates = [item for item in c.keys() if c[item] > 1]
        fault_collector[colname]["duplicate"] = [
            i for i in range(len(col)) if col[i] in duplicates]
        if fault_collector[colname]["duplicate"]:
            msg = "Found duplicate entries in column '" + \
                colname + "' (unique required)"
            throw_or_enqueue("error", msg, main_msg_queue)
        # check versus existing DB objects
        existing = model.objects.values_list(colname, flat=True)
        fault_collector[colname]["assigned"] = [
            i for i in range(len(col)) if col[i] in existing]
        if fault_collector[colname]["assigned"]:
            msg = "Found entries in column '" + colname + \
                "' already assigned in database (unique required)."
            throw_or_enqueue("error", msg, main_msg_queue)

# Tests, whether declarations of (type-dependent) domains are correct


def check_domain(colname, sheet, codes, fault_collector, main_msg_queue):
    # get rid off useless blanks and (allowed) brackets
    col = [cell.strip(" []") for cell in sheet.column[colname]]
    if not col == sheet.column[colname]:
        sheet.column[colname] = col
        msg = "Removed useless leading/trailing whitespace characters from column '" + colname + "'"
        throw_or_enqueue("warning", msg, main_msg_queue)
    datatypes = sheet.column["Datatype"]
    fault_collector[colname]["domain"] = []
    db_codes = list(DatamodelCode.objects.values_list("Code", flat=True))
    all_codes = db_codes + codes

    for i in range(len(col)):
        if not len(col[i]):
            continue  # Domain is optional... if empty: skip

        # integer tests
        if datatypes[i] in ["int", "array(int)"]:
            corr = check_int_array_and_sanitize(col[i], main_msg_queue)
            if corr:
                if not col[i] == corr:
                    msg = "Found float values or whitespace chars in domain declaration of an integer-type variable."
                    throw_or_enqueue("warning", msg, main_msg_queue)
                    col[i] = corr
            else:
                fault_collector[colname]["domain"].append(i)
            continue

        # float tests
        if datatypes[i] in ["float", "array(float)"]:
            corr = check_float_array_and_sanitize(col[i])
            if corr:
                if not col[i] == corr:
                    msg = "Found integer values or whitespace chars in domain declaration of a float-type variable."
                    throw_or_enqueue("warning", msg, main_msg_queue)
                    col[i] = corr
            else:
                fault_collector[colname]["domain"].append(i)
            continue

        # code tests
        if datatypes[i] in ["code", "array(code)"]:
            corr = [r.strip() for r in col[i].split(",")]
            if not ",".join(corr) == col[i]:
                msg = "Removed unnecessary whitespaces in codes list."
                throw_or_enqueue("warning", msg, main_msg_queue)
                col[i] = corr
            misfits = [r for r in col[i].split(",") if r not in all_codes]
            if misfits:
                msg = "Found unknown codes referenced: '" + "', '".join(misfits) + "'"
                throw_or_enqueue("error", msg, main_msg_queue)
                fault_collector[colname]["domain"].append(i)
            continue

        # date tests
        if datatypes[i] in ["date", "array(date)"]:
            corr = check_date_array_and_sanitize(col[i], main_msg_queue)
            if corr:
                if not col[i] == corr:
                    msg = "Found sub-optimal formatting in domain declaration of a date-type variable."
                    throw_or_enqueue("warning", msg, main_msg_queue)
                    col[i] = corr
            else:
                fault_collector[colname]["domain"].append(i)
            continue

    # if datatypes[i] == "string" and not array_float_array_pattern.match(col[i]):
    if not col == sheet.column[colname]:
        sheet.column[colname] = col
        msg = "Sanitized entries in column '" + colname + "'"
        throw_or_enqueue("warning", msg, main_msg_queue)


# get rid of empty sheet rows
def blank_row(row_index, row):
    result = [element for element in row if element != '']
    return len(result) == 0


# helper; determines whether issues have been recorded
def get_error_flag(fault_collector, colname):
    if [error for error in fault_collector[colname].keys() if fault_collector[colname][error]]:
        return True
    else:
        return False

# check foreign key columns: string referencing correct (existing) key?


def check_foreign_keys(colname, sheet, model, local_fault_collector, data_collector):
    relations = get_relations(model)
    if colname in [r.name for r in relations]:
        # database entries: simple query on related model instances
        pos = [r.name for r in relations].index(colname)
        distmodel = relations[pos].related_model
        distfield = relations[pos].to_fields[0]
        db_keys = list(distmodel.objects.values_list(distfield, flat=True))

        # sheet entries (for dependency levels > 1)
        # extract from data collector; browse previously stored, lower dependency level sheets
        sheet_keys = []
        distmodel_name = distmodel._meta.model.__name__.lower()
        #print("calculating sheet keys \n \n")
        if distmodel_name in data_collector:
            #print(f"calculating sheet keys with: {distmodel_name}")
            colpos = data_collector[distmodel_name].colnames.index(distfield)
            #print(f"calculating sheet keys with: {colpos}")
            sheet_keys.extend([row[colpos]
                               for row in data_collector[distmodel_name]])
        else:
            pass
            #print(f"NOT FOUND IN COLLECTOR: {distmodel_name} \n")
            #print(f"DATA COLLECTOR: {data_collector} \n")

        col = sheet.column[colname]
        #print(f"DB KEYS : {db_keys}")
        #print(f"SHEET KEYS : {sheet_keys}")
        all_keys = set(db_keys + sheet_keys)
        #print(f"ALL KEYS : {all_keys}")
        #print(set(col))
        if not set(col).issubset(all_keys):  # unknown foreign key referenced
            local_fault_collector[colname]["foreignkey"] = [
                i for i in range(len(col)) if col[i] not in all_keys]
        #for cell in [i for i in range(len(col)) if col[i] not in all_keys]:
        #    print(cell)

# Setup containers for sheet/model
def fill_import_containers(importer, data_collector, model, sheet):
    # generate import adapter from model
    adapter = DjangoModelImportAdapter(model)
    # print(sheet.colnames)
    adapter.column_names = sheet.colnames
    print(adapter.column_names)

    print(adapter)

    # add adapter to importer (= queue for current dependency level)
    importer.append(adapter)

    # feed data collector struct with sheet-derived data
    # data_collector[adapter.get_name()] = sheet.get_internal_array()
    data_collector[adapter.get_name()] = sheet


# float
def floatable(x, main_msg_queue, sanitize=False):
    if sanitize:
        value = x.replace(",", ".")
        if value != x:
            throw_or_enqueue("warning", "Converted floating point symbol in '" +
                             x + "' (German notation ',' found!).", main_msg_queue)
            x = value
    try:
        return float(x)
    except ValueError as e:
        return False


# float
def advanced_string2float(string, refU_obj, main_msg_queue, verified_UCUM_units={}, value_conversions={}):
    string = consider_unit_and_convert(
        string, refU_obj, verified_UCUM_units, value_conversions)
    num = floatable(string, main_msg_queue)
    if not num:
        throw_or_enqueue(
            "error", "Could not convert value to integer number: '" + string, main_msg_queue)
    return num


# code
def check_codekey_matches(values, target_code, main_msg_queue, sanitize=False):
    target_keys = set(DatamodelCode.objects.filter(
        Code=target_code).values_list("Key", flat=True))
    if not target_keys:
        throw_or_enqueue("error", "Could not find code system '" +
                         target_code + "'", main_msg_queue)
        return False
    try:
        diff = set(values).difference(target_keys)
    except KeyError:
        diff = True
    if diff:
        if sanitize:
            fail = []
            success = []
            sanitized = []
            for item in list(values):
                try_hard = str(advanced_string2int(item, main_msg_queue))
                if try_hard in target_keys:
                    success.append(try_hard)
                    if item != try_hard:
                        sanitized.append(item)
                else:
                    fail.append(item)
            if fail:
                msg = "Found key(s) '" + ", ".join(fail) + "' being incompatible to code system '"\
                      + target_code + \
                    "' (not in [" + ", ".join(sorted(target_keys)) + "])"
                throw_or_enqueue("error", msg, main_msg_queue)
                return False
            msg = "Key(s) '" + ", ".join(sanitized) + "' had to be sanitized in order to be compatible to code system '"\
                  + target_code + "'"
            throw_or_enqueue("warning", msg, main_msg_queue)
            return values.__class__(success)
        msg = "Found key(s) '" + ", ".join(values) + "' being incompatible to code system '"\
              + target_code + \
            "' (not in [" + ", ".join(sorted(target_keys)) + "])"
        throw_or_enqueue("error", msg, main_msg_queue)
        return False
    return values


# num + unit
def consider_unit_and_convert(var, refU_obj, main_msg_queue,  verified={}, conversions={}):
    value, unit = separate_value_and_unit(var)

    if not value:  # errornous outputs
        return False

    if not unit:  # no unit detected, keep value as is
        return value

    refU = refU_obj.Unit

    # check if reference or not (yes = no action required)
    if unit == refU:
        return value

    # verify UCUM membership (automated conversion is yet possible for those only!)
    if refU_obj.UCUM:
        return convert_using_UCUM(value, unit, refU, verified, conversions)
    else:
        throw_or_enqueue("error", "Auto-conversion from '" + unit + "' to '" + refU
                         + "' unavailable (no UCUM units).)", main_msg_queue)
        return False


# integer
def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# integer
def lossless_float2int(numstring, main_msg_queue):
    if numstring.count(".") == 1:
        integer, decimal = numstring.split(".")
        if represents_int(integer):
            if not decimal or (represents_int(decimal) and int(decimal) == 0):
                throw_or_enqueue("warning", "Converted '" + numstring +
                                 "' to integer '" + integer + "' (lossless)", main_msg_queue)
                return integer
    throw_or_enqueue(
        "error", "Could not convert float value to integer number: " + numstring, main_msg_queue)
    return False


# integer
def advanced_string2int(string, main_msg_queue, refU_obj=None, verified_UCUM_units={}, value_conversions={}):
    if "," in string:
        string = string.replace(",", ".")
        throw_or_enqueue("warning", "Converted '" + string +
                         "' to international decimal '.'!", main_msg_queue)

    if "." in string:
        string_ = lossless_float2int(string, main_msg_queue)
        if not string_:
            throw_or_enqueue(
                "error", "Could not convert value to integer number: " + string, main_msg_queue)
            return False
        string = string_

    if refU_obj and not refU_obj.Unit == "None":
        string = consider_unit_and_convert(
            string, refU_obj, main_msg_queue, verified_UCUM_units, value_conversions)
        if not string:
            throw_or_enqueue(
                "error", "Could not convert value to integer number: " + string, main_msg_queue)
            return False

    try:
        return int(string)
    except ValueError:
        return False


# num (both integer and float)
def check_num_domain_fit(var_num, domain, type, main_msg_queue):
    for subdomain in array_from_string(domain):
        leftfit = rightfit = True
        elements = subdomain.split(":")

        if len(elements) > 2:
            return False
        elif len(elements) == 2:
            if len(elements[0]):
                if type == "int":
                    left = int(elements[0])
                elif type == "float":
                    left = float(elements[0])
            else:
                left = False
            if len(elements[1]):
                if type == "int":
                    right = int(elements[1])
                elif type == "float":
                    right = float(elements[1])
            else:
                right = False
        else:
            left = right = elements[0]
        if left and var_num < left:
            leftfit = False
        if right and var_num > right:
            rightfit = False
        if leftfit and rightfit:
            return var_num
    throw_or_enqueue("error", "'" + str(var_num) +
                     "' exceeds value range of defined domain: " + str(domain), main_msg_queue)
    return False


# date
def check_date_domain_fit(var_date, domain, main_msg_queue):
    # domain = two-item array of dates
    if domain[0] and var_date < domain[0]:
        throw_or_enqueue("error", "'" + str(var_date) +
                         "' exceeds date range: < " + str(domain[0]), main_msg_queue)
        return False
    if domain[1] and var_date > domain[1]:
        throw_or_enqueue("error", "'" + str(var_date) +
                         "' exceeds date range: > " + str(domain[1]), main_msg_queue)
        return False
    return True


# array of elements from formatted string
def array_from_string(instring, delim=",", convert="string"):
    #cont = (instring.split("["))[1].split("]")[0]
    if convert == "int":
        return [int(x) for x in instring.split(delim)]
    elif convert == "float":
        return [float(x) for x in instring.split(delim)]
    elif convert == "string":
        return instring.split(delim)
    else:
        return False


# two-item array of elements ('domain' as from/to pairing)
def domain_from_string(instring, generic_from=False, generic_to=False):
    fr, to = array_from_string(instring)

    if not fr and generic_from:
        fr = generic_from
    if not to and generic_to:
        to = generic_to
    return fr, to


# num + unit
def separate_value_and_unit(var, main_msg_queue):
    var = re.sub(r"\s", "", var)
    value = "".join(re.findall(r"[\d.]", var))
    try:
        startpos = var.index(value)
        if startpos == 0:
            unit = var[(len(value)):]
            return value, unit
        else:
            return False, False
    except ValueError as e:
        msg = "No valid number, even considering trailing unit declarations: " + var
        throw_or_enqueue("error", msg, main_msg_queue)
        return False, False


# num + unit
def UCUM_server_reply2dict(reply):
    d = dict()
    for r in reply:
        u, v = r.split(" = ")
        if v == "true":
            d[u] = True
        elif v == "false":
            d[u] = False
        else:
            d[u] = v
    return d


# num + unit
def verify_units2UCUM(actual_unit, reference_unit, main_msg_queue, buffer_dict={}):
    call = [x for x in [actual_unit, reference_unit] if x not in buffer_dict]
    if not call:
        return {}
    reply = ucumVerify(call, ucum_api_url)
    reply_dict = UCUM_server_reply2dict(reply)
    if not reference_unit in buffer_dict and not reference_unit in reply_dict:
        throw_or_enqueue(
            "error", "Could not resolve reference unit in UCUM!", main_msg_queue)
        return False
    elif actual_unit in buffer_dict and not actual_unit in reply_dict:
        throw_or_enqueue(
            "error", "Could not resolve reference unit in UCUM!", main_msg_queue)
        return False
    else:
        return reply_dict


# num + unit
def generate_conversion_api_urls(actual_unit, reference_unit, value=1):
    collector = {}
    if isinstance(actual_unit, list) or isinstance(reference_unit, list):
        if len(actual_unit) != len(reference_unit):
            return False
        else:
            for i in range(0, len(actual_unit)):
                collector.update(generate_conversion_api_urls(
                    actual_unit[i], reference_unit[i]))
    else:
        url = ucum_api_url + "/ucumtransform"
        request = url + "/" + str(value) + "/from/" + \
            actual_unit + "/to/" + reference_unit
        request.replace("//", "/")
        collector[actual_unit + "=>" + reference_unit] = request
    return collector


# num + unit
def get_responses_from_UCUM(actU, refU, value):
    urls = generate_conversion_api_urls(actU, refU, value)
    responses = {}
    for conv in urls.keys():
        # request = urls['g/l=>g/dL']
        request = urls[conv]
        try:
            with urllib.request.urlopen(request) as res:
                context = ET.fromstring(res.read())
                # print(context)
                for child in context:
                    tmp1 = {}
                    if child.text == None:
                        for element in child:
                            # print(element.tag)
                            tmp1[element.tag] = element.text
                            # print(child, tmp1)
                    elif child.text != None:  # error handling ERROR: unexpected result: Invalid UCUM Transformation Expression
                        # print(child.text)
                        tmp1["ERROR"] = child.text
        except urllib.error.HTTPError as e:  # error handling bad request
            tmp1["ERROR"] = e
        responses[conv] = tmp1
    return responses


# num + unit
def convert_using_UCUM(value, actU, refU, main_msg_queue,  verified={}, conversions={}):
    reply = verify_units2UCUM(actU, refU, verified, main_msg_queue)
    if reply is False:
        return False
    verified.update(reply)

    # conversion (for UCUM units)
    try:
        if verified[actU] and verified[refU]:
            conv = actU + "=>" + refU
            rev_conv = refU + "=>" + actU
            if conv in conversions:
                # use 'conversions' dict for calculating the VALUE according to the reference UNIT
                value = str(float(value) * conversions[conv])
            elif rev_conv in conversions:
                # reverse available conversion
                value = str(float(value) / conversions[rev_conv])
            else:
                # query UCUM server API for factor
                responses = get_responses_from_UCUM(actU, refU, value)
                value = responses[conv]['ResultQuantity']
                factor = float(responses[conv]['ResultQuantity']) / \
                    float(responses[conv]['SourceQuantity'])
                conversions[conv] = factor
            return value
        else:
            msg = "Auto-conversion from '" + actU + "' to '" + refU + \
                "' unavailable (could not verify using UCUM server)."
            throw_or_enqueue("error", msg, main_msg_queue)
    except KeyError as e:
        throw_or_enqueue(
            "error", "An error occured while trying to convert a UCUM unit...", main_msg_queue)

    return False

# convert_using_UCUM("2", "d", "s")   # True
# convert_using_UCUM("2", "x", "s")   # False

# general entry point for deep tests on all available data types (except 'code')
# TODO: enable transformations (^)
# TODO: in data main(), transform input values into target space by source (no mapping/source information necessary to hand in here)


def ensure_datatype_and_domain_fit(values, target, main_msg_queue, date_range=date_range_global,
                                   sanitize=False, verified_UCUM_units={}, value_conversions={}):
    sanitized = False

    for i in range(len(values)):
        var = values[i]
        c = list()
        #print(var)
        #print(target)
        #print(target.Datatype)
        if target.Datatype in ["int", "array(int)"]:
            for v in array_from_string(var):
                try:
                    var_int = int(v)
                except ValueError:
                    print("fail")
                    if sanitize:
                        var_int = advanced_string2int(
                            v, main_msg_queue, target.Unit, verified_UCUM_units, value_conversions)
                        sanitized = True
                    else:
                        throw_or_enqueue(
                            "error", "Could not convert value to integer number: " + v, main_msg_queue)
                        var_int = False
                if var_int is not False and target.Domain:
                    var_int = check_num_domain_fit(
                        var_int, target.Domain, "int", main_msg_queue)
                if var_int is not False:
                    c.append(str(var_int))
                else:
                    c.append(var_int)

        elif target.Datatype in ["float", "array(float)"]:
            for v in array_from_string(var):
                try:
                    var_float = float(v)
                    if not str(var_float) == v:
                        sanitized = True
                        msg = "Found integer number ('" + \
                            v + "') where float expected"
                        if not sanitize:
                            var_float = False
                            throw_or_enqueue("error", msg, main_msg_queue)
                        else:
                            throw_or_enqueue("warning", msg, main_msg_queue)
                except ValueError:
                    if sanitize:
                        var_float = advanced_string2float(
                            var, target.Unit, main_msg_queue,  verified_UCUM_units, value_conversions)
                        sanitized = True
                    else:
                        throw_or_enqueue(
                            "error", "Could not convert value to float number: " + var, main_msg_queue)
                        var_float = False
                if var_float is not False and target.Domain:
                    var_float = check_num_domain_fit(
                        var_float, target.Domain, "float", main_msg_queue)
                if var_float is not False:
                    c.append(str(var_float))
                else:
                    c.append(var_float)

        elif target.Datatype in ["date", "array(date)"]:
            if target.Domain:
                ddomain = [datetime.strptime(
                    x, '%Y-%m-%d') if x else False for x in domain_from_string(target.Domain)]
            for v in array_from_string(var):
                v_ = check_date(v, main_msg_queue,
                                date_range=date_range, sanitize=sanitize)
                if v_:
                    if v != v:
                        throw_or_enqueue(
                            "warning", "Had to sanitize date statement: " + v + " => " + v_, main_msg_queue)
                        v = v_
                    if target.Domain and not check_date_domain_fit(datetime.strptime(v, '%Y-%m-%d'), ddomain, main_msg_queue):
                        v = False
                else:
                    v = False
                if v:
                    c.append(str(v))
                else:
                    c.append(v)

        elif target.Datatype in ["code", "array(code)"]:
            #key_map = {m.Source_Value: m.Target_Equivalent for m in
            #            DatamodelCodeMapping.objects.filter(Code_Mapping=target.Transformation)}
            for v in array_from_string(var):
                v_ = check_codekey_matches(
                    v, target.Domain, main_msg_queue,  sanitize=sanitize)
                if v_ is not False:
                    if v != v:
                        throw_or_enqueue(
                            "warning", "Had to sanitize code key: " + v + " => " + v_, main_msg_queue)
                        v = v_
                else:
                    v = False
                if v:
                    c.append(str(v))
                else:
                    c.append(v)

        elif target.Datatype in ["string", "array(string)"]:
            pass

        else:
            throw_or_enqueue("error", "Test for data model variable type '" +
                             target.Datatype + "' is not implemented.", main_msg_queue)
            c.append(False)

        if False not in c:
            values[i] = ",".join(c)
        else:
            values[i] = False

    if False in values:
        return False, sanitized

    return values, sanitized


def prettyprint_formula(p, operators):
    #p = " 1/( CERAD_WLLSUM_R+1 - 8)"
    for o in operators:
        p = re.sub(r'%s' % re.escape(o), r' %s ' % o, p)
    p = re.sub('\( ', '(', p)
    p = re.sub(' \)', ')', p)
    p = ' '.join(p.split())
    return(p)


# 'pattern' parameter for development only!
def check_formula(t, main_msg_queue,  restrict=[]):
    return t
    functions = ["FORMULA", "MEAN", "RANK", "SUM",
                 "DELTA", "DIV", "PROD", "DRANGE", "DATE", "VALID_IF", "ANY", "IF"]
    operators = ["+", "-", "/", "*", "%", "^"]  # , "(", ")"]

    left_bracket = False
    right_bracket = False
    #print("==> '" + t + "'")
    r = t.strip()
    if not r == t:
        t = r
        throw_or_enqueue(
            "warning", "Removed leading/trailing whitespaces from formula.", main_msg_queue)

    error_flag = False
    try:
        left_bracket = t.index("(")
    except ValueError:
        error_flag = True
        throw_or_enqueue(
            "error", "No opening bracket in formula.", main_msg_queue)
    try:
        right_bracket = t.rindex(")")
    except ValueError:
        error_flag = True
        throw_or_enqueue(
            "error", "No closing bracket in formula.", main_msg_queue)

    if not right_bracket == len(t) - 1:
        error_flag = True
        throw_or_enqueue(
            "error", "Formula declaration does not end with closing bracket.", main_msg_queue)
    function = t[:left_bracket]
    if not function in functions:
        error_flag = True
        if not function:
            msg = "Formula declaration does not start with any function call."
        else:
            msg = "Formula declaration does not start with any known function call - found '" + function + "'..."
        throw_or_enqueue("error", msg, main_msg_queue)

    if error_flag:
        msg = "Could not parse a valid formula following scheme 'FUNCTION(parameters | math expr.)'', with FUNCTION out of " \
            + "['" + "', '".join(functions) + "']" + "."
        throw_or_enqueue("error", msg, main_msg_queue)
        return False

    inner = t[left_bracket+1:right_bracket]
    if function == "FORMULA":
        delim = " "
        pattern = " (?![^()]*\))"
    else:
        delim = ", "
        pattern = "[,](?![^()]*\))"
    elements = [x.strip() for x in re.split(r''+pattern, inner) if x]

    refactored = []
    for e in elements:
        c = []
        for ci in range(len(e)):
            if e[ci] in operators:
                c.append(ci)
        if c:
            first = e[:c[0]].strip()
            if first:
                refactored.append(first)
            for j in range(len(c)-1):
                refactored.append(e[c[j]].strip())
                refactored.append(e[c[j]+1:c[j+1]].strip())
            refactored.append(e[c[-1]].strip())
            last = e[c[-1]+1:].strip()
            if last:
                refactored.append(last)
        else:
            refactored.append(e)

    # print(refactored)

    misfits = []
    for ri in range(len(refactored)):
        r = refactored[ri]
        if not r:
            continue
        if r in operators:
            continue
        if floatable(r.strip("()"), main_msg_queue):
            continue
        if "(" in r and r[:r.index("(")] in functions:
            ret = check_formula(r, main_msg_queue, restrict=restrict)
            if ret:
                if not r == ret:
                    refactored[ri] = ret
                continue
            else:
                misfits.append(r)
                continue
        elif restrict:
            if not r.strip("()") in restrict:
                throw_or_enqueue(
                    "error", "Unknown element in formula declaration: '" + r.strip("()") + "'", main_msg_queue)
            else:
                continue
        else:
            value, unit = separate_value_and_unit(
                r.strip("()"), main_msg_queue)
            if value:
                if not unit:
                    continue
                else:
                    # check for time tolerance parameter:
                    if convert_using_UCUM(value, unit, "s", main_msg_queue):
                        continue  # try conversion to seconds (base unit)
        if restrict:
            misfits.append(r.strip("()"))

    if misfits:
        msg = "Issues on formula elements : " + ", ".join(misfits)
        throw_or_enqueue("error", msg, main_msg_queue)
        return False

    return t[:left_bracket] + "(" + delim.join([r for r in refactored if r]) + ")"


def check_transformation(colname, sheet, fault_collector, main_msg_queue,  source_code_mappings={}):
    db_code_mappings = list(
        DatamodelCodeMapping.objects.values_list("Code_Mapping", flat=True))
    db_attrs = set(DatamodelAttribute.objects.all(
    ).values_list("Attribute", flat=True))
    source_attrs = set(sheet.column["Source_Attribute"])
    target_column = sheet.column["Target_Attribute"]
    fault_collector[colname]["transformation"] = []
    #formulas = ["FORMULA", "MEAN", "RANK", "SUM", "DELTA", "DIV", "PROD", "DRANGE", "DATE"]
    #operators = ["+", "-", "/", "*", "%", "^"]
    #pattern = ",|\s|\d" + "|[(" + ''.join(operators) + ")]"

    col = [cell.strip() for cell in sheet.column[colname]]
    if not col == sheet.column[colname]:
        msg = "Removed useless leading/trailing whitespace characters from column '" + colname + "'"
        throw_or_enqueue("warning", msg, main_msg_queue)

    for i in range(len(col)):
        if not col[i]:  # transformation is optional...
            continue
        t = col[i]
        # check, if the referenced code mapping is compatible to target variable's domain by values
        if t in db_code_mappings:
            #print(str(i) + ": " + t + " [CM]")
            cm_targeted_keys = list(set(DatamodelCodeMapping.objects.filter(
                Code_Mapping=t).values_list("Target_Equivalent", flat=True)))
        elif t in source_code_mappings:
            #print(str(i) + ": " + t + " [cm]")
            cm_targeted_keys = sorted(source_code_mappings[t])
        else:  # no code mapping found... should be a valid formula
            #print(str(i) + ": " + t + " [PF]")
            corr = check_formula(t, main_msg_queue, restrict=list(
                db_attrs.union(source_attrs)))
            #print( str(i) + ": " + str(col[i]) + " ==> " + str(corr) )
            if corr:
                col[i] = corr
            else:
                fault_collector[colname]["transformation"].append(i)
            continue

        # found a code mapping; value space acquired above
        if not DatamodelAttribute.objects.filter(  # <--- inserted by philipp
                Attribute=target_column[i]).exists():
            continue
        try:
            target_obj = DatamodelAttribute.objects.filter(Attribute=target_column[i])[0]
        except IndexError:
            throw_or_enqueue("error","Could not test code mapping '" + t + "'; target variable '"
                              + target_column[i] + "' unknown...", main_msg_queue)
            fault_collector[colname]["transformation"].append(i)
        cm_targeted_keys_new, sanitized = ensure_datatype_and_domain_fit(
            cm_targeted_keys, target_obj, main_msg_queue)

        #cm_targeted_keys = check_codekey_matches(cm_targeted_keys, target_obj.Domain)
        if not cm_targeted_keys_new:
            msg = "Could not apply code mapping '" + t + \
                "'; mismatches targeted attribute '" + target_obj.Attribute + "'..."
            throw_or_enqueue("error", msg, main_msg_queue)
            fault_collector[colname]["transformation"].append(i)

        sheet.column[colname] = col


def check_function(colname, sheet, fault_collector, main_msg_queue):
    db_attrs = set(DatamodelAttribute.objects.all(
    ).values_list("Attribute", flat=True))
    source_attrs = set(sheet.column["Attribute"])
    #target_column = sheet.column["Target_Attribute"]
    fault_collector[colname]["function"] = []
    #formulas = ["FORMULA", "MEAN", "RANK", "SUM", "DELTA", "DIV", "PROD", "DRANGE", "DATE"]
    #operators = ["+", "-", "/", "*", "%", "^"]
    #pattern = ",|\s|\d" + "|[(" + ''.join(operators) + ")]"

    col = [cell.strip() for cell in sheet.column[colname]]
    if not col == sheet.column[colname]:
        msg = "Removed useless leading/trailing whitespace characters from column '" + colname + "'"
        throw_or_enqueue("warning", msg, main_msg_queue)

    for i in range(len(col)):
        corr = check_formula(col[i], main_msg_queue)
        #print( str(i) + ": " + str(col[i]) + " ==> " + str(corr) )
        if corr:
            col[i] = corr
        else:
            fault_collector[colname]["function"].append(i)


    sheet.column[colname] = col


def get_relations(model):
    return [f for f in model._meta.fields if f.is_relation]


def sheet2model_core(sheet, model, data_collector, main_msg_queue, sheet_name, domain_extension=[]):
    fault_collector = {}
    error_flag = False
    row_mapper = []
    column_mapper = []
    try:
        sheet, row_mapper, column_mapper = prepare_sheet(
            sheet, main_msg_queue, sheet_name)
    except:
        return False, fault_collector, row_mapper, column_mapper

    # For all remaining data, check model compliance (by columns)

    msg = "\tWorking on columns:"
    throw_or_enqueue("info", msg, main_msg_queue)
    for colname in colname_map[sheet_name]:
        msg = "\t * " + colname
        throw_or_enqueue("info", msg, main_msg_queue)
        fault_collector[colname] = {}

        check_regular_field_compliance(
            colname, sheet, model, fault_collector, main_msg_queue)

        check_uniqueness_for_column(
            colname, sheet, model, fault_collector, main_msg_queue)

        if colname == "Domain":
            check_domain(colname, sheet, domain_extension,
                         fault_collector, main_msg_queue)
        #print(f"FAULT COLLECTOR: {fault_collector}")
        if not error_flag:
            error_flag = get_error_flag(fault_collector, colname)

        if not error_flag:
            check_foreign_keys(colname, sheet, model,
                               fault_collector,
                               data_collector)

        if not error_flag:
            error_flag = get_error_flag(fault_collector, colname)
    # END OF LOOP over columns of sheet

    if not error_flag:  # prepare DB import of data IF no errors occurred yet
        # generate import adapter from model
        #print(f"SUCCESS SHEET: {sheet_name} \n")
        #print(f"SHEET NAMES: {sheet}")
        adapter = DjangoModelImportAdapter(model)
        adapter.column_names = sheet.colnames
        # feed data collector struct with sheet-derived data
        data_collector[adapter.get_name()] = sheet
        return adapter, fault_collector, row_mapper, column_mapper
    else:
        pass
        #print(f"ERROR SHEET{sheet_name}")
    return False, fault_collector, row_mapper, column_mapper

    # if not error_flag:  # prepare DB import of data IF no errors occurred yet
    #    if sheet_name == "Codes":
    #        codes = sheet.column["Code"]   # bulk import only
    # if sheet_name == "Code_Mappings":
    #    code_mappings = sheet.column["Code_Mapping"]
    #    print("\tFine... Preparing import container...\n")
    #    importer = DjangoModelImporter()
    #    fill_import_containers(importer, data_collector, model, sheet)
    #    return importer
    # return False


def sheet2model_mapping(sheet, model, data_collector, main_msg_queue, sheet_name, source_code_mappings={}):
    fault_collector = {}
    error_flag = False
    try:
        sheet, row_mapper, column_mapper = prepare_sheet(
            sheet, main_msg_queue, sheet_name)
    except:
        return False, fault_collector, [], []

    # For all remaining data, check model compliance (by columns)

    msg = "\tWorking on columns:"
    throw_or_enqueue("info", msg, main_msg_queue)

    for colname in colname_map[sheet_name]:
        msg = "\t * " + colname
        throw_or_enqueue("info", msg, main_msg_queue)
        fault_collector[colname] = {}

        check_regular_field_compliance(
            colname, sheet, model, fault_collector, main_msg_queue)

        check_uniqueness_for_column(
            colname, sheet, model, fault_collector, main_msg_queue)

        if colname == "Transformation":
            check_transformation(colname, sheet, fault_collector, main_msg_queue,
                                 source_code_mappings=source_code_mappings)

        if colname == "Function":
            check_function(colname, sheet, fault_collector, main_msg_queue)

        if not error_flag:
            error_flag = get_error_flag(fault_collector, colname)

        if not error_flag:
            check_foreign_keys(colname, sheet, model,
                               fault_collector,
                               data_collector)

        if not error_flag:
            error_flag = get_error_flag(fault_collector, colname)
    # END OF LOOP over columns of sheet

    if not error_flag:  # prepare DB import of data IF no errors occurred yet
        # generate import adapter from model
        adapter = DjangoModelImportAdapter(model)
        adapter.column_names = sheet.colnames
        # feed data collector struct with sheet-derived data
        data_collector[adapter.get_name()] = sheet
        return adapter, fault_collector, row_mapper, column_mapper
    return False, fault_collector, row_mapper, column_mapper

    # if not error_flag:  # prepare DB import of data IF no errors occurred yet
    #    if sheet_name == "Codes":
    #        codes = sheet.column["Code"]   # bulk import only
    # if sheet_name == "Code_Mappings":
    #    code_mappings = sheet.column["Code_Mapping"]
    #    print("\tFine... Preparing import container...\n")
    #    importer = DjangoModelImporter()
    #    fill_import_containers(importer, data_collector, model, sheet)
    #    return importer
    # return False


def print_fault_collector(fault_collector, row_mappers, column_mappers):

    report = []
    throw_or_enqueue("error", "### ISSUE REPORT ###", report)

    for sheet in fault_collector.keys():
        throw_or_enqueue("error", "\n=== Sheet '" + sheet + "' ===", report)
        for column in fault_collector[sheet].keys():
            for error in fault_collector[sheet][column].keys():
                if len(fault_collector[sheet][column][error]):
                    throw_or_enqueue("error", "\nColumn '" + column + "' - '" +
                                     error + "' errors in following rows:", report)
                    throw_or_enqueue("error", ", ".join(
                        [str(row_mappers[sheet][x] + 2) for x in fault_collector[sheet][column][error]]), report)
    for msg in report:
        print(msg)


'''Deprecicated
def adapt_sheet2model(sheet, model, data_collector, main_msg_queue, sheet_name, domain_extension=[]):

    error_flag = False

    sheet, row_mapper, column_mapper = prepare_sheet(
        sheet, main_msg_queue, sheet_name)

    # For all remaining data, check model compliance (by columns)
    fault_collector = {}
    msg = "\tWorking on columns:"
    throw_or_enqueue("info", msg, main_msg_queue)
    for colname in colname_map_core[sheet_name]:
        msg = "\t * " + colname
        throw_or_enqueue("info", msg, main_msg_queue)
        fault_collector[colname] = {}

        check_regular_field_compliance(
            colname, sheet, model, fault_collector, main_msg_queue)

        check_uniqueness_for_column(
            colname, sheet, model, fault_collector, main_msg_queue)

        if colname == "Domain":
            check_domain(colname, sheet, domain_extension,
                         fault_collector, main_msg_queue)

        if not error_flag:
            error_flag = get_error_flag(fault_collector, colname)

        if not error_flag:
            check_foreign_keys(colname, sheet, model,
                               fault_collector,
                               data_collector)

        if not error_flag:
            error_flag = get_error_flag(fault_collector, colname)
    # END OF LOOP over columns of sheet

    if not error_flag:  # prepare DB import of data IF no errors occurred yet
        # generate import adapter from model
        adapter = DjangoModelImportAdapter(model)
        adapter.column_names = sheet.colnames
        # feed data collector struct with sheet-derived data
        data_collector[adapter.get_name()] = sheet
        return adapter, fault_collector
    return False, fault_collector

    # if not error_flag:  # prepare DB import of data IF no errors occurred yet
    #    if sheet_name == "Codes":
    #        codes = sheet.column["Code"]   # bulk import only
    # if sheet_name == "Code_Mappings":
    #    code_mappings = sheet.column["Code_Mapping"]
    #    print("\tFine... Preparing import container...\n")
    #    importer = DjangoModelImporter()
    #    fill_import_containers(importer, data_collector, model, sheet)
    #    return importer
    # return False

'''


def get_relations(model):
    return [f for f in model._meta.fields if f.is_relation]


# toDo: enable reporting
def foreign_key_replacement(target_model, target_colname, column, main_msg_queue, blank_allowed=False):
    i = 0
    while i < len(column):
        entry = column[i]
        if not entry:
            if not blank_allowed:
                msg = "Foreign Key field '" + target_colname \
                    + "' could not be served (empty source file field in input line " \
                    + str(i + 2) + ")!"
                throw_or_enqueue("error", msg, main_msg_queue)
                return False
            column[i] = ''
        else:
            try:
                targetObj = target_model.objects.filter(
                    **{target_colname: entry})[0]
            except IndexError:
                msg = "Foreign Key field '" + target_colname \
                      + "' could not be served (key '" + entry \
                      + "' could not be resolved)!"
                throw_or_enqueue("error", msg, main_msg_queue)
                return False
            column[i] = targetObj
        i += 1
    return column


def setup_foreign_keys_in_sheet(sheet, model, main_msg_queue):
    relations = get_relations(model)
    i = 0
    for colname in sheet.colnames:  # iterate over sheet-derived names
        try:
            fk_index = [r.name for r in relations].index(colname)
            target_model = relations[fk_index].related_model
            target_column = relations[fk_index].to_fields[0]
            msg = " --> Resolving Foreign Keys..."
            throw_or_enqueue("info", msg, main_msg_queue)
            blank_allowed = relations[fk_index].blank and relations[fk_index].null
            new_col = foreign_key_replacement(
                target_model, target_column, sheet.column[colname], main_msg_queue, blank_allowed)
            if not new_col:
                return False
            sheet.column[colname] = new_col
        except ValueError:
            # regular_fields
            pass
        i += 1
    return sheet


def importer2database(importer, data_collector, main_msg_queue):
    error_flag = False
    data_collector_subset = {}  # prepare struct for respective data chunk
    for model_adapter_name in importer._DjangoModelImporter__adapters.keys():
        sheet = data_collector[model_adapter_name]
        model = importer._DjangoModelImporter__adapters[model_adapter_name].model
        # Re-work data in sheet in order to fulfill foreignKey constraints (replace strings with objects)
        msg = "Checking ForeignKeys for '" + model_adapter_name + "'..."
        throw_or_enqueue("info", msg, main_msg_queue)
        new_sheet = setup_foreign_keys_in_sheet(sheet, model, main_msg_queue)
        if new_sheet:
            throw_or_enqueue("info", "...done.", main_msg_queue)
            data_collector_subset[model_adapter_name] = new_sheet.get_internal_array(
            )
        else:
            throw_or_enqueue("error", "...failed!", main_msg_queue)
            error_flag = True

    if not error_flag:
        msg = "Writing data to database..."
        throw_or_enqueue("info", msg, main_msg_queue)
        try:
            save_data(importer, data_collector_subset, file_type=DB_DJANGO)
        except IntegrityError as e:
            throw_or_enqueue("error", "FAILED!", main_msg_queue)
            throw_or_enqueue("error", e, main_msg_queue)
            return False
        throw_or_enqueue("info", "...success!", main_msg_queue)
        return True
    else:
        return False


def generate_report(fault_collector, row_mappers):
    report = []
    throw_or_enqueue("error", "### ISSUE REPORT ###", report)

    for sheetname in fault_collector.keys():
        throw_or_enqueue("error", "\n=== Sheet '" +
                         sheetname + "' ===", report)
        for column in fault_collector[sheetname].keys():
            for error in fault_collector[sheetname][column].keys():
                if len(fault_collector[sheetname][column][error]):
                    throw_or_enqueue("error", "\nColumn '" + column + "' - '" +
                                     error + "' errors in following rows:", report)
                    throw_or_enqueue("error", ", ".join(
                        [str(row_mappers[sheetname][x] + 2) for x in fault_collector[sheetname][column][error]]), report)
    return report


# MAIN METHOD DATAMODEL UPLOAD

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def datamodel_upload(request):
    print(f"GOT A DATA MODEL UPLOAD FROM : {get_client_ip(request)}")
    _file = request.FILES['datamodel_file']

    print(request.POST)

    core_method = request.POST.get('core_method')
    mapping_method = request.POST.get('mapping_method')

    # FETCHING PARAMETERS

    # variables usually acquired from the web interface (user inputs)

    try:
        offset = request.POST.get('header_line')
        header_line_core = {   # offset
            'Units': offset,
            'Attributes': offset,
            'Codes': offset,
        }
        header_line_mapping = {'Sources': offset, 'Attribute_Mappings': offset,    # offset
                               'Code_Mappings': offset,
                               'Calculations': offset,
                               }
    except:

        header_line_core = {    # offset
            'Units': 0,
            'Attributes': 0,
            'Codes': 0,
        }
        header_line_mapping = {'Sources': 0,
                               'Attribute_Mappings': 0,    # offset
                               'Code_Mappings': 0,
                               'Calculations': 0,
                               }
    model2sheet_core = {
        DatamodelUnit: 'Units',
        DatamodelCode: 'Codes',
        DatamodelAttribute: 'Attributes',
    }
    model2sheet_mapping = {DatamodelSource: 'Sources',
                           DatamodelAttributeMapping: 'Attribute_Mappings',
                           DatamodelCodeMapping: 'Code_Mappings',
                           DatamodelCalculation: 'Calculations',
                           }

    write_modes = [("new", "Drop complete data model before loading file"),
                   ("add", "Leave existing entries untouched, append your new ones"),
                   ]
    # "add" - "new" waere eine Einstellung *nur* fuer uns

    try:
        write_mode = request.POST.get('write_mode')
    except:
        write_mode = write_modes[0][0]

    # SAVE FILE TO DISK
    print(f"SAVING FILE TO DISK: {_file.name}")

    print("##--SAVING CURRENT FILE AS CURRENT DATA MODEL--##")
    # UserFile.objects.all().delete()

    fi = UserFile.objects.create(file=_file, name=_file.name)

    # print(file.file)
    #post_data = request.POST
    # START

    main_msg_queue = []
    sheet_names = get_book(file_name=fi.file.path).sheet_names()

    misses = [sn for sn in model2sheet_core.values() if not sn in sheet_names]
    if misses:
        msg = "Could not find following required worksheets in uploaded data model file:\n" + \
            "\n".join(misses)
        throw_or_enqueue("error", msg)

    if write_mode == "new":
        throw_or_enqueue(
            "warning", "This will delete all data model information contained in the current database.")
        drop_tables_core()
    # start iterative reading of contents from file
    dli = 0
    importer_collector = {}
    data_collector = {}
    fault_collector = {}
    column_mappers = {}
    row_mappers = {}
    unimported_codes = []
    error_flag = False
    for models in get_dependency_levels_core():
        msg = "Checking level " + str(dli+1) + " models..."
        throw_or_enqueue("info", msg, main_msg_queue)
        # generate new importer (adapter queue) for current dependency level
        importer = DjangoModelImporter()

        for model in models:
            sheet_name = model2sheet_core[model]
            # PRINT-MODEL: {model} \n")
            # print(model)
            # print(sheet_name)

            msg = "    => " + sheet_name + " --> " + model.__name__
            throw_or_enqueue("info", msg, main_msg_queue)

            # Get original data (sheet) from file
            sheetname = get_sheet(file_name=fi.file.path,
                              sheet_name=sheet_name,
                              name_columns_by_row=int(
                                  header_line_core[sheet_name]),
                              auto_detect_float=False,  # does not work
                              auto_detect_datetime=False)
            print("CALL MAIN / CORE")
            adapter, fc, rm, cm = sheet2model_core(
                sheetname, model, data_collector, main_msg_queue, sheet_name, unimported_codes)

            fault_collector[sheet_name] = fc
            row_mappers[sheet_name] = rm
            column_mappers[sheet_name] = cm
            # add adapter to importer (= queue for current dependency level)
            if not adapter:
                error_flag = True
            else:
                importer.append(adapter)
                if sheet_name == "Codes":
                    # bulk import only
                    unimported_codes = sheetname.column["Code"]
        #print(f"DATACOLLECTOR: {data_collector}")
        # END OF LOOP over sheets (= models) of the current dependency level

        if error_flag:
            msg = "General errors on dependency level " + \
                str(dli+1) + " models..."
            throw_or_enqueue("error", msg, main_msg_queue)
            error_flag = True
            break
        importer_collector[dli] = importer
        dli += 1
    # END OF LOOP over model dependency levels
    # Write collected, model-adapted data into database
    if not error_flag:
        for level in range(dli):
            # fire up the import for a dependency level
            msg = "Importing level " + str(level + 1) + " model data..."
            throw_or_enqueue("info", msg, main_msg_queue)
            # get level-specific subset of adapters (= one importer)
            importer = importer_collector[level]
            success = importer2database(
                importer, data_collector, main_msg_queue)
            if not success:
                error_flag = True
                msg = "Failed to write data model contents to DB (dep. level " + str(
                    level) + ")"
                throw_or_enqueue("error", msg, main_msg_queue)
                error_flag = True
            else:
                msg = "...done: Finished on level " + \
                    str(level + 1) + " models.\n"
                throw_or_enqueue("info", msg, main_msg_queue)
    else:
        print("ERRORs on core")
        if error_flag:
            report = generate_report(fault_collector, row_mappers)
            return JsonResponse({'message': 'not OK', 'msg_queue': main_msg_queue, "report": report})
        else:
            report = []
            throw_or_enqueue("info", "No errors occured", report)

        for msg in main_msg_queue:
            print(msg)
        throw_or_enqueue("error", "Errors occurred...", main_msg_queue)
        return JsonResponse({'message': 'not OK', 'msg_queue': main_msg_queue, "report": report})
    #print(f"ERROR CELL: {row_mapper[167]}")

    # 1b. Mappings: Initialization
    main_msg_queue = []
    sheet_names = get_book(file_name=fi.file.path).sheet_names()
    misses = [sn for sn in model2sheet_mapping.values()
              if not sn in sheet_names]
    if misses:
        msg = "Could not find following required worksheets in uploaded data model file:\n" + \
            "\n".join(misses)
        throw_or_enqueue("error", msg)

    if write_mode == "new":
        from django.db import connections
        from django.db.utils import OperationalError
        db_conn = connections['default']
        try:
            c = db_conn.cursor()
        except OperationalError:
            connected = False
        else:
            connected = True
        #print(c.db.__dict__)
        throw_or_enqueue(
            "warning", "This will delete all mapping information contained in the current database.")
        drop_tables_mapping()

    # 2b. Mappings: start iterative reading of contents from file
    dli = 0
    importer_collector = {}
    data_collector = {}
    fault_collector = {}
    row_mappers = {}
    column_mappers = {}
    unimported_codemappings = {}
    error_flag = False
    for models in get_dependency_levels_mapping():
        msg = "Checking level " + str(dli+1) + " models..."
        throw_or_enqueue("info", msg, main_msg_queue)
        # generate new importer (adapter queue) for current dependency level
        importer = DjangoModelImporter()

        for model in models:
            sheet_name = model2sheet_mapping[model]

            msg = "    => " + sheet_name + " --> " + model.__name__
            throw_or_enqueue("info", msg, main_msg_queue)

            # Get original data (sheet) from file
            sheetname = get_sheet(file_name=fi.file.path,
                              sheet_name=sheet_name,
                              name_columns_by_row=int(
                                  header_line_mapping[sheet_name]),
                              auto_detect_float=False,  # does not work
                              auto_detect_datetime=False)
            print("CALL MAIN / MAPPING")
            adapter, fc, rm, cm = sheet2model_mapping(
                sheetname, model, data_collector, main_msg_queue, sheet_name, unimported_codemappings)
            fault_collector[sheet_name] = fc
            row_mappers[sheet_name] = rm
            column_mappers[sheet_name] = cm
            # add adapter to importer (= queue for current dependency level)
            if not adapter:
                error_flag = True
                print("no adapter")
            else:
                importer.append(adapter)
                if sheet_name == "Code_Mappings":                       # for bulk import only
                    pos_cm = sheetname.colnames.index("Code_Mapping")
                    pos_te = sheetname.colnames.index("Target_Equivalent")
                    for row in sheetname:
                        cm = row[pos_cm]
                        if cm in unimported_codemappings:
                            unimported_codemappings[cm].add(row[pos_te])
                        else:
                            unimported_codemappings[cm] = set([row[pos_te]])
                    for cm in unimported_codemappings:
                        unimported_codemappings[cm] = list(
                            unimported_codemappings[cm])
                    #unimported_codemappings = sheet.column["Code_Mapping"]

        # END OF LOOP over sheets (= models) of the current dependency level

        if error_flag:
            msg = "General errors on dependency level " + \
                str(dli+1) + " models..."
            throw_or_enqueue("error", msg, main_msg_queue)
            break
        importer_collector[dli] = importer
        dli += 1
# END OF LOOP over model dependency levels

    # 3b. Write collected, model-mapped data into database
    if not error_flag:
        for level in range(dli):
            # fire up the import for a dependency level
            msg = "Importing level " + str(level + 1) + " model data..."
            throw_or_enqueue("info", msg, main_msg_queue)
            # get level-specific subset of adapters (= one importer)
            importer = importer_collector[level]
            success = importer2database(
                importer, data_collector, main_msg_queue)
            if not success:
                error_flag = True
                msg = "Failed to write data model contents to DB (dep. level " + str(
                    level) + ")"
                throw_or_enqueue("error", msg, main_msg_queue)
                error_flag = True
            else:
                msg = "...done: Finished on level " + \
                    str(level + 1) + " models.\n"
                throw_or_enqueue("info", msg, main_msg_queue)
    else:
        throw_or_enqueue("error", "Errors occurred...", main_msg_queue)

    # Reporting
    for msg in main_msg_queue:
        print(msg)
    #main_msg_queue = []

    if error_flag:
        report = generate_report(fault_collector, row_mappers)
        return JsonResponse({'message': 'not OK', 'msg_queue': main_msg_queue, "report": report})

    else:
        report = []
        throw_or_enqueue("info", "No errors occured", report)

    for msg in report:
        print(msg)
    #report = []
    return JsonResponse({'message': 'OK', 'msg_queue': main_msg_queue, "report": report})


@csrf_exempt
def get_attr(request):
    attributes = DatamodelAttribute.objects.filter(Active=True)
    attr = []
    for at in attributes:
        attr.append({'tooltip': at.Attribute_Tooltip,
                     'topic': at.Topic, 'name': at.Attribute, "description": at.Attribute_Description})

    return JsonResponse({'attributes': attr})


@csrf_exempt
def get_sources(request):
    sources = DatamodelSource.objects.all()
    so = []
    sources_abbreviation = []
    for s in sources:
        sources_abbreviation.append(s.Abbreviation)
        so.append(s.Source)
    return JsonResponse({'sources': so, "abbreviations": sources_abbreviation})


@csrf_exempt
def get_attr_mappings(request):
    attr_mappings = DatamodelAttributeMapping.objects.filter(Active=True)
    am = []
    for attr_map in attr_mappings:
        am.append({'Source': attr_map.Source.Source, 'name': attr_map.Source_Attribute,
                   'Target': attr_map.Target_Attribute.Attribute,
                   'TargetDescription': attr_map.Target_Attribute.Attribute_Description,
                   'Transformation': attr_map.Transformation})

    return JsonResponse({'mappings': am})


@csrf_exempt
def get_data_all(request):
    datapoints = BasicDataPoint.objects.all()

    return JsonResponse({"data": [{"variableExternal": dp.variable_raw, "variableMapped": dp.variable.Attribute if dp.variable else "__unmapped__", "value": dp.value, "patientId": dp.pid, "timestamp": dp.timestamp} for dp in datapoints]})

@csrf_exempt
def get_attr_information(request):

    node = request.GET['node']
    t = request.GET['type']

    if t == "attribute":
        queryResult = DatamodelAttribute.objects.filter(
            Attribute=node) | DatamodelAttribute.objects.filter(Attribute_Tooltip=node)

    if t == "source":
        queryResult = DatamodelSource.objects.filter(Source=node)
    else:
        queryResult = DatamodelAttribute.objects.filter(
            Attribute=node) | DatamodelAttribute.objects.filter(Attribute_Tooltip=node)
    if queryResult.exists():
        return JsonResponse({'information': serializers.serialize('json', queryResult)})
    else:
        return JsonResponse({'information': "none"})


@api_view(["GET"])
def get_units_all(request):
    units = DatamodelUnit.objects.all()
    return JsonResponse({'units': serializers.serialize('json', units)})


def onOffTrueFalse(data):
    if data == "on":
        return True
    elif not data:
        return True
    else:
        return False

def oneZeroTrueFalse(data):
    if data:
        return 1
    else:
        return 0


@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_create_code(request):
    data = request.POST

    code_name = data['code_name']
    code_description = data['code_discription']
    active = onOffTrueFalse(data['active'])
    counter = 1
    for dat in data:
        if "key" in dat:
            code = DatamodelCode(Code=code_name, Code_Description=code_description, Active=active)
            if data[f"key_{counter}"] and data[f"val_{counter}"] and data[f"key_{counter}"] != "" and data[f"val_{counter}"] != "" :
                code.Key = data[f"key_{counter}"]
                code.Value = data[f"val_{counter}"]
                code.save()
                counter+=1

    return JsonResponse({"message": "ok"})


@api_view(["POST"])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_edit_attr(request):
    # get data
    data = request.POST
    main_msg_queue = []

    #print(data)

    active = onOffTrueFalse(data.get('active') or None)
    topic = data.get('topic') or None
    topic_description = data.get('topic_description') or None
    umbrella = data.get('umbrella') or None
    umbrella_description = data.get('umbrella_description') or None
    attribute = data.get('attribute') or None
    attribute_description = data.get('attribute_description') or None
    attribute_tooltip = data.get('attribute_tooltip') or None
    domain = data.get('domain') or None
    datatype = data.get('datatype') or None
    unit_unit = data.get('unit') or None
    # to do make sanitizing
    # check if model exists
    
    attr = DatamodelAttribute.objects.filter(Attribute = attribute)
    if not attr.exists():
        return JsonResponse({'message':'Attribute does not exist!'})
    attr = attr[0]
    

    
    # check for topic entry and its description
    if topic and topic_description:
        attr.Topic = topic
        attr.Topic_Description = topic_description
    else:
        throw_or_enqueue("error", "Provide proper Topic name and its description", main_msg_queue)
        print(f"Error: Provide proper Topic name and its description")
    
    if umbrella and umbrella_description:
        attr.Umbrella = umbrella
        attr.Umbrella_Description = umbrella_description
    else:
        throw_or_enqueue("error", "Provide proper Umbrella and its description", main_msg_queue)
        print(f"Error: Provide proper Umbrella and its description")
    
    if attribute and attribute_tooltip and attribute_description:
        attr.Attribute = attribute
        attr.Attribute_Description = attribute_description
        attr.Attribute_Tooltip = attribute_tooltip
    else:
        throw_or_enqueue("error", "Provide proper information related to Attribute", main_msg_queue)
        print(f"Error: Provide proper information related to Attribute")
        return JsonResponse({'message': "Missing data"})


    attr.Datatype = datatype
    attr.Domain = domain

    unit = DatamodelUnit.objects.filter(pk=unit_unit)
    if not unit.exists():
        return JsonResponse({'message': "No such unit"})
    attr.Unit = unit[0]

    '''
    unit = DatamodelUnit()
    unit.Unit = unit_unit
    unit.UCUM = unit_ucum
    if len(unit_description) == 4:
        unit.Description = unit_description
    else:
        throw_or_enqueue("error", "Provide proper unit desscription", main_msg_queue)
        print(f"Error: Provide proper unit desscription")
    attr.Unit = unit


    file = UserFile.objects.all().order_by('-id')[0]
    # with open(file.file.path, "wr") as f:
    book = get_book(file_name=file.file.path)
    attr_map_sheet = book['Attributes']
    attr_map_sheet.row += [oneZeroTrueFalse(active), topic, topic_description, umbrella, umbrella_description,
                           attribute, attribute_description, attribute_tooltip, datatype, domain, unit_unit]
    book.save_as(file.file.path)
    '''
    try:
        attr.save()
     
    except:
        print(traceback.format_stack())
        return JsonResponse({'message': traceback.format_stack()})

    return JsonResponse({'message': 'ok', 'msg_queue': main_msg_queue})



@api_view(["POST"])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_create_attr(request):
    # get data
    data = request.POST
    main_msg_queue = []

    #print(data)

    active = onOffTrueFalse(data.get('active') or None)
    topic = data.get('topic') or None
    topic_description = data.get('topic_description') or None
    umbrella = data.get('umbrella') or None
    umbrella_description = data.get('umbrella_description') or None
    attribute = data.get('attribute') or None
    attribute_description = data.get('attribute_description') or None
    attribute_tooltip = data.get('attribute_tooltip') or None
    domain = data.get('domain') or None
    datatype = data.get('datatype') or None
    unit_unit = data.get('unit') or None


    # to do make sanitizing
    # check if model exists
    
    attr = DatamodelAttribute.objects.filter(Attribute = attribute)
    if attr.exists():
        return JsonResponse({'message':'Attribute already exists!'})
        #attr = attr[0]
    else:
    
        attr = DatamodelAttribute()

    # create model
    
    attr.Active = active
    
    # check for topic entry and its description
    if topic and topic_description:
        attr.Topic = topic
        attr.Topic_Description = topic_description
    else:
        throw_or_enqueue("error", "Provide proper Topic name and its description", main_msg_queue)
        print(f"Error: Provide proper Topic name and its description")
    
    if umbrella and umbrella_description:
        attr.Umbrella = umbrella
        attr.Umbrella_Description = umbrella_description
    else:
        throw_or_enqueue("error", "Provide proper Umbrella and its description", main_msg_queue)
        print(f"Error: Provide proper Umbrella and its description")
    
    if attribute and attribute_tooltip and attribute_description:
        attr.Attribute = attribute
        attr.Attribute_Description = attribute_description
        attr.Attribute_Tooltip = attribute_tooltip
    else:
        throw_or_enqueue("error", "Provide proper information related to Attribute", main_msg_queue)
        print(f"Error: Provide proper information related to Attribute")
        return JsonResponse({'message': "Missing data"})


    attr.Datatype = datatype
    attr.Domain = domain

    unit = DatamodelUnit.objects.filter(pk=unit_unit)
    if not unit.exists():
        return JsonResponse({'message': "No such unit"})
    attr.Unit = unit[0]

    '''
    unit = DatamodelUnit()
    unit.Unit = unit_unit
    unit.UCUM = unit_ucum
    if len(unit_description) == 4:
        unit.Description = unit_description
    else:
        throw_or_enqueue("error", "Provide proper unit desscription", main_msg_queue)
        print(f"Error: Provide proper unit desscription")
    attr.Unit = unit


    file = UserFile.objects.all().order_by('-id')[0]
    # with open(file.file.path, "wr") as f:
    book = get_book(file_name=file.file.path)
    attr_map_sheet = book['Attributes']
    attr_map_sheet.row += [oneZeroTrueFalse(active), topic, topic_description, umbrella, umbrella_description,
                           attribute, attribute_description, attribute_tooltip, datatype, domain, unit_unit]
    book.save_as(file.file.path)
    '''
    try:
        attr.save()
     
    except:
        print(traceback.format_stack())
        return JsonResponse({'message': traceback.format_stack()})

    return JsonResponse({'message': 'ok', 'msg_queue': main_msg_queue})


@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_create_unit(request):
    data = request.POST

    #print(data)
    unit = DatamodelUnit()
    unit.Unit = data['unit_name']
    unit.Description = data['unit_description']
    if "ucum" in data.keys():
        unit.UCUM = onOffTrueFalse(data['ucum'])
    try:

        unit.save()
    except:
        print(traceback.format_stack())
        return JsonResponse({'message': traceback.format_stack()})
    return JsonResponse({'message': "ok"})


@api_view(["POST"])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_create_mapping(request):

    data = request.POST
    #print(data)
    main_msg_queue = []
    mapping = DatamodelAttributeMapping()
    source = data.get('source') or None
    target_attr = data.get('target') or None
    source_attr = data.get('source_attr') or None
    active = onOffTrueFalse(data.get('active') or None)
    transformation = data.get('transformation') or None
    model_source = DatamodelSource.objects.filter(Source=source)


    if not model_source.exists():
        return JsonResponse({'message': "no such source"})

    mapping.Source = model_source.first()
    mapping.Active = active
    # sanitizing

    if not source_attr:
        throw_or_enqueue("error", "Provide unique source attribut for mapping", main_msg_queue)
        print(f"Error: Provide unique source attribut for mapping")
    else:
        mapping.Source_Attribute = source_attr

    if not target_attr:
        throw_or_enqueue("error", "Provide proper name of target for mapping", main_msg_queue)
        print(f"Error: Provide proper name of target for mapping")
    else:
        model_target = DatamodelAttribute.objects.filter(Attribute=target_attr)
        if not model_target.exists():
            return JsonResponse({'message': 'no such target attribute'})
        mapping.Target_Attribute = model_target.first()

    if not transformation:
        throw_or_enqueue("error", "Provide proper transformation method for mapping", main_msg_queue)
        print(f"Error: Provide proper transformation method for mapping")
    else:
        mapping.Transformation = transformation


    '''
    file = UserFile.objects.all().order_by('-id')[0]
    # with open(file.file.path, "wr") as f:
    book = get_book(file_name=file.file.path)
    attr_map_sheet = book['Attribute_Mappings']
    attr_map_sheet.row += [oneZeroTrueFalse(active),
                           source, source_attr, target_attr, transformation]
    book.save_as(file.file.path)
    try:
        mapping.save()
    except:
        return JsonResponse({'message': traceback.format_stack()})
    '''

    return JsonResponse({'message': 'ok', 'msg_queue': main_msg_queue})


@csrf_exempt
@require_http_methods(['GET'])
def get_datamodel_as_excel(request):

    f = open("DM.xlsx", 'wb')

    writer = pd.ExcelWriter(f)

    #DatamodelAttribute
    data_attr_df = pd.DataFrame(DatamodelAttribute.objects.all().values())

    #DatamodelUnit
    data_unit_df = pd.DataFrame(DatamodelUnit.objects.all().values())

    # DatamodelCode
    data_code_df = pd.DataFrame(DatamodelCode.objects.all().values())

    #DatamodelAttributeMapping
    data_attrmapping_df = pd.DataFrame(DatamodelAttributeMapping.objects.all().values())

    #DatamodelCalculation
    data_calculation_df = pd.DataFrame(DatamodelCalculation.objects.all().values())

    # DatamodelCodeMapping
    data_codemapping_df = pd.DataFrame(DatamodelCodeMapping.objects.all().values())

    # DatamodelSource
    data_source_df = pd.DataFrame(DatamodelSource.objects.all().values())

    #xlsx file write
    data_unit_df.to_excel(writer, sheet_name='Units', index=False)
    data_code_df.to_excel(writer, sheet_name='Codes', index=False)
    data_attr_df.to_excel(writer, sheet_name='Attributes', index=False)
    data_source_df.to_excel(writer, sheet_name='Sources', index=False)
    data_codemapping_df.to_excel(writer, sheet_name='Code_Mappings', index=False)
    data_attrmapping_df.to_excel(writer, sheet_name='Attribute_Mappings', index=False)
    data_calculation_df.to_excel(writer, sheet_name='Calculations', index=False)


    writer.save()

    f = open("DM.xlsx", 'rb')
    response = FileResponse(f)
    response['Content-Disposition'] = 'attachment; filename="DM.xlsx"'
    writer.close()
    return response


@csrf_exempt
@require_http_methods(['POST'])
def post_create_src(request):

    data = request.POST
    main_msg_queue = []

    abbreviation = data.get('abbreviation') or None
    source = data.get('source') or None
    pid_colname = data.get('pid_colname') or None
    site_colname = data.get('site_colname') or None
    timestamp_colname = data.get('timestamp_colname') or None
    header_offset = data.get('header_offset') or None
    filepath = data.get('filepath') or None

    source_model = DatamodelSource()

    # sanitizing
    if not abbreviation:
        throw_or_enqueue("error", "Provide unique abbreviation for the source", main_msg_queue)
        print(f"Error: Provide unique abbreviation for the source")
    else:
        source_model.Abbreviation = abbreviation

    if not source:
        throw_or_enqueue("error", "Provide proper name of the source", main_msg_queue)
        print(f"Error: Provide proper name of the source")
    else:
        source_model.Source = source


    if not pid_colname:
        throw_or_enqueue("error", "Provide proper PID column name for the source", main_msg_queue)
        print(f"Error: Provide proper PID column name for the source")
    else:
        source_model.PID_colname = pid_colname

    if not site_colname:
        throw_or_enqueue("error", "Provide proper SITE column name for the source", main_msg_queue)
        print(f"Error: Provide proper SITE column name for the source")
    else:
        source_model.SITE_colname = site_colname

    if not timestamp_colname:
        throw_or_enqueue("error", "Provide proper timestamp column name for the source", main_msg_queue)
        print(f"Error: Provide proper timestamp column name for the source")
    else:
        source_model.TIMESTAMP_colname = timestamp_colname

    if not header_offset:
        throw_or_enqueue("error", "Provide proper header offset for the source", main_msg_queue)
        print(f"Error: Provide proper header offset for the source")
    else:
        source_model.Header_offset = header_offset

    if not filepath:
        throw_or_enqueue("error", "Provide proper filepath for the source", main_msg_queue)
        print(f"Error: Provide proper filepath for the source")
    else:
        source_model.Filepath = filepath

    try:
        source_model.save()
    except:
        return JsonResponse({'message': traceback.format_stack()})

    return JsonResponse({'message': "ok", 'msg_queue': main_msg_queue})


@csrf_exempt
def get_fulltext(request):
    data = request.GET
    # print(data)
    text = data.get('text')
    result = set()
    for attr in DatamodelAttribute.objects.all():
        if attr.Attribute and text.lower() in attr.Attribute.lower():
            result.add(attr.Attribute)
        if attr.Attribute_Description and text.lower() in attr.Attribute_Description.lower():
            result.add(attr.Attribute)
        if attr.Attribute_Tooltip and text.lower() in attr.Attribute_Tooltip.lower():
            result.add(attr.Attribute)
        if attr.Umbrella and text.lower() in attr.Umbrella.lower():
            result.add(attr.Attribute)
        if attr.Umbrella_Description and text.lower() in attr.Umbrella_Description.lower():
            result.add(attr.Attribute)
    return JsonResponse({'result': list(result)})


@csrf_exempt
def check_attr_exists(request):
    data = request.GET
    name = data['attr_name']

    if DatamodelAttribute.objects.filter(Attribute=name).exists():
        return JsonResponse({
            "message": "taken"
        })
    else:
        return JsonResponse({
            "message": "free"
        })

@csrf_exempt
def get_data_by_attribute(request):
    attr = request.GET["attribute"]
    attribute_model = DatamodelAttribute.objects.filter(Attribute = attr)
    if not attribute_model.exists():
        return JsonResponse({"message": "no such variable"}, status=404)
    qs = BasicDataPoint.objects.filter(variable = attribute_model)
    return JsonResponse({"data": [{"attribute": a.variable.Attribute, "value": a.value, "timestamp": a.timestamp, "pid": a.pid} for a in qs]})


@csrf_exempt
def get_attr_mapping_info(request):
    data = request.GET
    # print(data)
    query = DatamodelAttributeMapping.objects.filter(Target_Attribute=data['attr_1'], Source_Attribute=data['attr_2']) | DatamodelAttributeMapping.objects.filter(
        Target_Attribute=data['attr_2'], Source_Attribute=data['attr_1'])
    if not query.exists():
        return JsonResponse({"information": "none"})
    return JsonResponse({"information": serializers.serialize('json', query)})


class AsyncioMessenger:
    def __init__(self, id):
        self.id = id

    def send(self, message):
        requests.post("http://localhost:3001/makemessage",
                      data={'uuid': self.id, 'msg': message})
        return

#@csrf_exempt
@api_view(["POST"])
def datapoints_upload(request):
    data = request.POST

    # print(f"data {data}")
    #sender = AsyncioMessenger(data['socket_id'])
    print(f"GOT A DATA UPLOAD FROM : {get_client_ip(request)}")
    _file = request.FILES['data_file']
    fi = UserFile.objects.create(file=_file, name=_file.name)



    print("Here 1")

    #sheet = request.FILES['data_file'].get_sheet(name_columns_by_row=0)

    sheet = get_sheet(file_name=fi.file.path,
                      name_columns_by_row=0,
                      delimiter=data["delim"],
                      auto_detect_datetime=False,
                      quotechar='"',
                      quoting=csv.QUOTE_ALL)

    print(f"colum names")
    # print(sheet)
    meta = {}
    if 'source_origin' in data.keys():
        meta['source'] = data['source_origin']
    else:
        meta['source'] = 'CRC-SCA'
    if 'error_mode' in data.keys():
        meta['error_mode'] = data['error_mode']
    if 'write_mode' in data.keys():
        meta['write_mode'] = data['write_mode']
    meta['delim'] = data["delim"]
    meta['min_date'] = data["min_date"]
    meta['max_date'] = data["max_date"]
    meta['_id'] = data['_id']
    cache.set(meta['_id'], {'status': "working", "message": "", 'msg_queue': []})
    print("Here 2")
    request.session['form-data'] = meta

    main_msg_queue = []
    throw_or_enqueue("info", "message queue logging", main_msg_queue)

    th = threading.Thread(target=import_data_sanitization, args=(meta, request, sheet, main_msg_queue))
    print("Starting Thread....")
    th.start()
    print("Started Thread!")


    #df = pd.read_csv(fi.file.path)
    #th = threading.Thread(target=import_data_straight_forward, args=(df,meta))
    #th.start()





    return JsonResponse({'message': 'ok'})


def import_data_straight_forward(df, meta):
    DataPointsVisit.objects.all().delete()
    data = []
    row_count = len(df.index)
    for index, row in df.iterrows():

        cache.set(meta['_id'], {'status': str(index/40000)})

        if index >= 40000:
            DataPointsVisit.objects.bulk_create(data)
            print("##########------------DONE--------------#############")
            cache.set(meta['_id'], {'status': 'done'})
            break
        try:
            data_point = DataPointsVisit(PID = row['PID'],TIMESTAMP = row['TIMESTAMP'],VALUE = row['VALUE'],ATTRIBUTE = row['ATTRIBUTE'],VISIT = row['VISIT'])
            source = DatamodelSource.objects.get(Source = row['SOURCE'])
            data_point.SOURCE = source
            data.append(data_point)
        except:
            print(f"Corrupt line :{index}")

    return


@api_view(['GET'])
def get_chache_by_id(request):
    return JsonResponse({'message': cache.get(request.GET['_id'])})

#@csrf_exempt
@api_view(["POST"])
def datapoints_upload_forgetit(request):
    data = request.POST
    # print(f"data {data}")
    #sender = AsyncioMessenger(data['socket_id'])
    print(f"GOT A DATA UPLOAD FROM : {get_client_ip(request)}")
    _file = request.FILES['data_file']
    fi = UserFile.objects.create(file=_file, name=_file.name)

    """
    # sheet = request.FILES['data_file'].get_sheet(name_columns_by_row=0)
    # print(f"colum names")
    # print(sheet)
    meta = {}
    if 'source_origin' in data.keys():
        meta['source'] = data['source_origin']
    else:
        meta['source'] = 'CRC-SCA'
    if 'error_mode' in data.keys():
        meta['error_mode'] = data['error_mode']
    if 'write_mode' in data.keys():
        meta['write_mode'] = data['write_mode']
    meta['delim'] = data["delim"]
    meta['min_date'] = data["min_date"]
    meta['max_date'] = data["max_date"]

    request.session['form-data'] = meta
    """
    main_msg_queue = []
    throw_or_enqueue("info", "message queue logging", main_msg_queue)

    ### code import from old 'upload' app starts here

    # INPUTS
    sanitize = (data["error_mode"] == "sanitize" or data["error_mode"] == "propose")

    eav_colnames = ["PID", "DATE", "ATTRIBUTE", "VALUE", "PROVENANCE"]
    chunk_size = 1000

    colname_mapping = {"PID": "PID",
                       "DATE": "TS",
                       "VISIT": "VISIT",
                       "ATTRIBUTE": "ITEM",
                       "VALUE": "VALUE",
                       "PROVENANCE": "PROVENANCE"}  # ToDo: enable mappings by form...
    colname_vec = ["PID", "DATE", "ATTRIBUTE", "VALUE", "PROVENANCE"]

    # ToDo: user declares 2D ('normal') or 1D (EAV++) table; if 2D, reformat first

    # END OF INPUTS

    # sweep data table if necessary
    if data["write_mode"] == "sweep":
        throw_or_enqueue("warning", "This will delete all data contained in the current database.", main_msg_queue)
        drop_tables_data()

    # open file provided by upload form
    # sheet = _file.get_sheet(name_columns_by_row=0)
    #sheet = pd.read_csv(fi.file.path, delimiter=data["delim"])

    sheet = get_sheet(file_name=fi.file.path,
                      name_columns_by_row=0,
                      delimiter=data["delim"],
                      quotechar='"',
                      quoting=csv.QUOTE_ALL)
    # ToDo: offset header?

    # Check header
    print(sheet.colnames)
    #r = csv.reader(sheet.colnames, delimiter=data["delim"], quotechar='"',
    #               quoting=csv.QUOTE_ALL)
    #header = next(r)
    # print("This is the header " + str(header))
    if colname_mapping:
        indices = get_header_indeces(request, sheet.colnames, [colname_mapping[x] for x in colname_vec])
        if indices:
            for c in colname_vec:
                indices[c] = indices.pop(colname_mapping[c])
    else:
        indices = get_header_indeces(request, sheet.colnames, colname_vec)

    if not indices:
        throw_or_enqueue("error", "Corrupt EAV++ header line - please check log for details.", main_msg_queue)
        #return HttpResponse("Corrupt EAV++ header line - please check log for details.")

    # Proceed on contents: iterate rows of EAV
    targets = {}  # collector; saves DB requests
    verified_UCUM_units = {}  # index; saves server requests
    value_conversions = {}  # collector; saves server requests
    eav_array = [eav_colnames]  # collector; saves EAV lines for chunked database uploads
    bulk_mgr = BulkCreateManager(chunk_size=chunk_size)
    line_counter = 0
    line_cnt_success = 0
    k = 0
    length = 0

    for row in sheet:
        if data["error_mode"] == "strict" and line_counter != line_cnt_success:
            # TODO
            break

        line_counter += 1

        row_pid = row[indices["PID"]]
        row_date = row[indices["DATE"]]
        row_visit = row[indices["VISIT"]]
        row_attr = row[indices["ATTRIBUTE"]]
        row_value = row[indices["VALUE"]]
        # print(row_value)

        # check DATE
        date_range = [data["min_date"], data["max_date"]]
        sanitize_trigger = (data["error_mode"] == "sanitize" or data["error_mode"] == "propose")
        if row_date == "*":
            static = True
            entity_date = row_date
        else:
            static = False
            entity_date = check_date(row_date,
                                     date_range=date_range,
                                     sanitize=sanitize_trigger
                                     )
            if not entity_date:  # no valid DATE - row data is useless
                continue
            elif entity_date != row_date:
                msg = "Line " + str(line_counter) + ": " + row_date + " => " + entity_date + " (DATE)"
                if data["error_mode"] == "propose":
                    throw_or_enqueue("info", "Sanitizing of 'DATE' successful, while proposal requested.", main_msg_queue)
                    #async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                    #                                        {"type": "status_message", "message": msg + " PROPOSAL"})
                    #brokenlines[line_counter] = msg + ";;PROPOSAL;;red;;DATE"
                    continue
                #else:
                    #async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                    #                                        {"type": "status_message", "message": msg + " SANITIZED"})
                    #brokenlines[line_counter] = msg + ";;SANITIZED;;yellow;;DATE"

        # check uniqueness of EAV entry for SOURCE
        ## dynamics: message and action depends on mode and coarseness
        ## statics: duplicates are illegal per se (or replace the given info IF configured so)
        entries = list()
        if not data["write_mode"] == "sweep":
            entries = DataPoints.objects.filter(    SOURCE=data["source"],
                                                    PID = row_pid,
                                                    DATE = entity_date,
                                                    ATTRIBUTE = row_attr,
                                                )
            if entries:
                eav = row_pid + ";" + entity_date + ";" + row_attr + ";" + row_value
                if data["write_mode"] == "unique":
                    throw_or_enqueue("error", "Duplicate entry while 'unique' requested - skipping line #"
                                     + str(line_counter) + "...", main_msg_queue)
                    #brokenlines[line_counter] = "Duplicate entry while 'unique' requested - skipping line;;SKIPPED;;grey;;SOURCE"
                    continue
                elif data["write_mode"] == "update":
                    throw_or_enqueue("warning", "Existing entry " + " will be replaced with input line #"
                                     + str(line_counter) + "('" + eav + "')...", main_msg_queue)
                    #brokenlines[line_counter] = "Existing entry " + " will be replaced with input line" + str(
                    #    line_counter) + "('" + eav + "')...;;SANITIZED;;yellow;;SOURCE"
                elif data["write_mode"] == "add" and static:
                    throw_or_enqueue("error", "Existing time-less entry " + " - addition not possible! Skipping line #"
                                     + str(line_counter) + "...", main_msg_queue)
                    #brokenlines[
                    #    line_counter] = "Existing time-less entry " + " - addition not possible! Skipping line;;SKIPPED;;grey;;SOURCE"
                    continue

        # check ATTRIBUTE in variable list existance (in mapping table and core set)
        # todo: if target variable is not ACTIVE: WARNING and skip
        # print( str(line_counter + 1) + ": " + row_attr )

        if row_attr not in targets:
            target_list = get_target_from_datamodel(request, row_attr, targets, data["source"],
                                                    "mapping_only" in data)
            if not target_list:
                continue

    ###
    return JsonResponse({'message': 'OK'})


def get_or_create(ontology, class_name, parent_class):
    if(ontology[class_name]):
        return ontology[class_name]
    else:
        c = types.new_class(
            class_name, (parent_class,))
        c.namespace = ontology
        return c


@csrf_exempt
@require_http_methods(['GET'])
def get_owl(request):

    seed(time.time())


    file_path = os.path.dirname(os.path.realpath(
        __file__)) + "/" + "../" + settings.OWL_LOCATION + "/CCDM_blueprint.owl"
    #print(file_path)

    onto = get_ontology("file:///" + file_path).load()
    #print(list(onto.classes()))

    # BUILDING THE ONTOLOGY

    #onto_path.append(os.path.dirname(os.path.realpath(
    #    __file__)) + "/" + "../" + settings.OWL_LOCATION)

    object_property_topclass = "relational_property"
    '''
    UNITS

    '''


    unit_class = onto['Unit']
    for unit in DatamodelUnit.objects.all():

        if unit.Unit:

            c = get_or_create(
                onto, unit.Unit, unit_class)
            if unit.UCUM:
                c.is_UCUM = "true"

            if unit.Description:
                c.has_description =unit.Description

    '''
    CODES
    '''

    code_class = onto['Code']

    # print(list(onto.annotation_properties()))
    for code in DatamodelCode.objects.all():

        if code.Code:

            c = get_or_create(
                onto, code.Code, code_class)
            c.has_code_key_value_pair.append(str(code.Key) + "::" + str(code.Value))
            c.has_description.append(code.Code_Description)
            c.label = "Code for " + str(code.Code_Description)
            #c.has_code = code.Code

    '''
    VARIABLES
    '''

    variable_class = onto['Variable']
    for variable in DatamodelAttribute.objects.all():

        #variable = variable.Attribute

        topic_from_sheet = variable.Topic
        topic_class = onto[topic_from_sheet]
        if not topic_class:
            # Search for label instead
            topic_class = onto.search_one(label=topic_from_sheet)
        if not topic_class:
            print(variable)
            break
        c = get_or_create(onto, variable.Attribute, variable_class)
        c.label = variable.Attribute

        c.is_a.append(onto.has_topic.only(topic_class))
        if variable.Topic_Description:
            topic_class.has_description.append(variable.Topic_Description)
        umbrella_term_from_sheet = variable.Umbrella
        if umbrella_term_from_sheet:
            umbrella_class = get_or_create(
                onto, umbrella_term_from_sheet, onto.Umbrella_term)
            if variable.Umbrella_Description:
                umbrella_class.has_description = variable.Umbrella_Description
            if umbrella_class:
                c.is_a.append(onto.has_umbrella.only(umbrella_class))

        description_from_sheet = variable.Attribute_Description
        if description_from_sheet:
            c.has_description = description_from_sheet
        tooltip_from_sheet = variable.Attribute_Tooltip
        if tooltip_from_sheet:
            c.has_tooltip = tooltip_from_sheet
        datatype_from_sheet = variable.Datatype
        if datatype_from_sheet:
            if datatype_from_sheet == "float":
                c.is_a.append(onto.has_datatype.only(float))
            elif datatype_from_sheet == "int":
                c.is_a.append(onto.has_datatype.only(int))
            elif datatype_from_sheet == "string":
                c.is_a.append(onto.has_datatype.only(str))
            elif datatype_from_sheet == "date":
                c.is_a.append(onto.has_datatype.only(datetime.date))
            elif datatype_from_sheet == "code":
                datatype_class_in_onto = onto.datatype
                d_code_class = get_or_create(onto, 'd_code', datatype_class_in_onto)
                d_code_class.label = "code"
                if d_code_class:
                    c.is_a.append(onto.has_datatype.only(d_code_class))
            else:
                datatype_class_in_onto = onto.datatype
                if datatype_class_in_onto:
                    datatype_class = get_or_create(
                        onto, datatype_from_sheet, datatype_class_in_onto)
                    c.is_a.append(onto.has_datatype.only(datatype_class))
        domain_from_sheet = variable.Domain
        if domain_from_sheet:
            if datatype_from_sheet == "code":
                helper_class_code = get_or_create(onto, domain_from_sheet, code_class)
                c.has_range = "range_of:"  + str(helper_class_code.iri).split("#")[1]

            else:
                c.has_range = domain_from_sheet

        unit_from_sheet = variable.Unit.Unit
        if unit_from_sheet:
            unit_class = get_or_create(onto, unit_from_sheet, onto.Unit)
            c.is_a.append(onto.has_unit.only(unit_class))

    '''
    SOURCES
    '''

    source_class = onto['Source']
    for source in DatamodelSource.objects.all():
        if source.Abbreviation:
            c = get_or_create(
                onto, source.Abbreviation, source_class)
            if source.Source:
                c.label = source.Source

    '''
    CODE MAPPING
    '''

    code_mapping_class = onto['Code_mapping']
    for code_mapping in DatamodelCodeMapping.objects.all():

        if code_mapping.Code_Mapping:
            c = get_or_create(
                onto, str(code_mapping.Code_Mapping), code_mapping_class)
            c.label = code_mapping.Code_Mapping

            if code_mapping.Source_Value_Description:
                c.has_description = code_mapping.Source_Value_Description
            if code_mapping.Target_Equivalent and code_mapping.Source_Value:
                c.has_code_key_value_pair.append(str(code_mapping.Source_Value) + "::" + str(code_mapping.Target_Equivalent))

    '''
    VARIABLE MAPPING
    '''

    external_var_class = onto['External_variable']
    for variable_mapping in DatamodelAttributeMapping.objects.all():
        if variable_mapping.Source_Attribute and variable_mapping.Target_Attribute:
            c = get_or_create(onto, str(variable_mapping.Source_Attribute) , external_var_class)
            c.has_source_variable = variable_mapping.Source_Attribute
            target_variable = get_or_create(onto, variable_mapping.Target_Attribute.Attribute, variable_class)
            c.is_a.append(onto.maps_to.only(target_variable))
            if variable_mapping.Source:
                c.is_a.append(onto.has_source.some(get_or_create(onto, variable_mapping.Source.Abbreviation, source_class)))
            if variable_mapping.Transformation:
                transformation = variable_mapping.Transformation
                if onto[transformation]:
                    c.is_a.append(onto.has_code_mapping.only(onto[transformation]))
                else:
                    c.has_formula = transformation

    '''
    MEASUREMENTS
    '''
    measurement_variable = onto['measurement_variable']
    for measurement in Measurement.objects.all():
        pass

    rand = str(random.random())
    onto.save(file = os.path.dirname(os.path.realpath(
        __file__)) + "/" + "../" + settings.OWL_LOCATION + "/CCDM" + rand + ".owl")
    f = open(os.path.dirname(os.path.realpath(
        __file__)) + "/" + "../" + settings.OWL_LOCATION + "/CCDM"+ rand + ".owl", 'rb')

    response = FileResponse(f)
    response['Content-Disposition'] = 'attachment; filename="CCDM.owl"'
    return response

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_semantic_asset(request):
    data = request.data
    name = data.get('label')
    provenance = data.get('provenenance')
    description = data.get('description')
    if not name or not description:
        return JsonResponse({'message': 'Name and description must be provided!'})

    if SemanticAsset.objects.filter(name=name).exists():
        return JsonResponse({'message': 'Name is already taken!'})
    else:
        semantic_asset = SemanticAsset()
        semantic_asset.name = name
        semantic_asset.description = description
        if provenance:
            semantic_asset.provenenace = provenance
        semantic_asset.save()
        return JsonResponse({'message': 'ok'})


def get_header_indeces(request, act_colnames, exp_colnames, main_msg_queue):
    print(f"COLNAMES ACTUAL :{act_colnames}")
    indices = {n: catch(lambda: act_colnames.index(n)) for n in exp_colnames}
    misses = [re.findall('\'([^\']*)\'', miss.args[0])[0] for miss in indices.values() if
              miss.__class__ is ValueError]
    #print(indices)
    if misses:
        msg = "Could not find following column headers (format corrupt?):\n" + "\n".join(misses)
        print(msg)
        throw_or_enqueue("error", msg, main_msg_queue)
        gui_messages.error(request, msg)
        return False
    return indices

def get_target_from_datamodel(request, attr, targets, source, main_msg_queue, mapping_only=False):
    source_model = DatamodelSource.objects.filter(Source=source)[0]
    mappings = DatamodelAttributeMapping.objects.filter(Source_Attribute=attr, Source=source_model)
    # print(f"mappings")
    #print(mappings)
    core = DatamodelAttribute.objects.filter(Attribute=attr)
    # print(f"core")
    #print(core)
    if mappings:
        if core:
            #gui messages warning
            msg = "Attribute name " + str(attr) + " known in both data model's core set and mapping table (latter preferred)!"
            throw_or_enqueue("warning", msg, main_msg_queue)
            print(f"Warning: Attribute name {attr} known in both data model's core set and mapping table (latter preferred)!")
        else:
            #gui messages info
            msg = "Attribute name " + str(attr) + " found in mapping table"
            throw_or_enqueue("info", msg, main_msg_queue)
            print(f"Info: Attribute name {attr} found in mapping table.")
        target_set = [m.Target_Attribute for m in mappings]
    elif core:
        if mapping_only:
            #gui messages error
            msg = "Attribute name " + str(attr) + " unknown to data model mappings"
            throw_or_enqueue("error", msg, main_msg_queue)
            print(f"Error: Attribute name {attr} unknown to data model mappings!")
            return False
        target_set = core
    else:
        #gui messages Error
        msg = "Attribute name " + str(attr) + " unknown to data model (neither core set nor mapping table)"
        throw_or_enqueue("error", msg, main_msg_queue)
        print(f"Error: Attribute name {attr} unknown to data model (neither core set nor mapping table)!")
        return False
    targets[attr] = target_set
    return target_set


def check_date_in_each_row(meta, row_date, line_counter, request, main_msg_queue):

    date_range = [meta['min_date'], meta['max_date']]
    if 'error_mode' in meta.keys():
        sanitize_trigger = (meta['error_mode'] == "sanitize" or meta['error_mode'] == "propose")
    else:
        sanitize_trigger = False

    if row_date == '*':
        static = True
        entity_date = row_date
    else:
        static = False
        entity_date = check_date(row_date,
                                main_msg_queue,
                                sanitize=sanitize_trigger,
                                date_range=date_range
        )

    #check for the below if not condition
    if not entity_date:
        #display error message in front end
        throw_or_enqueue("error", "not entity date", main_msg_queue)
        print(f"not entity date")
        pass
    elif entity_date != row_date:
        msg = "Line " + str(line_counter) + ": " + row_date + " => " + entity_date + " (DATE)."
        if "error_mode" in meta.keys() and meta['error_mode'] == 'propose':
            #check async to syn and broken lines
            throw_or_enqueue("warning", "Sanitizing of 'DATE' successful, while proposal requested", main_msg_queue)
            print(f"Status_message: Sanitizing of 'DATE' successful, while proposal requested.")
            msg1 = msg + " PROPOSAL"
            throw_or_enqueue("warning", msg1, main_msg_queue)
            print(f"Status_message: {msg} PROPOSAL")
            pass
        else:
            #check async and sync and broken lines
            msg1 = msg + " SANITIZED"
            throw_or_enqueue("warning", msg1, main_msg_queue)
            print(f"Status_message: {msg} SANITIZED")
            pass

    return entity_date, static


def import_data_sanitization(meta, request, sheet, main_msg_queue):

    eav_col_names = ["PID", "DATE","VISIT","ATTRIBUTE", "VALUE", "PROVENANCE"]
    date_range = [meta['min_date'], meta['max_date']]
    if 'error_mode' in meta.keys() and (meta["error_mode"] == "sanitize" or meta["error_mode"] == "propose"):
        sanitize = True
    else:
        sanitize = False
    chunk_size = 1000
    col_names = list(sheet.colnames)
    print(f"COLNAMES: {col_names}")
    colname_mapping =   {"PID": "PID",
                         "DATE": "TS",
                         "VISIT": "VISIT",
                         "ATTRIBUTE": "ITEM",
                         "VALUE": "VALUE",
                         "PROVENANCE": "PROVENANCE"}
    colname_mapping = {}

    if 'write_mode' in meta.keys() and meta['write_mode'] == "sweep":
        throw_or_enqueue("warning", "This will delete all data contained in the current database", main_msg_queue)
        print(f"Status message: This will delete all data contained in the current database.")
        DataPointsVisit.objects.all().delete()

    if colname_mapping:
        indices = get_header_indeces(request, col_names, [colname_mapping[x] for x in eav_col_names], main_msg_queue)
        if indices:
            for c in eav_col_names:
                indices[c] = indices.pop(colname_mapping[c])
    else:
        indices = get_header_indeces(request, col_names, eav_col_names, main_msg_queue)

    if not indices:
        indices = {'PID': 0, 'DATE': 1,"VISIT": 2,  'ATTRIBUTE': 3, 'VALUE': 4, 'PROVENANCE': 5}
        #send error message to front end
        throw_or_enqueue("error", "Corrupt EAV++ header line - please check log for details", main_msg_queue)
        print(f"Error message: Corrupt EAV++ header line - please check log for details.")
        #return
        #return JsonResponse({'message':"ERROR: Corrupt EAV++ header line - please check log for details."})
        # implement http response oder json msg?
    #print(indices)
    #print(sheet.column)
    # undo auto-detection/casting of data types
    for cn in indices.keys():
        sheet.column.format(cn, str)

    targets = {}                # collector; saves DB requests
    verified_UCUM_units = {}    # index; saves server requests
    value_conversions = {}      # collector; saves server requests
    eav_array = [eav_col_names]  # collector; saves EAV lines for chunked database uploads
    bulk_mgr = BulkCreateManager(chunk_size=chunk_size)
    line_counter = 0
    line_cnt_success = 0
    row_count = len(list(sheet))
    for index, row in enumerate(sheet):
        if index > 80000:
            break

        cache.set(meta['_id'], {'status': str(index/row_count)})

        line_counter += 1
        print(str(line_counter) + ": ['" + "', '".join(row) + "']")

        row_pid = row[indices["PID"]]
        row_date = row[indices["DATE"]]
        row_attr = row[indices["ATTRIBUTE"]]
        row_value = row[indices["VALUE"]]
        row_visit = row[indices['VISIT']]

        # print(row_pid, row_date, row_attr, row_value)

        #check date in each row
        entity_date, static = check_date_in_each_row(meta, row_date, line_counter, request, main_msg_queue)

        # check uniqueness of EAV entry for SOURCE
        entries = list()
        if 'write_mode' in meta.keys() and meta["write_mode"] != "sweep":
            entries = DataPointsVisit.objects.filter(SOURCE=meta["source"],
                                                PID=row_pid,
                                                DATE=entity_date,
                                                ATTRIBUTE=row_attr,
                                                )
            if entries:
                eav = row[indices["PID"]] + ";" + entity_date + ";" + row[indices["ATTRIBUTE"]] + ";" + row[indices["VALUE"]]
                if 'write_mode' in meta.keys() and meta["write_mode"] == "unique":
                    #async to sync messages
                    msg = "Duplicate entry while 'unique' requested - skipping line #" + str(line_counter)
                    throw_or_enqueue("error", msg, main_msg_queue)
                    print(f"Status_message: Duplicate entry while 'unique' requested - skipping line # {line_counter}...")
                    continue
                elif 'write_mode' in meta.keys() and meta["write_mode"] == "update":
                    #async to sync messages
                    msg = "Existing entry will be replaced with input line #" + str(line_counter)
                    throw_or_enqueue("warning", msg, main_msg_queue)
                    print(f"Status_message: Existing entry will be replaced with input line # {line_counter}...")
                    continue
                elif 'write_mode' in meta.keys() and meta["write_mode"] == "add" and static:
                    #async to sync messages
                    msg = "Existing time-less entry - addition not possible! Skipping line #" + str(line_counter)
                    throw_or_enqueue("error", msg, main_msg_queue)
                    print(f"Status_message: Existing time-less entry - addition not possible! Skipping line #{line_counter}...")
                    continue

        if not row_attr in targets:
            #check for mapping_only element of below function

            target_list = get_target_from_datamodel(request, row_attr, targets, meta["source"], main_msg_queue)
            if not target_list:
                continue

        # ATTRIBUTE from SOURCE might point to multiple TARGETs
        for target in targets[row_attr]:
            if target.Topic == "master":
                entity_date = date_range_global[0]
            else:
                entity_date, _ = check_date_in_each_row(meta, row[indices["DATE"]], line_counter, request,main_msg_queue)
                if not entity_date:  # no valid DATE - row data is useless => skip line
                    #release message
                    msg = "no valid DATE - row data is useless => skip line"
                    throw_or_enqueue("warning", msg, main_msg_queue)
                    print(f"no valid DATE - row data is useless => skip line")
                    continue
                elif entity_date != row[indices["DATE"]]:
                    msg = "Line " + str(line_counter) + ": " + row[indices["DATE"]] + " => " + entity_date + " (DATE)"
                    if "error_mode" in meta.keys() and meta["error_mode"] == "propose":
                        #async to sync
                        msg1 = "Sanitizing of 'DATE' successful, while proposal requested line " + str(line_counter)
                        throw_or_enqueue("warning", msg1, main_msg_queue)
                        print(f"Status_message: Sanitizing of 'DATE' successful, while proposal requested line {line_counter}")
                        msg2 = msg + " PROPOSAL"
                        throw_or_enqueue("warning", msg2, main_msg_queue)
                        print(f"Status_message: {msg} PROPOSAL")
                        continue
                    else:
                        #async to sync
                        msg2 = msg + " SANITIZED"
                        throw_or_enqueue("warning", msg2, main_msg_queue)
                        print(f"Status_message: {msg} SANITIZED")

            # get EAV value and check
            if not row[indices["VALUE"]]:
                # async to sync
                msg = "Value for attribute " + row_attr + " is empty. Skipping line " + str(line_counter)
                throw_or_enqueue("warning", msg, main_msg_queue)
                print(f"Status_message: Value for attribute {row_attr} is empty. Skipping line {line_counter}")
                #release message
                break  # no valid entry given, skip complete EAV line

            # check uniqueness of EAV entry for SOURCE
            entries = list()
            if 'write_mode' in meta.keys() and meta["write_mode"] != "sweep":
                entries = DataPointsVisit.objects.filter(SOURCE=meta["source"],
                                                    PID=row_pid,
                                                    DATE=entity_date,
                                                    ATTRIBUTE=row_attr,
                                                    )
                if entries:
                    eav = row_pid + ";" + entity_date + ";" + row_attr + ";" + row_value
                    if 'write_mode' in meta.keys() and meta["write_mode"] == "unique" and row_value not in entries.values_list("VALUE", flat=True):
                        #async to sync
                        msg = "Duplicate entry while 'unique' requested - skipping line " + str(line_counter + 1)
                        throw_or_enqueue("warning", msg, main_msg_queue)
                        print(f"Status_message: Duplicate entry while 'unique' requested - skipping line {line_counter + 1} ")
                        continue
                    elif 'write_mode' in meta.keys() and meta["write_mode"] == "update" and row_value not in entries.values_list("VALUE", flat=True):
                        #async to sync
                        msg = "Existing entry will be replaced with input line " + str(line_counter+1) + " eav"
                        throw_or_enqueue("warning", msg, main_msg_queue)
                        print(f"Status_message: Existing entry will be replaced with input line {line_counter + 1} eav ")
                    elif 'write_mode' in meta.keys() and meta["write_mode"] == "add" and target.Topic == "master":
                        #async to sync
                        msg = "Existing time-less entry - addition not possible! Skipping line " + str(line_counter + 1)
                        throw_or_enqueue("warning", msg, main_msg_queue)
                        print(f"Status_message: Existing time-less entry - addition not possible! Skipping line {line_counter + 1} ")
                        #release message
                        continue

            #TODO: move duplicate check AFTER transformation and sanitizing

            #TODO: [DEF] transform value according to data model definitions
            source_model = DatamodelSource.objects.filter(Source=meta["source"])[0]
            try:    # code mappings
                ams = DatamodelAttributeMapping.objects.filter(Source_Attribute=row[indices["ATTRIBUTE"]],
                                                                Target_Attribute=target,
                                                                Source=source_model)
                cms = DatamodelCodeMapping.objects.filter(Code_Mapping=ams[0].Transformation)
                conversion_map = {m.Source_Value: m.Target_Equivalent for m in cms}
                #print(conversion_map)
                if conversion_map:
                    try:
                        row_value = conversion_map[row_value]
                    except KeyError:
                        throw_or_enqueue("warning", "Value '" + row_value + "' not included in code mapping '" + ams[0].Transformation + "'!")
            except:  # formulas
                pass        # ToDo: implement
            #check for further conversion maps improvement

            vars, sanitized = ensure_datatype_and_domain_fit([row_value],
                                                            target,
                                                            main_msg_queue,
                                                            date_range=date_range,
                                                            sanitize=sanitize,
                                                            verified_UCUM_units=verified_UCUM_units,
                                                            value_conversions=value_conversions)

            if vars is False:  # no valid VALUE - row data is useless
                # async to sync
                msg = "VALUE for line " + str(line_counter+1) + " appears invalid according to definitions for attribute " + str(target.Attribute)
                throw_or_enqueue("error", msg, main_msg_queue)
                print(f"Status_message: VALUE for line {line_counter + 1} appears invalid according to definitions for attribute {target.Attribute}")
                # release message
                continue
            elif vars[0] != row_value and sanitized:
                msg = "Line " + str(line_counter + 1) + ": " + row_value + " => " + vars[0]
                if 'error_mode' in meta.keys() and meta["error_mode"] == "propose":
                    #async to sync
                    throw_or_enqueue("warning", "Sanitizing of 'VALUE' successful, while proposal requested", main_msg_queue)
                    print(f"Status_message: Sanitizing of 'VALUE' successful, while proposal requested.")
                    msg1 = msg + " PROPOSAL"
                    throw_or_enqueue("warning", msg1, main_msg_queue)
                    print(f"Status_message: {msg} PROPOSAL")
                    continue
                else:
                    #async to sync
                    msg1 = msg + " SANITIZED"
                    throw_or_enqueue("warning", msg1, main_msg_queue)
                    print(f"Status_message: {msg} SANITIZED")
            var = vars[0]
            line_cnt_success += 1

            if 'error_mode' in meta.keys() and meta["error_mode"] == "strict" and line_counter + 1 != line_cnt_success:
                #release message
                # todo: rollback
                #async to sync
                msg = "Failed to read data - found errornous entries after input line " + str(line_counter) + " " + str(row)
                throw_or_enqueue("error", msg, main_msg_queue)
                print(f"Error_message: Failed to read data - found errornous entries after input line {line_counter} {str(row)}")
                return JsonResponse({'message' :"Failed to read data - found errornous entries after input line #" + str(
                    line_counter) + " (" + str(row) + ").",
                    'msg_queue': main_msg_queue})

            if 'write_mode' in meta.keys() and meta["write_mode"] == "update" and len(entries) > 0:    # existing EAV entry: update immediately if possible
                if len(entries) > 1:
                    #async to sync
                    throw_or_enqueue("warning", "Multiple entries found while update (with one datapoint) requested - not possible, skipping", main_msg_queue)
                    print(f"Status_message: Multiple entries found while update (with one datapoint) requested - not possible, skipping...")
                    continue
                if not entries[0].VALUE == var or not entries[0].PROVENANCE == row[indices["PROVENANCE"]]:
                    entries[0].VALUE = var
                    entries[0].PROVENANCE = row[indices["PROVENANCE"]]
                    entries[0].save()
            else:  # new EAV entry: store to buffer array
                #print(meta["source"])
                source_obj = DatamodelSource.objects.filter(Source=meta["source"])[0]
                eav_array.append([row_pid, entity_date, row_visit, target.Attribute, var,
                                    row[indices["PROVENANCE"]], source_obj])
                bulk_mgr.add(DataPointsVisit(PID=row_pid,
                                        DATE=entity_date,
                                        TIMESTAMP = entity_date,
                                        ATTRIBUTE=target.Attribute,
                                        VALUE=var,
                                        VISIT=row_visit,
                                        PROVENANCE=row[indices["PROVENANCE"]],
                                        SOURCE=source_obj,
                                        ))
        # END OF LOOP over 'targets[row_attr]
    #print("BEFORE BULK")
    bulk_mgr.done()
    #print(bulk_mgr.getcommitted(DataPoints))
    #async to snc
    msg = "Here I am. Successfully read " + str(line_cnt_success) + " entries into database (skipped " + str(line_counter - line_cnt_success) + " lines)."
    throw_or_enqueue("info", msg, main_msg_queue)
    print(f"Status_message: Here I am. Successfully read "
                                                + str(line_cnt_success)
                                                + " entries into database (skipped "
                                                + str(line_counter - line_cnt_success)
                                                + " lines).")
    cache.set(meta['_id'], {'status':'done', 'message' :"Here I am. Successfully read "
                                    + str(line_cnt_success)
                                    + " entries into database (skipped "
                                    + str( line_counter - line_cnt_success )
                                    + " lines).",
                         'msg_queue': main_msg_queue})
    return





def upload_basic(df,id, source):
    created_ols_count = 0 
    attributes_not_found = set()
    patients_all = set()
    attributes_all = set()
    count = len(df.index)
    all_attributes = DatamodelAttribute.objects.all()
    all_mappings = DatamodelAttributeMapping.objects.all()
    all_code_mappings = DatamodelCodeMapping.objects.all()
    #print(id)
    cache.set(id, {'status': "working", "message": "starting...", "done": 0, "total": count, "not_found": list(attributes_not_found)})
    for index, row in df.iterrows():
        cache.set(id, {'status': "working", "message": "processing...", "done": int(index*100/count), "total": count, "not_found": list(attributes_not_found)})
        
        attr = row["ATTRIBUTE"]
        val = row["VALUE"]
        pid = row["PID"]
        
        patients_all.add(pid)
        attributes_all.add(attr)
        
        ## DISTINGUISH BETWEEN DATE AND TIMESTAMP
        if "DATE" in row.keys():

            ts_arr = row["DATE"].split("-")
            ts = datetime.datetime(int(ts_arr[0]), int(ts_arr[1]), int(ts_arr[2]))
            datapoint = BasicDataPoint(timestamp=str(make_aware(ts)), variable_raw=attr, value=val, pid=pid)
        else:
            ts = row['TIMESTAMP']
            datapoint = BasicDataPoint(timestamp=str(ts), variable_raw=attr, value=val, pid=pid)

        has_found, created_new_from_ols = datapoint.set_variable(all_attributes, all_mappings, all_code_mappings) ## finding the actual variable maybe search through ols
        if not has_found:
            attributes_not_found.add(attr) 
           
        if created_new_from_ols:
            created_ols_count +=1
        if source:
            src = DatamodelSource.objects.filter(Source = source)
            if src.exists():

                datapoint.source = src[0]
        datapoint.save()
    cache.set(id, {'status': "done", "message": f"Done! \n Found {len(attributes_all)} variables from {len(patients_all)} patients.", "done": 100, "total": count, "not_found": list(attributes_not_found), "ols_count": created_ols_count})
    return 
    





@api_view(["POST"])
def upload_basicdata(request):
    data = request.data
    file = request.FILES['file']
    f = UserFile.objects.create(file=file, name=file.name)

    
    try:
        df = pd.read_csv(f.file.path, sep=";")
        if len(df.columns) <2:
            raise
    except:
        df = pd.read_csv(f.file.path)
    
    id = data['_id']
    source = data["_source"]
    t = threading.Thread(target=upload_basic, args=[df,id, source])
    t.start()

    

    return JsonResponse({"message": "Successfully uploaded data. Your data is now getting processes!"})


@api_view(["GET"])
def get_all_unmapped(request):
    datapoints_to_return = set()
    for datapoint in BasicDataPoint.objects.filter(variable__isnull=True):
        datapoints_to_return.add(datapoint.variable_raw)
    return JsonResponse({'datapoints': list(datapoints_to_return)})



@api_view(["POST"])
def post_mapping_basic(request):
    source_attr = request.data["source_attribute"]
    target_attr = request.data["target"]
    #print(target_attr)
    source = request.data["source"]

    source = DatamodelSource.objects.filter(Source=source)
    if not source.exists():
        return JsonResponse({"message": "No such Source available!"})
    source = source[0]

    ## Check case if variable should be imported from OLS

    if settings.USE_OLS and len(target_attr.split('|'))>2:
        ## import from ols
        label = target_attr.split('|')[0]
        ontology = target_attr.split('|')[1]
        iri = target_attr.split('|')[2]
        print("Searching through OLS.")

        ## check if that is already imported 
        if DatamodelAttribute.objects.filter(IRI=iri).exists():
            print("No need to import from OLS. Already in the backend.")
            attr = DatamodelAttribute.objects.get(IRI=iri)
        else:


            description = " "
            
                
            url_encoded_ = urlencode({'test':urlencode({'test':iri}).split("=")[1]}).split("=")[1] ## double encode url 
            term_query = dict(requests.get(settings.OLS_URL + f"/ols/api/ontologies/{ontology}/terms/" + url_encoded_).json())
            if 'description' in term_query.keys() and term_query['description'] != None: ## try to grab a description
                description = term_query['description']
                
            ## Create a new variable 
            none_unit = DatamodelUnit.objects.filter(Unit="None")[0]
            attr = DatamodelAttribute(Attribute=label, Attribute_Description=description, Attribute_Tooltip=label, IRI=iri ,Unit=none_unit, Datatype="string")
                
            attr.save()
        target_attr = attr
    else:
        target_attr = DatamodelAttribute.objects.filter(Attribute=target_attr)
        if not target_attr.exists():
            return JsonResponse({"message": "No such Target Attribute available!"})
        target_attr = target_attr[0]
    mapping = DatamodelAttributeMapping(Source = source , Target_Attribute=target_attr, Source_Attribute=source_attr)
    try:
        mapping.save()
    except Exception:
        print(f"Traceback: {traceback.format_exc()}")
        th = threading.Thread(target=map_datapoints_async, args=(source_attr,))
        print("Starting Thread for mapping datapoints....")
        th.start()
        print("Started Thread!")
        return JsonResponse({"message": "Something went wrong during saving the mapping. Please try again later!"})

    th = threading.Thread(target=map_datapoints_async, args=(source_attr,))
    print("Starting Thread for mapping datapoints....")
    th.start()
    print("Started Thread!")

    return JsonResponse({"message": "ok"})


def map_datapoints_async(source_attr):
    print(source_attr)
    ## map the datapoints 
    attr_all = DatamodelAttribute.objects.all()
    map_all = DatamodelAttributeMapping.objects.all()
    code_map_all =  DatamodelCodeMapping.objects.all()
    for datapoint in BasicDataPoint.objects.filter(variable_raw=source_attr):

        found, ols = datapoint.set_variable(attr_all,map_all, code_map_all)
        print(f"Filled variable status : {found}. For variable : {source_attr}")
        if not found:
            print("Something went wrong while finding the mapping. Please try again later!")
        else:
            datapoint.save()
    print(f"Done mapping datapoints for {source_attr}...")



@api_view(["GET"])
def get_attr_by_sources(request):
    attr_by_source = {}
    for mapping in DatamodelAttributeMapping.objects.all():
        src = mapping.Source.Abbreviation 
        if src in attr_by_source.keys():
            attr_by_source[src] +=1
        else:
            attr_by_source[src] =1
    return JsonResponse({"attr_by_src": attr_by_source})



########
#
# This performes a nearest neighbor seaerch throughout the complete database based on the edit distance (Levenshtein)
#
#
#
########


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def string_distance(s1,s2):

    d = editdistance.eval(s1,s2)
    return d

@api_view(['GET'])
def get_nearest_neighbor_attribute(request):
    attribute = request.GET.get("attribute")
    INCLUDED_CHECK = True
    CAMELCASE_CHECK = False
    UNDERSCORE_SPLIT = False
    ##  make initial candidate 
    all_attributes = DatamodelAttribute.objects.all()
    candidate = all_attributes[0].Attribute
    distance = string_distance(attribute,candidate)
    ## bruteforece loop over all attributes and find a better one 


     ## check if included 
    if INCLUDED_CHECK:
        for attr in all_attributes:
            if attr.Attribute in ["Yes", "YES", "No", "NO", "Nicht bekannt"]:
                continue
            if str(attribute) in str(attr.Attribute) or str(attribute) in str(attr.Attribute_Description.split(";")):
                candidate = attr
                return JsonResponse({'message': 'ok', 'candidate': candidate.Attribute, "distance": 0.81})
    for attr in all_attributes:
        dist = string_distance(attr.Attribute,attribute)

        if dist < distance:
            candidate = attr
            distance = dist
    if distance > 0.66*len(attribute):
        if request.GET.get('ols') == "true":
            ## searching in OLS
            print("Search through OLS")
            ols_response = requests.get(settings.OLS_URL + f"/ols/api/suggest?q={attribute}&rows=10").json()['response']
            print(f"Making query : {settings.OLS_URL} + /ols/api/suggest?q={attribute}&rows=10")
            suggestion = ""
            if ols_response['numFound'] > 0:
                for autosuggest in ols_response["docs"]:
                    if autosuggest["autosuggest"] is not None and autosuggest["autosuggest"] != "":
                        suggestion = autosuggest["autosuggest"]
                        break
            
            
            if suggestion == "":
                return JsonResponse({'message': 'ok', 'candidate': "--no-candidate--"})

            ## grabbing the result
            ols_response = requests.get(settings.OLS_URL + f"/ols/api/select?q={suggestion}&rows=10").json()['response']
            if ols_response['numFound']>0:
                
                for i in range(0, ols_response['numFound']):
                    result = ols_response['docs'][i] ## Take the first one in the result 
                    iri = result['iri']
                    ontology = result["ontology_name"]
                    label = result['label']
                    url_encoded_ = urlencode({'test':urlencode({'test':iri}).split("=")[1]}).split("=")[1] ## double encode url 
                    term_query = dict(requests.get(settings.OLS_URL + f"/ols/api/ontologies/{ontology}/terms/" + url_encoded_).json())
                    if 'description' in term_query.keys() and term_query['description'] != None and 'label' in term_query.keys():

                        return JsonResponse({'message': 'ok', 'candidate': label + "|" + ontology + "|" + iri })
                return JsonResponse({'message': 'ok', 'candidate': ols_response['docs'][0]['label'] + "|" + ols_response['docs'][0]["ontology_name"] + "|" + ols_response['docs'][0]["iri"] })
       
        if CAMELCASE_CHECK:
            if UNDERSCORE_SPLIT:
                s = attribute.split('_')
                camel_split = [camel_case_split(sub) for sub in s]

                splitted = [item for sublist in camel_split for item in sublist]
                
            else:
                splitted = camel_case_split(attribute)
            for attr in all_attributes:
                for s in splitted:
                    if str(s).lower() == str(attr).lower() or s in attr.Attribute_Description:
                        candidate = attr
                        return JsonResponse({'message': 'ok', 'candidate': candidate.Attribute, "distance": 0.81})
        return JsonResponse({'message': 'ok', 'candidate': "--no-candidate--"}) ## if more then 66% of the string has to be changed
    return JsonResponse({'message': 'ok', 'candidate': candidate.Attribute, "distance": 1- (distance/len(attribute))})




@api_view(['GET'])
def get_sematic_assets_all(request):

    ret = []
    for asset in SemanticAsset.objects.all():
        ret.append(asset.name)
    print(ret)
    return JsonResponse({'assets': ret})


@api_view(['POST'])
def post_owl_file(request):
    print(request.file)
    return JsonResponse({"message": "ok"})


@api_view(["POST"])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_measurement(request):

    object_of_measurement = request.data['object']
    location_of_measurement = request.data['location']
    method_of_measurement = request.data['method']
    measurement = Measurement.objects.create()
    measurement.object_of_measurement = MeasurementObject.objects.create(label=object_of_measurement)
    measurement.location_of_measurement = MeasurementLocation.objects.create(label=location_of_measurement)
    measurement.method_of_measurement = MeasurementMethod.objects.create(label=method_of_measurement)
    measurement.save()
    return JsonResponse({"message": "ok"})
