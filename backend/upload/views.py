import calendar
import csv
from datetime import date, datetime
import traceback

import django_excel as excel

from upload.forms import DataUploadFileForm, DatamodelUploadFileForm
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

from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view,  permission_classes
from rest_framework.permissions import IsAuthenticated

from api.views import use_token_auth

date_range_global = ["1875-01-01", datetime.today().strftime('%Y-%m-%d')]
ucum_api_url = "http://ucum.nlm.nih.gov/ucum-service/v1"
from pyucum.ucum import *
import urllib
import xml.etree.ElementTree as ET
from collections import Counter


from django.contrib.auth.decorators import login_required

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
from upload.models import DataPoints, DataPointsVisit, VisitsDataSet
# from pyexcel import DjangoRenderer
from django.views.decorators.http import require_http_methods
# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages as gui_messages
from django.contrib.messages import get_messages
from threading import Thread
import time
import pickle
import pandas as pd
import xlrd
import json
from pymongo import MongoClient


true_replacements = [True, "True", "TRUE", "true"]
false_replacements = [False, "False", "FALSE", "false"]


def drop_tables():
    DataPoints.objects.all().delete()
    DatamodelAttributeMapping.objects.all().delete()
    DatamodelCodeMapping.objects.all().delete()
    DatamodelAttribute.objects.all().delete()
    DatamodelCode.objects.all().delete()
    DatamodelUnit.objects.all().delete()
    DatamodelSource.objects.all().delete()


def drop_data_table():
    DataPoints.objects.all().delete()


def index(request):
    return HttpResponse("Hello, world. You're at the data upload index.")






# helper function for handling exceptions in list comparisons
def catch(func, handle=lambda e: e, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return handle(e)


### Datamodel section: all functions for reading in the datamodel definitions from an Excel book and imprinting the database ###

# helper; ToDo: should be replaced by function automatically determining the dependencies by the models.py file's contents
def get_dependency_levels():
    model_dependency_levels = [[DatamodelSource,
                                DatamodelUnit,
                                DatamodelCode,
                                DatamodelCodeMapping],
                               [DatamodelAttribute],
                               [DatamodelAttributeMapping]]
    return model_dependency_levels


# helper; ToDo: should be replaced by function receiving the relevant information by a data steward's form inputs on the upload page
def get_mapping_information():
    model2sheetMappings = {DatamodelAttribute: 'Attributes',
                           DatamodelAttributeMapping: 'Attribute_Mappings',
                           DatamodelCodeMapping: 'Code_Mappings',
                           DatamodelCode: 'Codes',
                           DatamodelUnit: 'Units',
                           DatamodelSource: 'Sources'}
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
                   }
    header_line = 0

    return model2sheetMappings, colname_map, header_line


# read sheet from Excel book    #ToDo: remove (usage deprecated)
def get_sheet_with_colnames(filehandle, sheet_name, header_line=0):
    sheet = filehandle.get_sheet(sheet_name=sheet_name, start_row=header_line)
    sheet.colnames = sheet.row[0]
    del sheet.row[0]
    return sheet


def get_bool_fields(model):
    return [f.name for f in model._meta.fields if f.__class__.__name__ == 'BooleanField']


def get_char_fields(model):
    return [f.name for f in model._meta.fields if f.__class__.__name__ == 'CharField']


def get_relations(model):
    return [f for f in model._meta.fields if f.is_relation]


def foreign_key_replacement(request, target_model, target_colname, column, blank_allowed=False):  # toDo: enable reporting
    #print("###### target_model ######")
    #print(target_model)
    #print("###### target_colname ######")
    #print(target_colname)
    i = 0
    while i < len(column):
        entry = column[i]
        #print("###### entry ######")
        if not entry:
            if not blank_allowed:
                gui_messages.error(request, "Foreign Key field '" + target_colname
                                   + "' could not be served (empty source file field in input line "
                                   + str(i + 2) + ")!")
                return False
            column[i] = ''
        else:
            try:
                targetObj = target_model.objects.filter(**{target_colname: entry})[0]
            except IndexError:
                gui_messages.error(request, "Foreign Key field '" + target_colname
                                   + "' could not be served (key '" + entry + "' could not be resolved)!")
                return False
            column[i] = targetObj
        i += 1
    return column


def setup_foreign_keys_in_sheet(request, sheet, model):
    relations = get_relations(model)
    i = 0
    for colname in sheet.colnames:  # iterate over sheet-derived names
        # print("        >>> Working on column '" + colname + "'...")
        # print("        Col len: " + str(len(sheet.column[colname])))
        try:
            fk_index = [r.name for r in relations].index(colname)
            target_model = relations[fk_index].related_model
            target_column = relations[fk_index].to_fields[0]
            gui_messages.info(request, colname + " --> Resolving Foreign Key...")
            #print("### colname ###")
            #print(colname)
            #print("### sheet.column[colname] ###")
            #print(sheet.column[colname])
            #print("### target_model ###")
            #print(target_model)
            #print("### target_column ###")
            #print(target_column)
            #print( "### target_model.objects.all() ###")
            #print( target_model.objects.all())
            blank_allowed = relations[fk_index].blank and relations[fk_index].null
            new_col = foreign_key_replacement(request, target_model, target_column, sheet.column[colname], blank_allowed)
            # print(new_col)
            if not new_col:
                return False
            sheet.column[colname] = new_col
        except ValueError:
            #print("        " + colname)
            # regular_fields
            pass
        i += 1
        # print("        ...done <<<")
    return sheet


# get rid of empty sheet rows
def blank_row(row_index, row):
    result = [element for element in row if element != '']
    return len(result) == 0


def get_error_flag(fault_collector, sheet_name, colname):
    if [error for error in fault_collector[sheet_name][colname].keys() if fault_collector[sheet_name][colname][error]]:
        return True
    else:
        return False


# check column for compliance with model's respective field
def check_regular_field_compliance(request, colname, sheet, model, local_fault_collector):
    col = sheet.column[colname]
    field = model._meta.get_field(colname)
    bool_fields = get_bool_fields(model)
    char_fields = get_char_fields(model)

    ## general: blank AND blank allowed?
    if not (field.blank and field.null) and field._get_default() is None:
        local_fault_collector[colname]["blank"] = [i for i in range(len(col)) if col[i] == ""]

    ## boolean fields: convertable?
    if colname in bool_fields:
        msg_base = "Column '" + colname + "' expected to be either TRUE or FALSE - "
        colset = set([str(y) for y in col])
        diff = colset.difference(["0", "1"])
        if diff:  # contents not read from regular Excel bool cells - try adequate values
            gui_messages.warning(request, msg_base + "found '" + "', '".join(diff) + "'")
            replaced_true = [1 if x in true_replacements else x for x in col]
            replaced_false = [0 if x in false_replacements else x for x in replaced_true]
            diff_again = set(replaced_false).difference(["0", "1"])
            if diff_again:  # replacement failed - refuse
                gui_messages.error(request, msg_base + "could not sanitize value(s) '" + "', '".join(diff) + "'")
                local_fault_collector[colname]["bools"] = [i for i in range(len(replaced_false)) if
                                                           replaced_false[i] in diff_again]
            else:  # replacement successful - exchange column
                sheet.column[colname] = replaced_false

    ## choices fields: in scope?
    choices = field.choices
    if choices:
        local_fault_collector[colname]["choices"] = [i for i in range(len(col)) if
                                                     col[i] not in [t[0] for t in choices]]
        if local_fault_collector[colname]["choices"]:
            gui_messages.error(request, "Values for column '" + colname + "' exceed range of allowed choices:\n"
                               + "\n  ".join([entry[0] + ": " + entry[1] for entry in field.choices]))

    ## character fields: length?
    if colname in char_fields:
        flag = False
        for i in range(len(col)):
            if col[i].__class__.__name__ != "str":
                col[i] = str(col[i])
                flag = True
        if flag:
            sheet.column[colname] = col
        local_fault_collector[colname]["length"] = [i for i in range(len(col)) if len(col[i]) > field.max_length]
        if local_fault_collector[colname]["length"]:
            gui_messages.error(request, "Values for column '" + colname + "' exceed maximum string length of "
                               + str(field.max_length))


# check column for uniqueness, if required by model's respective field
def check_uniqueness_for_column(request, colname, sheet, model, local_fault_collector):
    if colname == model._meta.pk.name or model._meta.get_field(colname)._unique:
        # check duplicates locally in column
        col = sheet.column[colname]
        c = Counter(col)
        duplicates = [item for item in c.keys() if c[item] > 1]
        local_fault_collector[colname]["duplicate"] = [i for i in range(len(col)) if col[i] in duplicates]
        if local_fault_collector[colname]["duplicate"]:
            gui_messages.error(request, "Found duplicate entries in column '" + colname + "' (unique required)")
        # check versus existing DB objects
        existing = model.objects.values_list(colname, flat=True)
        local_fault_collector[colname]["assigned"] = [i for i in range(len(col)) if col[i] in existing]
        if local_fault_collector[colname]["assigned"]:
            gui_messages.error(request,
                               "Found entries in column '" + colname + "' already assigned in database (unique required).")


#def check_transformation(request, colname, sheet, code_mappings, target_obj, local_fault_collector):
def check_transformation(request, colname, sheet, local_fault_collector, target_colname=None):
    db_code_mappings = list(DatamodelCodeMapping.objects.values_list("Code_Mapping", flat=True))
    col = [cell.strip() for cell in sheet.column[colname]]
    if not col == sheet.column[colname]:
        sheet.column[colname] = col
        gui_messages.warning(request,
                             "Removed useless leading/trailing whitespace characters from column '" + colname + "'")
    local_fault_collector[colname]["transformation"] = []
    formulas = ["FORMULA", "MEAN", "RANK", "SUM", "DELTA", "DIV", "PROD", "IF", "VALID_IF", "DRANGE", "DATE", "PASTE" ]
    operators = ["+", "-", "/", "*", "%", "^"]
    pattern = ",|\s|\d" + "|[(" + ''.join(operators) + ")]"
    db_attrs = set(DatamodelAttribute.objects.all().values_list("Attribute", flat=True))
    source_attrs = set(sheet.column["Source_Attribute"])
    for i in range(len(col)):
        if not col[i]:  # transformation is optional...
            continue
        t = col[i]
        if t in db_code_mappings:  # check, if code mapping is compatible to target variable by values
            #print(str(i) + ": " + t + " [CM]")
            cm_targeted_keys = list(set(DatamodelCodeMapping.objects.filter(Code_Mapping=t).values_list("Target_Equivalent", flat=True)))
            try:
                target_obj = DatamodelAttribute.objects.filter(Attribute=target_colname[i])[0]
            except IndexError:
                gui_messages.error(request, "Could not test code mapping '" + t
                                   + "'; target variable '" + target_colname[i] + "' unknown...")
                local_fault_collector[colname]["transformation"].append(i)
            cm_targeted_keys = check_codekey_matches(request, cm_targeted_keys, target_obj.Domain)
            if not cm_targeted_keys:
                gui_messages.error(request, "Could not apply code mapping '" + t
                                   + "'; mismatches targeted attribute's domain '" + target_obj.Attribute + "'...")
                local_fault_collector[colname]["transformation"].append(i)
        else:  # no code mapping found...
            #print(str(i) + ": " + t + " [PF]")
            if "(" in t:
                left_bracket = t.index("(")
            else:
                left_bracket = False
            if ")" in t:
                right_bracket = t.rindex(")")
            else:
                right_bracket = False
            if left_bracket and right_bracket and right_bracket == len(t) - 1 and t[:left_bracket] in formulas:
                # ToDO: include digit + TIME elements (e.g. "2d" for "two days precision")
                args = [e.strip() for e in re.split(pattern,t[left_bracket+1:right_bracket]) if e]
                misfits = [a for a in args if a not in db_attrs.union(source_attrs)]
                if not misfits:
                    continue
                gui_messages.error(request, "Unknown elements in formula declaration: '" + ",".join(misfits) + "'")
            local_fault_collector[colname]["transformation"].append(i)


def check_int_array_and_sanitize(request, str_int):
    int_range_pattern = re.compile("(^(-?\d)?\d*:(-?\d)?\d*$)|(^(-?\d)?\d*$)")
    elements = str_int.split(",")
    misfits = [i for i in range(len(elements)) if not int_range_pattern.match(elements[i])]
    for m in misfits:
        x = elements[m].split(":")
        if len(x) > 2:
            return False
        try:
            elements[m] = ":".join(
                [str(f) for f in [lossless_float2int(request, x[i]) if x[i] else "" for i in range(len(x))]])
        except ValueError:
            return False
    return ",".join(elements)


def check_float_array_and_sanitize(str_float):
    float_range_pattern = re.compile("(^(-\d+)|(\d+)\.\d+$)|(^((-\d+)|(\d+)\.\d+)?:((-\d+)|(\d+)\.\d+)?$)")
    elements = str_float.split(",")
    misfits = [i for i in range(len(elements)) if not float_range_pattern.match(elements[i])]
    for m in misfits:
        x = elements[m].split(":")
        if len(x) > 2:
            return False
        try:
            elements[m] = ":".join([str(f) for f in [float(x[i]) if x[i] else "" for i in range(len(x))]])
        except ValueError:
            return False
    return ",".join(elements)


def check_date_array_and_sanitize(request, str_date):
    elements = [r.strip() for r in str_date.split(",")]
    # corrected = []
    for i in range(len(elements)):
        x = elements[i].split(":")
        if len(x) > 2:
            return False
        try:
            elements[i] = ":".join([str(f) for f in [
                check_date(request, 0, x[j], date_range=date_range_global, sanitize=True) if x[j] else "" for j in
                range(len(x))]])
        except ValueError:
            return False
    return ",".join(elements)


def check_domain(request, colname, sheet, codes, local_fault_collector):
    col = [cell.strip(" []") for cell in sheet.column[colname]]
    if not col == sheet.column[colname]:
        sheet.column[colname] = col
        gui_messages.warning(request,
                             "Removed useless leading/trailing whitespace characters from column '" + colname + "'")
    datatypes = sheet.column["Datatype"]
    local_fault_collector[colname]["domain"] = []
    db_codes = list(DatamodelCode.objects.values_list("Code", flat=True))
    all_codes = db_codes + codes

    for i in range(len(col)):
        if not col[i]:
            continue  # Domain is optional... if empty: skip

        # integer tests
        if datatypes[i] in ["int", "array(int)"]:
            corr = check_int_array_and_sanitize(request, col[i])
            if corr:
                if not col[i] == corr:
                    gui_messages.warning(request,
                                         "Found float values or whitespace chars in domain declaration of an integer-type variable.")
                    col[i] = corr
            else:
                local_fault_collector[colname]["domain"].append(i)
            continue

        # float tests
        if datatypes[i] in ["float", "array(float)"]:
            corr = check_float_array_and_sanitize(col[i])
            if corr:
                if not col[i] == corr:
                    gui_messages.warning(request,
                                         "Found integer values or whitespace chars in domain declaration of a float-type variable.")
                    col[i] = corr
            else:
                local_fault_collector[colname]["domain"].append(i)
            continue

        # code tests
        if datatypes[i] in ["code", "array(code)"]:
            misfits = [r.strip() for r in col[i].split(",") if r.strip() not in all_codes]
            if misfits:
                gui_messages.warning(request, "Unknown codes referenced: '" + "', '".join(misfits) + "'")
                local_fault_collector[colname]["domain"].append(i)
            continue

        # date tests
        if datatypes[i] in ["date", "array(date)"]:
            corr = check_date_array_and_sanitize(request, col[i])
            if corr:
                if not col[i] == corr:
                    gui_messages.warning(request,
                                         "Found sub-optimal formatting in domain declaration of a date-type variable.")
                    col[i] = corr
            else:
                local_fault_collector[colname]["domain"].append(i)
            continue

    # if datatypes[i] == "string" and not array_float_array_pattern.match(col[i]):
    if not col == sheet.column[colname]:
        sheet.column[colname] = col
        gui_messages.warning(request, "Sanitized entries in column '" + colname + "'")


## check foreign key columns: string referencing correct (existing) key?
def check_foreign_keys(request, colname, sheet, model, local_fault_collector, data_collector):
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
        adapters = []
        distmodel_name = distmodel._meta.model.__name__.lower()
        colpos = data_collector[distmodel_name].colnames.index(distfield)
        sheet_keys.extend([row[colpos] for row in data_collector[distmodel_name]])
        # sheet_keys.extend([row[distfield] for row in data_collector[distmodel_name]])

        col = sheet.column[colname]
        all_keys = set(db_keys + sheet_keys)
        if not set(col).issubset(all_keys):  # unknown foreign key referenced
            local_fault_collector[colname]["foreignkey"] = [i for i in range(len(col)) if col[i] not in all_keys]


# Setup containers for sheet/model
def fill_import_containers(importer, data_collector, model, sheet):
    # generate import adapter from model
    adapter = DjangoModelImportAdapter(model)
    # print(sheet.colnames)
    adapter.column_names = sheet.colnames
    # print(adapter.column_names)

    # add adapter to importer (= queue for current dependency level)
    importer.append(adapter)

    # feed data collector struct with sheet-derived data
    # data_collector[adapter.get_name()] = sheet.get_internal_array()
    data_collector[adapter.get_name()] = sheet


# finally write fitted data to database
def imprint_database(request, importer_collector, data_collector, dls_range=None):
    error_flag = False
    if not dls_range:
        dls_range = range(len(get_dependency_levels()))
    print("Imprinting database...")
    for dli in dls_range:
        # fire up the import for a dependency level
        print("...level " + str(dli + 1) + ":")
        importer = importer_collector[dli]  # get level-specific subset of adapters (= one importer)
        data_collector_subset = {}  # prepare struct for respective data chunk
        for model_adapter_name in importer._DjangoModelImporter__adapters.keys():
            sheet = data_collector[model_adapter_name]
            model = importer._DjangoModelImporter__adapters[model_adapter_name].model
            # Re-work data in sheet in order to fulfill foreignKey constraints (replace strings with objects)
            print("Setting up ForeignKeys for '" + model_adapter_name + "'...")
            new_sheet = setup_foreign_keys_in_sheet(request, sheet, model)
            if new_sheet:
                print("...done.")
                data_collector_subset[model_adapter_name] = new_sheet.get_internal_array()
            else:
                print("...failed!")
                error_flag = True

        if not error_flag:
            print("Saving data for dependency level " + str(dli + 1) + " models...")
            try:
                save_data(importer, data_collector_subset, file_type=DB_DJANGO)
            except IntegrityError as e:
                print("FAILED!")
                print(e)
            print("...success!")
        else:
            return False
    return True


@login_required
@require_http_methods(['GET','POST'])
def datamodeltable_view(request):
    if request.method == 'GET':
        return render(request, 'datamodelhandson.html')

@require_http_methods(['GET'])
def get_xlsx_as_json(request):
    id = request.GET.get('file_id')
    file = get_object_or_404(UserFile, pk=id)
    workbook = xlrd.open_workbook(file.file.path)
    data_json = {}
    #print(workbook.sheet_names())
    for sheet_name in workbook.sheet_names():

        sheet_json = {}
        sheet = workbook.sheet_by_name(sheet_name)
        header = sheet.row(0)
        for i in range(1, sheet.nrows):
            sheet_json[i-1]= {}
            for j in range(sheet.ncols):
                cell = sheet.cell_value(i,j)
                sheet_json[i-1][str(sheet.cell_value(0,j))] = cell
        data_json[str(sheet_name)] = sheet_json
    return JsonResponse(data_json)

@require_http_methods(['GET'])
def get_broken_lines_model(request):
    if cache.get('broken_lines_model'):
        return JsonResponse({'brokenlines': cache.get('broken_lines_model')})
    else:
        return JsonResponse({'Status': 'error'})

@require_http_methods(['GET'])
def get_ignored_lines_model(request):
    if cache.get('ignored_lines_model'):
        return JsonResponse({'ignoredlines': cache.get('ignored_lines_model')})
    else:
        return JsonResponse({'Status': 'error'})


# core function / entrypoint for importing datamodel
@require_http_methods(["GET", "POST"])
def import_datamodel(request):
    if request.method == "POST":

        form = DatamodelUploadFileForm(request.POST, request.FILES)

        if form.is_valid():

            ### INPUTS SECTION ###
            gui_messages.set_level(request, gui_messages.DEBUG)  # ToDo: user selection
            #chunk_size = 1000

            # setup base information on relations/mappings between Django models and Excel sheets
            model2sheetMappings, colname_map, header_line = get_mapping_information()  # ToDo: get from form

            # check file provided by upload form for required sheets
            #book = request.FILES['file'].get_book()
            file = request.FILES['file']

            f = UserFile.objects.create(file=file,name=file.name)

            ### END OF INPUTS SECTION ###

            book = file.get_book()
            sheet_names = book.sheet_names()
            #print([sn.__class__ for sn in model2sheetMappings.values()])
            misses = [sn for sn in model2sheetMappings.values() if not sn in sheet_names]
            if misses:
                msg = "Could not find following required worksheets in uploaded datamodel file:\n" + "\n".join(misses)
                gui_messages.error(request, msg)
                release_messages(request)
                return HttpResponse("Failed to read data model.")

            # clear database        # ToDo: remove?
            # sweep data table if necessary
            if form.data["write_mode"] == "new":
                gui_messages.warning(request,
                                     "This will delete all data model information contained in the current database.")
                drop_tables()

            # loops over models starts here (chunked in dependency levels)
            dli = 0
            importer_collector = {}
            data_collector = {}
            fault_collector = {}
            column_mappers = {}
            row_mappers = {}
            codes = []
            code_mappings = []
            error_flag = False
            broken_lines_model = {}
            ignored_lines_model = {}

            for models in get_dependency_levels():
                print("Checking level " + str(dli+1) + " models...")  # ToDo: replace messaging lines
                importer = DjangoModelImporter()  # generate new importer (adapter queue) for current dependency level
                for model in models:
                    sheet_name = model2sheetMappings[model]
                    broken_lines_model[sheet_name] = {}
                    ignored_lines_model[sheet_name] = []
                    print("    => " + sheet_name + " --> " + model.__name__)

                    # get original datamodel (sheet) from file
                    #sheet = request.FILES['file'].get_sheet(sheet_name=sheet_name,
                    sheet = file.get_sheet(sheet_name=sheet_name,
                                           name_columns_by_row=int(form.data["header_line"]),
                                           auto_detect_float=False,  # does not work
                                           auto_detect_datetime=False)

                    # Check header
                    indices = get_header_indeces(request, sheet.colnames, colname_map[sheet_name])
                    if not indices:
                        release_messages(request)
                        msgs = get_messages(request)
                        cache.set('broken_lines_model', broken_lines_model)
                        cache.set('ignored_lines_model', ignored_lines_model)
                        return render(request, "datamodelhandson.html", {'current_msg':
                            "Corrupt datamodel header line for '" + sheet_name + "' - please check log for details.", 'file_id': f.pk, 'msgs': msgs, 'blabla': "Her goes an interactive Handsontable..."})

                    # remove unused COLUMNS
                    delete_columns = [i for i in range(sheet.number_of_columns()) if not sheet.colnames[i] in indices] ##grau einfärben
                    column_mappers[sheet_name] = [i for i in range(sheet.number_of_columns()) if
                                                  i not in delete_columns]
                    sheet.delete_columns(delete_columns)

                    # index ROWS with Active = FALSE, if given
                    inactive_rows = []##GRAU
                    if "Active" in sheet.colnames:
                        active_col = sheet.column["Active"]
                        inactive_rows = [i for i in range(sheet.number_of_rows()) if
                                         active_col[i] in [0] + false_replacements]

                    # index blank ROWS
                    blank_rows = [i for i in range(sheet.number_of_rows()) if blank_row(i, sheet.row[i])] #GRAU



                    # remove blank and inactive ROWS from sheet
                    # ToDo: report inactive lines as infos, blank lines as warnings
                    delete_rows = inactive_rows + blank_rows  # no overlap of lists possible...
                    ignored_lines_model[sheet_name] = delete_rows
                    row_mappers[sheet_name] = [i for i in range(sheet.number_of_rows()) if i not in delete_rows]
                    sheet.delete_rows(delete_rows)

                    # check model compliance of remaining columns
                    fault_collector[sheet_name] = {}
                    print("\tWorking on columns:")
                    for colname in colname_map[sheet_name]:
                        print("\t * " + colname)
                        fault_collector[sheet_name][colname] = {}

                        check_regular_field_compliance(request, colname, sheet, model, fault_collector[sheet_name])

                        check_uniqueness_for_column(request, colname, sheet, model, fault_collector[sheet_name])

                        if colname == "Domain":
                            check_domain(request, colname, sheet, codes, fault_collector[sheet_name])

                        if colname in ["Transformation", "Function"]:
                            check_transformation(request, colname, sheet, fault_collector[sheet_name],
                                                 sheet.column["Target_Attribute"], )

                        if colname == "Function":
                            pass        # ToDo: functionality like in "check_transformation" (or move in...)

                        if not error_flag:
                            error_flag = get_error_flag(fault_collector, sheet_name, colname)

                        if not error_flag:
                            check_foreign_keys(request, colname, sheet, model, fault_collector[sheet_name],
                                               data_collector)

                        if not error_flag:
                            error_flag = get_error_flag(fault_collector, sheet_name, colname)

                        if fault_collector[sheet_name][colname]:
                            broken_lines_model[sheet_name][colname] = fault_collector[sheet_name][colname]
                    # END OF LOOP over columns of sheet

                    #print(error_flag)
                    if not error_flag:  # prepare DB import of data IF no errors occurred yet
                        if sheet_name == "Codes":
                            codes = sheet.column["Code"]
                        if sheet_name == "Code_Mappings":
                            code_mappings = sheet.column["Code_Mapping"]
                        print("\tFine... Preparing import container...\n")
                        fill_import_containers(importer, data_collector, model, sheet)

                    #no_of_entries = len(sheet._Matrix__array)
                # END OF LOOP over sheets (= models) of the current dependency level

                # save current dependency level's importer to respective collector
                importer_collector[dli] = importer
                if not error_flag:
                    success = imprint_database(request, importer_collector, data_collector, [dli])
                    if not success:
                        error_flag = True
                        gui_messages.error(request, "Failed to write datamodel contents to DB (dep. level " + str(dli) + ")")
                    else:
                        print("...done: Finished on level " + str(dli + 1) + " models.\n")
                    release_messages(request)
                dli += 1
            # END OF LOOP over model dependency levels

            if error_flag:
                print("THERE WERE ISSUES!") # report them...
                for sheet in fault_collector.keys():
                    print("\n=== Sheet '" + sheet + "' ===")
                    for column in fault_collector[sheet].keys():
                        for error in fault_collector[sheet][column].keys():
                            if len(fault_collector[sheet][column][error]):
                                print("\nColumn '" + column + "' - '" + error + "' errors in following rows:")
                                print(", ".join(
                                    [str(row_mappers[sheet][x] + 2) for x in fault_collector[sheet][column][error]]))
                #print(fault_collector)
                release_messages(request)
                msgs = get_messages(request)

                cache.set('broken_lines_model', broken_lines_model)
                cache.set('ignored_lines_model', ignored_lines_model)
                return render(request, "datamodelhandson.html", {'current_msg':
                            "Successfully read data model.", 'file_id': f.pk, 'msgs': msgs, 'blabla': "Her goes an interactive Handsontable..."})
                #return HttpResponse("Failed to read data model - please correct your file's contents.")
            msgs = get_messages(request)
            #print(fault_collector)
            #broken_lines_model['Sources']['Source'] = "RED"
            '''
            broken_lines_model['Sources']['Source']['dublicate'] = [2,3]
            broken_lines_model['Sources']['Abbreviation']['assigned'] = [0,1]

            '''
            cache.set('broken_lines_model', broken_lines_model)
            cache.set('ignored_lines_model', ignored_lines_model)
            return render(request, "datamodelhandson.html", {'current_msg':
                            "Successfully read data model.", 'file_id': f.pk, 'msgs': msgs, 'blabla': "Her goes an interactive Handsontable..."})
            #return render(request, 'data-model-response.html', {'msgmodel':"Successfully read data model."})
            # END of valid form conditional
        else:
            return HttpResponseBadRequest() # form invalid
    else:
        form = DatamodelUploadFileForm()

    return render(
        request,
        'upload_form.html',
        {
            'form': form,
            'title': 'Import Excel-formatted datamodel',
            'header': 'Datamodel upload',
            'info': 'Import Excel-formatted datamodel into database',
        })


### end of datamodel-related functionalities ###

### Data section: all functions for reading in the data and matching it to the datamodel definitions uploaded previously ###

def get_header_indeces(request, act_colnames, exp_colnames):
    indices = {n: catch(lambda: act_colnames.index(n)) for n in exp_colnames}
    #indices = {n: catch(lambda: act_colnames.index(exp_colnames[n])) for n in exp_colnames}
    misses = [re.findall('\'([^\']*)\'', miss.args[0])[0] for miss in indices.values() if
              miss.__class__ is ValueError]
    if misses:
        msg = "Could not find following column headers (format corrupt?):\n" + "\n".join(misses)
        gui_messages.error(request, msg)
        return False
    return indices


def get_target_from_datamodel(request, attr, targets, source, mapping_only=False):
    mappings = DatamodelAttributeMapping.objects.filter(Source_Attribute=attr, Source=source)
    # print( mapping )
    core = DatamodelAttribute.objects.filter(Attribute=attr)
    # print(core)

    #print("BLBLBLBLB" + str(core[0].Domain))

    if mappings:
        if core:
            gui_messages.warning(request, "Attribute name '" + attr
                                 + "' known in both data model's core set and mapping table (latter preferred)!")
        else:
            gui_messages.info(request, "Attribute name '" + attr + "' found in mapping table.")
        target_set = [m.Core_Attribute for m in mappings]
    elif core:
        if mapping_only:
            gui_messages.error(request,
                               "Attribute name '" + attr + "' unknown to data model mappings!")
            return False
        target_set = core
    else:
        gui_messages.error(request,
                           "Attribute name '" + attr + "' unknown to data model (neither core set nor mapping table)!")
        return False
    targets[attr] = target_set
    return target_set


# date
def sanitize_date(request, d):
    # remove time stamp
    old = d
    d = re.compile("[0-9][0-9]:[0-9][0-9]:[0-9][0-9]").sub("", d)
    if not d == old:
        gui_messages.warning(request, "Removed timestamp from date.")

    # remove leading/trailing spaces
    old = d
    d = d.strip()
    if not len(old) == len(d):
        gui_messages.warning(request, "Removed leading/trailing whitespaces.")

    # if dot "." as separator: apply dash "-"
    old = d
    d = d.replace(".", "-")
    if not d == old:
        gui_messages.info(request, "Replaced '.' with correct separators '-'.")

    # remove leading/trailing separators
    old = d
    d = d.strip("-")
    if not len(old) == len(d):
        gui_messages.info(request, "Removed dangling separators.")

    # for incomplete dates: add "00" blocks as placeholder
    dash_cnt = d.count("-")
    if dash_cnt == 1:
        # messages.warning("Incomplete date - added day field '00'")
        if re.compile("^[0-9][0-9][0-9][0-9]-[0-9][0-9]").match(d):  # trailing month in template (preferred)
            gui_messages.info(request, "Incomplete date - added day field '00'")
            return d + "-00"
        elif re.compile("^[0-9][0-9]-[0-9][0-9][0-9][0-9]").match(
                d):  # leading month in template (to be corrected later)
            gui_messages.info(request, "Incomplete date - added day field '00'")
            return "00-" + d
        else:
            gui_messages.error(request, "invalid partial date pattern: '" + d + "'")
            return False
    elif dash_cnt == 0:
        gui_messages.info(request, "Incomplete date - added day and month fields '00'")
        return d + "-00-00"
    elif dash_cnt != 2:
        gui_messages.error(request, "Inadequate number of separators (" + str(dash_cnt) + ") found!")
        return False
    else:
        return d


# date
def reverse_date(d):
    return "-".join(reversed(d.split("-")))


# date
def check_date_pattern(request, d, sanitize):
    pat_msg = "'YYYY-MM-DD' required, with '00' legal for 'DD' and 'MM'"
    pattern = re.compile("^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$")
    if pattern.match(d):
        return d
    elif not sanitize:
        return False

    rev_d = reverse_date(d)
    if pattern.match(rev_d):
        gui_messages.info(request, "Reversed date sequence - " + pat_msg)
        return rev_d

    if re.compile("^[0-9][0-9]-").match(d):
        gui_messages.info(request, "No valid date pattern! (presumably two-digit YEAR expression - " + pat_msg + ")")
        return False
    elif re.compile("^[0-9][0-9][0-9][0-9]-[0-9]-[0-9][0-9]$").match(d):
        msg = "No valid date pattern! (presumably single-digit MONTH expression - " + pat_msg + ")"
        if not sanitize:
            gui_messages.error(request, msg)
            return False
    elif re.compile("^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9]$").match(d):
        gui_messages.info(request, "")
        msg = "No valid date pattern! (presumably single-digit DAY expression - " + pat_msg + ")"
        if not sanitize:
            gui_messages.error(request, msg)
            return False
    elif re.compile("^[0-9][0-9][0-9][0-9]-[0-9]-[0-9]$").match(d):
        msg = "No valid date pattern! (presumably single-digit MONTH and DAY expression - " + pat_msg + ")"
        if not sanitize:
            gui_messages.error(request, msg)
            return False

    year, month, day = d.split("-")
    if len(month) == 1:
        month = "0" + month
    if len(day) == 1:
        day = "0" + day

    # recursion (effectively single iteration)
    d = check_date_pattern(request, year + "-" + month + "-" + day, sanitize=False)

    if d:
        gui_messages.warning(request, "Sanitized invalid date format.")
        return d
    gui_messages.error(request, "No valid date pattern! (attempts to sanitize failed)")
    return False


# date
def calculate_date_object(d):
    year, month, day = d.split("-")
    return date(int(year), int(month), int(day))


# date
def fit_00_date_vs_range(request, d, date_range):
    year, month, day = d.split("-")  # pattern YYYY-MM-DD ensured here

    err_str = "Date '" + d + "' out of accepted range! ('" + "' to '".join(date_range) + "')"
    if int(month) * int(day):  # both values are unequal zero - fully python-valid date format
        if not calculate_date_object(date_range[0]) <= calculate_date_object(d) <= calculate_date_object(date_range[1]):
            gui_messages.error(request, err_str)
            return False
        else:
            return d

    # day and/or month are zero'd - check year match first
    if not int(date_range[0][0:4]) <= int(year) <= int(date_range[1][0:4]):
        gui_messages.error(request, err_str)
        return False

    if not int(month):
        month_min = "12"
        month_max = "01"
    else:
        month_min = month_max = month

    if not int(day):
        date_min = year + "-" + month_min + "-" + str(calendar.monthrange(int(year), int(month_max))[1]).zfill(2)
        date_max = year + "-" + month_max + "-01"
    else:
        date_min = year + "-" + month_min + "-" + day
        date_max = year + "-" + month_max + "-" + day

    if calculate_date_object(date_range[0]) <= calculate_date_object(date_min):
        if calculate_date_object(date_max) <= calculate_date_object(date_range[1]):
            return d

    gui_messages.error(request, err_str)
    return False


# date: central access
def check_date(request, pid, d, sanitize=False, date_range=date_range_global):
    channel_layer= get_channel_layer()
    # expected pattern: YYYY-MM-DD

    # sanitize?
    if sanitize:
        d = sanitize_date(request, d)
        if not d: return False

    # test character set
    if not re.compile("^(\d+(?:-\d+)*)$").match(d):
        async_to_sync(channel_layer.group_send)('{}'.format("process_" + str(pid))  , {"type": "status_message", "message": "Illegal characters in date detected."})

        gui_messages.error(request, "Illegal characters in date detected.")
        return False

    # check pattern
    d = check_date_pattern(request, d, sanitize)
    if not d: return False

    # check plausible ranges
    year, month, day = d.split("-")
    if not 0 <= int(day) <= 31:
        async_to_sync(channel_layer.group_send)('{}'.format("process_" + str(pid))  , {"type": "status_message", "message": "Invalid day value (" + str(day) + ")!"})

        gui_messages.error(request, "Invalid day value (" + str(day) + ")!")
        d = False
    if not 0 <= int(month) <= 12:

        async_to_sync(channel_layer.group_send)('{}'.format("process_" + str(pid))  , {"type": "status_message", "message": "Invalid month value (" + str(month) + ")!"})

        gui_messages.error(request, "Invalid month value (" + str(month) + ")!")
        d = False

    if d: d = fit_00_date_vs_range(request, d, date_range)

    return d


# date
def check_date_domain_fit(request, var_date, domain):
    # domain = two-item array of dates
    if domain[0] and var_date < domain[0]:
        gui_messages.error(request, "'" + str(var_date) + "' exceeds date range: < " + str(domain[0]))
        return False
    if domain[1] and var_date > domain[1]:
        gui_messages.error(request, "'" + str(var_date) + "' exceeds date range: > " + str(domain[1]))
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
    #print(instring)
    fr, to = array_from_string(instring)
    if not fr and generic_from: fr = generic_from
    if not to and generic_to: to = generic_to
    return fr, to


# num + unit
def separate_value_and_unit(request, var):
    var = re.sub(r"\s", "", var)
    value = "".join(re.findall(r"[\d.]", var))
    try:
        startpos = var.index(value)
        if startpos == 0:
            unit = var[(len(value)):]
            return value, unit
    except ValueError as e:
        gui_messages.error(request, "No valid number, even considering trailing unit declarations: " + var)
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
def verify_units2UCUM(request, actual_unit, reference_unit, buffer_dict={}):
    call = [x for x in [actual_unit, reference_unit] if x not in buffer_dict]
    if not call:
        return {}
    # print(request)
    reply = ucumVerify(call, ucum_api_url)
    reply_dict = UCUM_server_reply2dict(reply)
    if not reference_unit in buffer_dict and not reference_unit in reply_dict:
        gui_messages.error(request, "Could not resolve reference unit in UCUM!")
        return False
    elif actual_unit in buffer_dict and not actual_unit in reply_dict:
        gui_messages.error(request, "Could not resolve unit in UCUM!")
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
                collector.update(generate_conversion_api_urls(actual_unit[i], reference_unit[i]))
    else:
        url = ucum_api_url + "/ucumtransform"
        request = url + "/" + str(value) + "/from/" + actual_unit + "/to/" + reference_unit
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
def convert_using_UCUM(request, value, actU, refU, verified={}, conversions={}):
    reply = verify_units2UCUM(request, actU, refU, verified)
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
                factor = float(responses[conv]['ResultQuantity']) / float(responses[conv]['SourceQuantity'])
                conversions[conv] = factor
            return value
        else:
            gui_messages.error(request, "Auto-conversion from '" + actU + "' to '" + refU
                               + "' unavailable (could not verify using UCUM server).")
    except KeyError as e:
        gui_messages.error(request, "An error occured while trying to convert a UCUM unit...")

    return False


# num + unit
def consider_unit_and_convert(request, var, refU_obj, verified={}, conversions={}):
    value, unit = separate_value_and_unit(request, var)

    if not value:  # errornous outputs
        return False

    if not unit:  # no unit detected, keep value as is
        return value

    refU = refU_obj.Unit

    # check if reference or not (yes = no action required)
    if unit == refU:
        return value

    if refU_obj.UCUM:  # verify UCUM membership (automated conversion is yet possible for those only!)
        return convert_using_UCUM(request, value, unit, refU, verified, conversions)
    else:
        gui_messages.error(request, "Auto-conversion from '" + unit + "' to '" + refU
                           + "' unavailable (no UCUM units).)")
        return False

# integer
def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# integer
def lossless_float2int(request, numstring):
    if numstring.count(".") == 1:
        integer, decimal = numstring.split(".")
        if represents_int(integer):
            if not decimal or (represents_int(decimal) and int(decimal) == 0):
                gui_messages.warning(request, "Converted '" + numstring + "' to integer '" + integer + "' (lossless)")
                return integer
    gui_messages.error(request, "Could not convert float value to integer number: " + numstring)
    return False


# integer
def advanced_string2int(request, string, refU_obj=None, verified_UCUM_units={}, value_conversions={}):
    if "," in string:
        string = string.replace(",", ".")
        gui_messages.warning(request, "Converted '" + string + "' to international decimal '.'!")

    if "." in string:
        string = lossless_float2int(request, string)
        if not string:
            gui_messages.error(request, "Could not convert value to integer number: " + string)
            return False

    if refU_obj and not refU_obj.Unit == "None":
        string = consider_unit_and_convert(request, string, refU_obj, verified_UCUM_units, value_conversions)
        if not string:
            gui_messages.error(request, "Could not convert value to integer number: " + string)
            return False

    try:
        return int(string)
    except ValueError:
        return False


# num (both integer and float)
def check_num_domain_fit(request, var_num, domain, type):
    for subdomain in array_from_string(domain):
        leftfit = rightfit = True
        left, right = array_from_string(subdomain, delim=":", convert=type)
        if left and var_num < left:
            leftfit = False
        if right and var_num > right:
            rightfit = False
        if leftfit and rightfit:
            return var_num
    gui_messages.error(request, "'" + str(var_num) + "' exceeds value range of defined domain: " + str(domain))
    return False


# float
def advanced_string2float(request, string, refU_obj, verified_UCUM_units={}, value_conversions={}):
    string = consider_unit_and_convert(request, string, refU_obj, verified_UCUM_units, value_conversions)
    try:
        value = string.replace(",", ".")
        if value != string:
            gui_messages.warning(request, "Converted floating point symbol (German notation ',' found!).")
        return float(value)
    except ValueError as e:
        gui_messages.error(request, "Could not convert value to integer number: '" + string + "'\n" + e)
        return False


# code
def check_codekey_matches(request, vars, target_code, sanitize=False):
    target_keys = set(DatamodelCode.objects.filter(Code=target_code).values_list("Key", flat=True))
    if not target_keys:
        gui_messages.error(request, "Could not find code system '" + target_code + "'")
        return False
    try:
        diff = set(vars).difference(target_keys)
    except KeyError:
        diff = True
    if diff:
        if sanitize:
            fail = []
            success = []
            sanitized = []
            for item in list(vars):
                try_hard = str(advanced_string2int(request, item))
                if try_hard in target_keys:
                    success.append(try_hard)
                    if item != try_hard:
                        sanitized.append(item)
                else:
                    fail.append(item)
            if fail:
                gui_messages.error(request, "Found key(s) '" + ", ".join(fail) +
                                   "' being incompatible to code system '" + target_code + "' (not in [" +
                                   ", ".join(target_keys) + "])")
                return False
            gui_messages.warning(request, "Key(s) '" + ", ".join(sanitized) +
                                 "' had to be sanitized in order to be compatible to code system '" + target_code + "'")
            return vars.__class__(success)
        gui_messages.error(request, "Found key(s) '" + ", ".join(vars) + "' being incompatible to code system '" +
                           target_code + "' (not in [" + ", ".join(target_keys) + "])")
        return False
    return vars

# TODO: implement contents... and call in data main()
def apply_transformation(var_int, transformation):
    return var_int

# general entry point for deep tests on all available data types (except 'code')
# TODO: enable transformations (^)
# TODO: in data main(), transform input values into target space by source (no mapping/source information necessary to hand in here)
def ensure_datatype_and_domain_fit(request, pid, vars, target, transformation=False, date_range=date_range_global,
                                   sanitize=False, verified_UCUM_units={}, value_conversions={}):
    sanitized = False
    #print(target)
    for i in range(len(vars)):
        var = vars[i]
        c = list()

        if target.Datatype in ["int", "array(int)"]:
            for v in array_from_string(var):
                try:
                    var_int = int(v)
                except ValueError:
                    if sanitize:
                        var_int = advanced_string2int(request, v, target.Unit, verified_UCUM_units, value_conversions)
                        sanitized = True
                    else:
                        gui_messages.error(request, "Could not convert value to integer number: " + v)
                        var_int = False
                if var_int and transformation:
                    apply_transformation(var_int, transformation)
                if var_int and target.Domain:
                    var_int = check_num_domain_fit(request, var_int, target.Domain, "int")
                if var_int:
                    c.append(str(var_int))
                else:
                    c.append(var_int)

        elif target.Datatype in ["float", "array(float)"]:
            for v in array_from_string(var):
                try:
                    var_float = float(v)
                    if not str(var_float) == v:
                        sanitized = True
                        msg = "Found integer number ('" + v + "') where float expected"
                        if not sanitize:
                            var_float = False
                            gui_messages.error(request, msg)
                        else:
                            gui_messages.warning(request, msg)
                except ValueError:
                    if sanitize:
                        var_float = advanced_string2float(request, var, target.Unit, verified_UCUM_units, value_conversions)
                        sanitized = True
                    else:
                        gui_messages.error(request, "Could not convert value to float number: " + var)
                        var_float = False
                if var_float and transformation:
                    apply_transformation(var_float, transformation)
                if var_float and target.Domain:
                    var_float = check_num_domain_fit(request, var_float, target.Domain, "float")
                if var_float:
                    c.append(str(var_float))
                else:
                    c.append(var_float)

        elif target.Datatype in ["date", "array(date)"]:
            for v in array_from_string(var):
                v_ = check_date(request, pid, v, date_range=date_range, sanitize=sanitize)
                if v_:
                    if v != v:
                        gui_messages.warning(request, "Had to sanitize date statement: " + v + " => " + v_)
                        v = v_
                    if target.Domain:
                        ddomain = [datetime.strptime(x, '%Y-%m-%d') if x else False for x in domain_from_string(target.Domain)]
                        if not check_date_domain_fit(request, datetime.strptime(v, '%Y-%m-%d'), ddomain):
                            v = False
                else:
                    v = False
                if v:
                    c.append(str(v))
                else:
                    c.append(v)

        elif target.Datatype in ["code", "array(code)"]:
            #key_map = {m.Source_Value: m.Target_Equivalent for m in
            #           DatamodelCodeMapping.objects.filter(Code_Mapping=target.Transformation)}
            for v in array_from_string(var):
                #if key_map:
                #    v_ = check_codekey_matches(request, key_map[v], target.Domain, sanitize=sanitize)
                #else:
                v_ = check_codekey_matches(request, v, target.Domain, sanitize=sanitize)
                if v_:
                    if v != v:
                        gui_messages.warning(request, "Had to sanitize code key: " + v + " => " + v_)
                        v = v_
                else:
                    v = False
                if v:
                    c.append(str(v))
                else:
                    c.append(v)

        else:
            gui_messages.error(request, "Test for data model variable type '" + target.Datatype + "' is not implemented.")
            c.append(False)

        if False not in c:
            vars[i] = ",".join(c)
        else:
            vars[i] = False

    if False in vars:
        return False, sanitized
    return vars, sanitized


def release_messages(request):
    print("\nFollowing messages have been collected:")
    storage = get_messages(request)
    for message in storage:
        print(message.message)


def start_new_thread(function):
    def decorators(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.deamon = True
        t.start()
    return decorators


# is not working for some reason ...
def send_user_message(layer, msg, pid, typeMsg): # check consumers.py for all possible typeMsg
    async_to_sync(layer.group_send)('{}'.format("process_" + pid)  , {"type": typeMsg, "message": msg})


@require_http_methods(['GET'])
def get_broken_lines(request):
    #print(cache.get('brokenlines'))
    if cache.get('brokenlines'):
        return JsonResponse({'brokenlines':cache.get('brokenlines')})
    else:
        return JsonResponse({'brokenlines':''})

# tests the connection to websocket
def wait_for_websocket(wait):
    start = time.time()

    print("Waiting for WebSocket....")
    while(True):
        now = time.time()

        connection = cache.get("websocket_connection")
        #print(connection)
        if connection == "connected":
            print("Connected to WebSocket after " + str(now - start) +" seconds!")
            return True
        if (now - start) > wait:
            break

    return False

@require_http_methods(['POST'])
def import_data_main_after_handson(request):
    #print( request.session.get('form-data'))
    meta = request.session.get('form-data')
    meta['delim'] = ","
    sheet = get_sheet(file_name=get_object_or_404(UserFile, pk=request.POST['file_id']).file.path,name_columns_by_row=0,encoding='utf8')
    sheet.colnames = ["PID", "DATE", "ATTRIBUTE","VALUE","PROVENANCE"]
    print("Restarting upload...")
    import_data(meta,request,sheet)
    #print(request.POST['file_id'])
    # TODO start upload THREAD
    return render(request, "response_board.html",{'pid': meta['pid'],'file_id': request.POST['file_id']})


@require_http_methods(['POST'])
def upload_file_to_server(request):
    if request.FILES['file']:
        file = request.FILES['file']
        name = file.name
        f = UserFile.objects.create(file=file,name=name)
        return JsonResponse({'file_id':f.pk})
    else :
        print('file not set')
        return HttpResponse(status=500)

@require_http_methods(["GET", "POST"])
def import_data_main(request):
    if request.method == "POST":
        form = DataUploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['file']
            '''
            file_name = settings.DATA_LOCATION + "/" + file.name
            #print(file_name)
            with open(file_name, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            '''
            fi = UserFile.objects.create(file=f, name=f.name)
            meta = {}
            meta['pid'] = form.data['pid']
            #meta['channel_layer'] = get_channel_layer()
            #meta['file_name'] = file_name
            meta['error_mode'] = form.data['error_mode']
            meta['write_mode'] = form.data['write_mode']
            meta['delim'] = form.data["delim"]
            meta['min_date'], meta['max_date'] = form.data["min_date"], form.data["max_date"]
            meta['pid'] = form.data['pid']
            meta['source'] = form.data["source"]
            request.session['form-data'] = meta
            sheet = request.FILES['file'].get_sheet(name_columns_by_row=0)
            #print("hallo2")
            import_data(meta, request, sheet)

        else:
            gui_messages.error(request, "The Form Input is not valid, please check the input.")
            return HttpResponseRedirect("/upload/data/")


        return render(request, "response_board.html",{'pid': form.data['pid'],'file_id': fi.pk})
    else:
        form = DataUploadFileForm()

    return render(
        request,
        'upload_form.html',
        {
            'form': form,
            'title': 'Import EAV++-formatted data',
            'header': 'Data upload',
            'info': 'Import EAV++-formatted data into database according to data model definitions and mappings.',
        })


# core function / entrypoint for importing data according to data model
@start_new_thread
def import_data(meta, request, sheet):
    brokenlines ={}
    cache.delete('brokenlines')
    # waits 10 seconds max for websocket
    connection_test = wait_for_websocket(10)
    if not connection_test :
        print("Waiting too long for Websocket...")
        return JsonResponse({'status': 'connection refused waited to long'})
    form = DataUploadFileForm(request.POST)

    #send_user_message(channel_layer, "statet progressing", meta['pid'])
    try:

        # print( form.__dict__ )
        if True:            # TODO: remove (= unindent one level)
            channel_layer = get_channel_layer()
            send_user_message(channel_layer, "test", meta['pid'], "status_message")
            #async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": 'Hallo'})

            # INPUTS
            sanitize = (meta["error_mode"] == "sanitize" or meta["error_mode"] == "propose")
            #gui_messages.set_level(request, gui_messages.DEBUG)
            eav_colnames = ["PID", "DATE", "ATTRIBUTE", "VALUE", "PROVENANCE"]
            chunk_size = 1000

            colname_mapping =   {"PID": "PID",
                                 "DATE": "TS",
                                 "ATTRIBUTE": "ITEM",
                                 "VALUE": "VALUE",
                                 "PROVENANCE": "PROVENANCE"}  # ToDo: enable mappings by form...
            colname_vec = ["PID", "DATE", "ATTRIBUTE", "VALUE", "PROVENANCE"]

            # ToDo: user declares 2D ('normal') or 1D (EAV++) table; if 2D, reformat first

            # END OF INPUTS

            # sweep data table if necessary
            if meta["write_mode"] == "sweep":
                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "This will delete all data contained in the current database."})
                drop_data_table()

            # open file provided by upload form
            '''
            sheet = None
            with open(meta['file_name'], 'r') as file:
                sheet = get_sheet(file, name_columns_by_row=0)
            '''
            # Check header
            #print(sheet.colnames)
            r = csv.reader(sheet.colnames, delimiter=meta["delim"], quotechar='"', quoting=csv.QUOTE_ALL)      # ToDo: offset header?
            header = next(r)
            #print("This is the header " + str(header))
            if colname_mapping:
                indices = get_header_indeces(request, header, [colname_mapping[x] for x in colname_vec])
                if indices:
                    for c in colname_vec:
                        indices[c] = indices.pop(colname_mapping[c])
            else:
                indices = get_header_indeces(request, header, colname_vec)

            if not indices:
                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "error_message", "message": "Corrupt EAV++ header line - please check log for details."})
                brokenlines[0] = "Corrupt EAV++ header line - please check log for details.;;ERROR;;red;;ALL"
                release_messages(request)
                cache.set('brokenlines',brokenlines)
                return HttpResponse("Corrupt EAV++ header line - please check log for details.")

            # Proceed on contents: iterate rows of EAV
            targets = {}                # collector; saves DB requests
            verified_UCUM_units = {}    # index; saves server requests
            value_conversions = {}      # collector; saves server requests
            eav_array = [eav_colnames]  # collector; saves EAV lines for chunked database uploads
            bulk_mgr = BulkCreateManager(chunk_size=chunk_size)
            line_counter = 0
            line_cnt_success = 0
            k = 0
            length = 0
            twentysent = False
            fourtysent = False
            sixtysent = False
            eightysent = False
            #brokenlines[1] = "hallo;;SANITIZED;;yellow;;VALUE"
            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "update_message", "proc": "0"})
            for row in sheet:
                length = length +1
            for raw_row in sheet:
                ## Check for abord

                if cache.get('cancel') == 'true':
                    cache.delete('cancel')
                    print('Killed the upload Thread due to user interaction.\n')
                    async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "error_message", "message": "Canceled Upload after " + str(line_counter) + "lines"})
                    cache.set('brokenlines',brokenlines)
                    return JsonResponse({'status': 'cancelled'})

                ## UPDATE PROCESS
                k=k+1
                proc = k/length
                if proc > 0.2 and not twentysent :
                    twentysent = True
                    async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "update_message", "proc": str(proc * 100)})
                if proc > 0.4 and not fourtysent :
                    fourtysent = True
                    async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "update_message", "proc": str(proc * 100)})
                if proc > 0.6 and not sixtysent :
                    sixtysent = True
                    async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "update_message", "proc": str(proc * 100)})
                if proc > 0.8 and not eightysent :
                    eightysent = True
                    async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "update_message", "proc": str(proc * 100)})



                if meta["error_mode"] == "strict" and line_counter != line_cnt_success:
                    #TODO
                    break

                line_counter += 1

                # print(raw_row)
                r = csv.reader(raw_row, delimiter=meta["delim"], quotechar='"', quoting=csv.QUOTE_ALL)
                row = next(r)
                # print(row)

                row_pid = row[indices["PID"]]
                row_date = row[indices["DATE"]]
                row_attr = row[indices["ATTRIBUTE"]]
                row_value = row[indices["VALUE"]]
                #print(row_value)

                # check DATE
                date_range = [meta["min_date"], meta["max_date"]]
                sanitize_trigger = (meta["error_mode"] == "sanitize" or meta["error_mode"] == "propose")
                if row_date == "*":
                    static = True
                    entity_date = row_date
                else:
                    static = False
                    entity_date = check_date(request,
                                             meta['pid'],
                                             row_date,
                                             date_range=date_range,
                                             sanitize=sanitize_trigger
                                             )
                    if not entity_date:  # no valid DATE - row data is useless
                        release_messages()
                        continue
                    elif entity_date != row_date:
                        msg = "Line " + str(line_counter) + ": " + row_date + " => " + entity_date + " (DATE)"
                        if meta["error_mode"] == "propose":
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']), {"type": "status_message", "message": "Sanitizing of 'DATE' successful, while proposal requested."})
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']), {"type": "status_message", "message": msg + " PROPOSAL"})
                            brokenlines[line_counter] = msg + ";;PROPOSAL;;red;;DATE"
                            continue
                        else:
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": msg + " SANITIZED"})
                            brokenlines[line_counter] = msg + ";;SANITIZED;;yellow;;DATE"

                # check uniqueness of EAV entry for SOURCE
                ## dynamics: message and action depends on mode and coarseness
                ## statics: duplicates are illegal per se (or replace the given info IF configured so)
                entries = list()
                if not meta["write_mode"] == "sweep":
                    entries = DataPoints.objects.filter(SOURCE=meta["source"],
                                                        PID=row_pid,
                                                        DATE=entity_date,
                                                        ATTRIBUTE=row_attr,
                                                        )
                    if entries:
                        eav = row_pid + ";" + entity_date + ";" + row_attr + ";" + row_value
                        if meta["write_mode"] == "unique":
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message":"Duplicate entry while 'unique' requested - skipping line #" + str(
                                                     line_counter) + "..."})
                            brokenlines[line_counter] = "Duplicate entry while 'unique' requested - skipping line;;SKIPPED;;grey;;SOURCE"
                            continue
                        elif meta["write_mode"] == "update":
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "Existing entry " + " will be replaced with input line #" + str(
                                line_counter) + "('" + eav + "')..."})
                            brokenlines[line_counter] = "Existing entry " + " will be replaced with input line"  + str(line_counter)+ "('" + eav + "')...;;SANITIZED;;yellow;;SOURCE"
                        elif meta["write_mode"] == "add" and static:
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "Existing time-less entry " + " - addition not possible! Skipping line #" + str(
                                                   line_counter) + "..."})
                            brokenlines[line_counter] ="Existing time-less entry " + " - addition not possible! Skipping line;;SKIPPED;;grey;;SOURCE"
                            continue

                # check ATTRIBUTE in variable list existance (in mapping table and core set)
                #todo: if target variable is not ACTIVE: WARNING and skip
                #print( str(line_counter + 1) + ": " + row_attr )

                if not row_attr in targets:
                    target_list = get_target_from_datamodel(request, row_attr, targets, meta["source"], "mapping_only" in form.data)
                    if not target_list:
                        continue

                # ATTRIBUTE from SOURCE might point to multiple TARGETs
                for target in targets[row_attr]:
                    # check DATE
                    if target.Topic == "master":
                        entity_date = date_range_global[0]
                    else:
                        entity_date = check_date(request, meta['pid'], row_date, date_range=date_range, sanitize=sanitize_trigger)
                        if not entity_date:  # no valid DATE - row data is useless => skip line
                            release_messages()
                            continue
                        elif entity_date != row_date:
                            msg = "Line " + str(line_counter) + ": " + row_date + " => " + entity_date + " (DATE)"
                            if form.data["error_mode"] == "propose":
                                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message":"Sanitizing of 'DATE' successful, while proposal requested (line #" + str(line_counter) + ")."})
                                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": msg + " PROPOSAL"})
                                brokenlines[line_counter] =  msg + ";;PROPOSAL;;grey;;DATE"
                                continue
                            else:
                                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": msg + " SANITIZED"})
                                brokenlines[line_counter] =  msg + ";;SANITIZED;;yellow;;DATE"


                    # get EAV value and check
                    if not row_value:
                        async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "Value for attribute '" + row_attr + "' is empty. Skipping line #" + str(
                                               line_counter) + "..."})
                        brokenlines[line_counter] =  "Value for attribute '" + row_attr + "' is empty. Skipping line #" + str(
                                               line_counter) + "..." + ";;SKIPPED;;grey;;DATE"

                        release_messages(request)
                        break  # no valid entry given, skip complete EAV line

                    # check uniqueness of EAV entry for SOURCE
                    ## general data: message and action depends on mode and coarseness
                    ## master data: duplicates are illegal per se (or replace the existing entry IF configured so)
                    entries = list()
                    if not form.data["write_mode"] == "sweep":
                        entries = DataPoints.objects.filter(SOURCE=form.data["source"],
                                                            PID=row_pid,
                                                            DATE=entity_date,
                                                            ATTRIBUTE=row_attr,
                                                            )
                        if entries:
                            eav = row_pid + ";" + entity_date + ";" + row_attr + ";" + row_value
                            if form.data["write_mode"] == "unique" and row_value not in entries.values_list("VALUE", flat=True):
                                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "Duplicate entry while 'unique' requested - skipping line #" + str(
                                                         line_counter + 1) + "..."})
                                brokenlines[line_counter] = "Duplicate entry while 'unique' requested - skipping line #" + str(
                                                         line_counter + 1) + "...;;SKIPPED;;grey;;SOURCE"
                                continue
                            elif form.data["write_mode"] == "update" and row_value not in entries.values_list("VALUE", flat=True):
                                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "Existing entry " + " will be replaced with input line #" + str(
                                                      line_counter + 1) + "('" + eav + "')..."})
                                brokenlines[line_counter] = "Existing entry " + " will be replaced with input line #" + str(
                                                      line_counter + 1) + "('" + eav + "')...;;SANITIZED;;yellow;;SOURCE"
                            elif form.data["write_mode"] == "add" and target.Topic == "master":
                                async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "status_message", "message": "Existing time-less entry " + " - addition not possible! Skipping line #" + str(
                                                       line_counter + 1) + "..."})
                                brokenlines[line_counter] = "Existing time-less entry " + " - addition not possible! Skipping line #" + str(
                                                       line_counter + 1) + "...;;SKIPPED;;grey;;SOURCE"
                                release_messages(request)
                                continue

                    # TODO: [DEF] transform value according to datamodel definitions
                    conversion_map = {m.Source_Value: m.Target_Equivalent
                               for m in DatamodelAttributeMapping.objects.filter(Target_Attribute=target).filter(Source=form.data["source"])}
                            #{m.Source_Value: m.Target_Equivalent for m in DatamodelCodeMapping.objects.filter(Code_Mapping=target.Transformation)}

                    # align value to target's datamodel definitions
                    ## type compatibility (get type of model attribute and apply tests by type)
                    var, sanitized = ensure_datatype_and_domain_fit(request, meta['pid'], row_value, target, "",
                                                                    date_range, sanitize, verified_UCUM_units, value_conversions)
                    if not var:  # no valid VALUE - row data is useless
                        async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                                                                {"type": "status_message",
                                                                 "message": "VALUE for line #" + str(line_counter + 1)
                                                                            + " appears invalid according to definitions for attribute '"
                                                                            + str(target.Attribute) + "'."})

                        release_messages(request)
                        continue
                    elif var != row_value and sanitized:
                        msg = "Line " + str(line_counter + 1) + ": " + row_value + " => " + var
                        if form.data["error_mode"] == "propose":
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                                                                    {"type": "status_message",
                                                                     "message": "Sanitizing of 'VALUE' successful, while proposal requested."})
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                                                                    {"type": "status_message",
                                                                     "message": msg + " PROPOSAL"})
                            brokenlines[line_counter] = msg + ";;SANITIZED;;yellow;;VALUE"
                            continue
                        else:
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                                                                    {"type": "status_message",
                                                                     "message": msg + " SANITIZED"})
                            brokenlines[line_counter] = msg + ";;SANITIZED;;yellow;;VALUE"

                    #var = str(var)

                    line_cnt_success += 1

                    if form.data["error_mode"] == "strict" and line_counter + 1 != line_cnt_success:
                        release_messages(request)
                        # todo: rollback
                        async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "error_message", "message": "Failed to read data - found errornous entries after input line #" + str(
                            line_counter) + " (" + str(raw_row) + ")."})
                        brokenlines[line_counter] = "Failed to read data - found errornous entries after input line #" + str(line_counter) + " (" + str(raw_row) + ").;;ERROR;;red;;ALL"
                        cache.set('brokenlines',brokenlines)
                        print(cache.get('brokenlines'))
                        return JsonResponse({'message' :"Failed to read data - found errornous entries after input line #" + str(
                            line_counter) + " (" + str(raw_row) + ")."})


                    if form.data["write_mode"] == "update" and len(entries) > 0:    # existing EAV entry: update immediately if possible
                        if len(entries) > 1:
                            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                                                                    {"type": "status_message",
                                                                     "message": "Multiple entries found while update (with one datapoint) requested - not possible, skipping..."})
                            brokenlines[line_counter] = "Multiple entries found while update (with one datapoint) requested - not possible, skipping...;;SKIPPED;;grey;;ALL"
                            continue
                            release_messages(request)
                        if not entries[0].VALUE == var or not entries[0].PROVENANCE == row[indices["PROVENANCE"]]:
                            # print("update")
                            entries[0].VALUE = var
                            entries[0].PROVENANCE = row[indices["PROVENANCE"]]
                            entries[0].save()
                    else:  # new EAV entry: store to buffer array
                        # print("new")
                        source_obj = DatamodelSource.objects.filter(Abbreviation=form.data["source"])[0]
                        eav_array.append([row_pid, entity_date, target.Attribute, var,
                                          row[indices["PROVENANCE"]], source_obj])
                        bulk_mgr.add(DataPoints(PID=row_pid,
                                                DATE=entity_date,
                                                ATTRIBUTE=target,
                                                VALUE=var,
                                                PROVENANCE=row[indices["PROVENANCE"]],
                                                SOURCE=source_obj,
                                                ))
                # END OF LOOP over 'targets[row_attr]'

            bulk_mgr.done()
            print(bulk_mgr.getcommitted(DataPoints))
            release_messages(request)
            async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid']),
                                                    {"type": "status_message",
                                                     "message": "Here I am. Successfully read "
                                                        + str(line_cnt_success)
                                                        + " entries into database (skipped "
                                                        + str(line_counter - line_cnt_success)
                                                        + " lines)."})
            cache.set('brokenlines',brokenlines)
            return JsonResponse({'message' :"Here I am. Successfully read "
                                            + str(line_cnt_success)
                                            + " entries into database (skipped "
                                            + str( line_counter - line_cnt_success )
                                            + " lines)."})
        else:

            # todo: this code is unreachable (counterpart to "if True")
            cache.set('brokenlines',brokenlines)

            return HttpResponseBadRequest()
    except Exception:
        cache.set('brokenlines',brokenlines)
        traceback.print_exc()
        async_to_sync(channel_layer.group_send)('{}'.format("process_" + meta['pid'])  , {"type": "error_message", "message": "An Error occured, that could not be handled..."})
    else:
        form = DataUploadFileForm()

    return render(
        request,
        'upload_form.html',
        {
            'form': form,
            'title': 'Import EAV++-formatted data',
            'header': 'Data upload',
            'info': 'Import EAV++-formatted data into database according to datamodel definitions and mappings.',
        })


### End of read in data section ###

### Deprecated templates starting from here ###


def download_eav(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="eav.csv"'

    writer = csv.writer(response, delimiter=";", quotechar='"')
    for obj in DataPoints.objects.all():
        writer.writerow([obj.SOURCE.Abbreviation + ":" + obj.PID, obj.DATE, obj.ATTRIBUTE, obj.VALUE, obj.PROVENANCE])

    return response


@require_http_methods(['GET'])
def get_csv_as_json(request):
    csv_id = request.GET.get('file_id')
    file = get_object_or_404(UserFile, pk=csv_id)
    data = {}
    k=0
    with open(file.file.path, 'r') as csv_file:
        csvReader = csv.DictReader(csv_file)
        for rows in csvReader:
            data[k] = rows
            k+=1
    return JsonResponse(data)

def datatable_view(request):
    csv_id = request.GET.get('file_id')
    csv = get_object_or_404(UserFile, pk=csv_id)

    return render(request, 'handsontable.html', {'file_id': csv_id,'file_name':csv.name})




def embed_handson_table(request):
    """
    Renders two table in a handsontable
    """
    content = excel.pe.save_book_as(
        models=[Question, Choice],
        dest_file_type='handsontable.html',
        dest_embed=True)
    content.seek(0)
    return render(
        request,
        'custom-handson-table.html',
        {
            'handsontable_content': content.read()
        })


def embed_handson_table_from_a_single_table(request):
    """
    Renders one table in a handsontable
    """
    content = excel.pe.save_as(
        model=Question,
        dest_file_type='handsontable.html',
        dest_embed=True)
    content.seek(0)
    return render(
        request,
        'custom-handson-table.html',
        {
            'handsontable_content': content.read()
        })


def import_sheet_using_isave_to_database(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST,
                              request.FILES)
        if form.is_valid():
            request.FILES['file'].isave_to_database(
                model=Question,
                mapdict=['question_text', 'pub_date', 'slug'])
            return HttpResponse("OK")
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(
        request,
        'upload_form.html',
        {'form': form})


def import_data_using_isave_book_as(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST,
                              request.FILES)

        def choice_func(row):
            q = Question.objects.filter(slug=row[0])[0]
            row[0] = q
            return row

        if form.is_valid():
            request.FILES['file'].isave_book_to_database(
                models=[Question, Choice],
                initializers=[None, choice_func],
                mapdicts=[
                    ['question_text', 'pub_date', 'slug'],
                    ['question', 'choice_text', 'votes']]
            )
            return redirect('handson_view')
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(
        request,
        'upload_form.html',
        {
            'form': form,
            'title': 'Import excel data into database example',
            'header': 'Please upload sample-data.xls:'
        })


def import_without_bulk_save(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST,
                              request.FILES)

        def choice_func(row):
            q = Question.objects.filter(slug=row[0])[0]
            row[0] = q
            return row

        if form.is_valid():
            request.FILES['file'].save_book_to_database(
                models=[Question, Choice],
                initializers=[None, choice_func],
                mapdicts=[
                    ['question_text', 'pub_date', 'slug'],
                    ['question', 'choice_text', 'votes']],
                bulk_save=False
            )
            return redirect('handson_view')
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(
        request,
        'upload_form.html',
        {
            'form': form,
            'title': 'Import excel data into database example',
            'header': 'Please upload sample-data.xls:'
        })


def drop_db(request):
    drop_tables()
    return HttpResponse("Done dropping tables")


# Print iterations progress

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def survey_result(request):
    return HttpResponse("HI")


import multiprocessing
import threading

from _thread import start_new_thread
def bulk_sub_data(data, counter):
    DataPointsVisit.objects.bulk_create(data)
    print(f"Done with sub dataset nr. {counter}")
    return True


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

@require_http_methods(['GET', 'POST', 'FILES'])
#@use_token_auth
#@permission_classes([IsAuthenticated])
def import_pkl(request):
    if request.method == "GET":
        return render(request, 'upload-pkl.html')
    else:
        if request.FILES.get('file'):
            f = request.FILES.get('file')
            fi = UserFile.objects.create(file=f, name=f.name)
            df = pd.read_pickle(fi.file.path)
            df.to_csv(fi.file.path + ".csv")
            print("Column headers: " + str(df.columns.values.tolist()))

            size = len(df.index)
            i=0
            datapoints = []
            print("delete old database \n")
            DataPointsVisit.objects.all().delete()
            cpu_count = multiprocessing.cpu_count()
            print(f"available cpus: {cpu_count} \n")
            print(f"Writing with up to {cpu_count*2} Threads \n")
            #printProgressBar(0, size, prefix = 'Progress:', suffix = 'Complete', length = 50)
            print(len(df.index))
            for index, row in df.iterrows():

                if index >= 80000:
                    break

                i+=1
                #if row['ATTRIBUTE'] == "SARASUM":
                    #print("HALLO")
                data = DataPointsVisit(PID = row['PID'],TIMESTAMP = row['TIMESTAMP'],VALUE = row['VALUE'],ATTRIBUTE = row['ATTRIBUTE'],VISIT = row['VISIT'],SOURCE = row['SOURCE'])
                datapoints.append(data)
                #printProgressBar(i, size, prefix = 'Progress:', suffix = 'Complete', length = 50)
                #print("\r" + str(100 * i /size) + "%")
            divided_data = split(list(datapoints), cpu_count*2)
            print("write to db...")
            counter = 0
            print(f"Writing with {cpu_count*2} subpackages...")
            for sub_data in divided_data:
                id = start_new_thread(bulk_sub_data, (sub_data,counter))
                counter +=1
                print(f"Write subpackage with thread id {id}")
                '''
            while counter < cpu_count*2:
                time.sleep(10)
                '''
            print("Done...")

            gui_messages.success(request, "You successfully uploaded a data sheet")
            return HttpResponseRedirect("")


        else:
            gui_messages.error(request, 'Something went wrong with the import...')
            return HttpResponseRedirect("")

@require_http_methods(['POST', 'FILES'])
def dump_as_json(request):


    if request.FILES.get('file'):

        client = MongoClient('localhost', 27017)
        #print(client.server_info())
        db = client['clinical_backend']
        collection = db['clinical_backend']
        #print(collection)


        f = request.FILES.get('file')
        fi = UserFile.objects.create(file=f, name=f.name)
        df = pd.read_pickle(fi.file.path)
        df.to_csv(fi.file.path + ".csv")
        print("Column headers: " + str(df.columns.values.tolist()))

        print("Dump as json")
        #VisitsDataSet.objects.all().delete()
        '''
        dataset = VisitsDataSet.objects.create()
        dataset.data_json = json.dumps(df.to_json())
        '''
        print("WRITING TO DB...")
        #dataset.save()
        id = collection.insert_one(json.loads(df.to_json()))
        print(id)

        print("Done...")

        gui_messages.success(request, "You successfully uploaded a data sheet")
        return HttpResponseRedirect("/clinical-backend/upload/import-pkl/")


    else:
        gui_messages.error(request, 'Something went wrong with the import...')
        return HttpResponseRedirect("/clinical-backend/upload/import-pkl/")




# @login_required
def landing(request):
    return render(request, 'landing.html', {'apis': settings.APILIST})



def welcome_upload(request):
    return render(request,"welcome_upload.html")
