from django.urls import path

from fhir_apis import views

urlpatterns = [
    path("get/all-datapoints", views.fhir_export_all_datapoints, name="fhir_all_datapoints"),
    path("get/patient/<source>/<pid>", views.fhir_export_patient, name="fhir_patient"),
    path("get/observation/<id>", views.fhir_export_observation, name="fhir_observation"),
    path("get/datapoints/id/all", views.all_datapoint_ids, name="fhir_all_dp_ids")
]