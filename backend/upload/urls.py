from django.urls import path

from . import views

urlpatterns = [
    #path('', views.index, name='index'),
    path('datamodel/', views.import_datamodel, name='upload_datamodel'),
    path('data/', views.import_data_main, name='upload_data'),
    #path('download_eav/', views.download_eav, name='download_data'),
    #path('datatable/data/',views.import_data_main_after_handson, name="upload_data_datatable"),
    #path('ajax/upload-file/',views.upload_file_to_server,name="ajax_upload_file"),
    #path('ajax/get-broken-lines',views.get_broken_lines,name="get_broken_lines"),
    #path('ajax/get-broken-lines-model', views.get_broken_lines_model, name="get_broken_lines_model"),
    #path('ajax/get-ignored-lines-model', views.get_ignored_lines_model, name="get_ignored_lines_model"),
    path('import-pkl/', views.import_pkl, name="import_pkl"),
    path('import-pkl-dump/', views.dump_as_json, name="import_pkl_dump"),

    #path('convert', views.excel2csv, name='convert'),
    #path('download/(.*)', views.download, name="download"),
    #path('download_attachment/(.*)/(.*)', views.download_as_attachment,
    #    name="download_attachment"),
    #path('exchange/(.*)', views.exchange, name="exchange"),
    #path('parse/(.*)', views.parse, name="parse"),
    #path('import_sheet/', views.import_sheet, name="import_sheet"),
    #path('export/(.*)', views.export_data, name="export"),
    #path('handson_view/', views.handson_table, name="handson_view"),

    # handson table view
    path('datatable/', views.datatable_view, name="datatable"),
    path('datamodeltable/', views.datamodeltable_view, name="datamodeltable"),
    path('get-csv-as-json/', views.get_csv_as_json, name="get_csv_as_json"),
    path('get-xlsx-as-json/', views.get_xlsx_as_json, name="get_xlsx_as_json"),
    path('embedded_handson_view/',
        views.embed_handson_table, name="embed_handson_view"),
    path('embedded_handson_view_single/',
        views.embed_handson_table_from_a_single_table,
        name="embed_handson_view_single"),
    # survey_result
    path('survey_result/',
        views.survey_result, name='survey_result'),

    # testing purpose
    path('import_using_isave/',
        views.import_data_using_isave_book_as),
    path('import_sheet_using_isave/',
        views.import_sheet_using_isave_to_database),
    path('import_without_bulk_save/',
        views.import_without_bulk_save, name="import_no_bulk_save"),

    # APP
    #path('api/delete_db', views.drop_db, name="drop_db"),
    path('welcome-upload', views.welcome_upload, name="welcome_upload")

]
