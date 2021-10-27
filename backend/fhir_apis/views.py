import orjson
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404

from datastewardbackend.models import BasicDataPoint

from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.list import List

from viewer import settings


@api_view(['GET'])
def fhir_export_all_datapoints(request):
    all_dpts = BasicDataPoint.objects.exclude(variable__isnull=True)

    all_patients = all_dpts.values("pid").distinct()
    list_entries = []
    for patient in all_patients:
        patients_dpts = all_dpts.filter(pid=patient['pid'])

        for dtps in patients_dpts:
            observation_obj = {
                "identifier": [
                    {
                        "value": settings.BASE_HTTP_URL + f"/fhir/get/observation/{dtps.id}"
                    },
                    {
                        "value": dtps.pid + "@" + dtps.source
                    }
                ],
                "subject": {
                    "reference": patient['pid']
                },
                "status": "final",
                "code": {
                    "text": dtps.variable.Attribute
                },
                "valueString": dtps.value,
                "effectiveTiming": {
                    "code": {
                        "text": dtps.timestamp
                    }
                }
            }
            if dtps.source:
                observation_obj["performer"] = [{
                    "reference": dtps.source.Source
                }]
            fhir_observation = Observation(**observation_obj)
            list_entries.append(
                orjson.loads(fhir_observation.json())
            )
    return JsonResponse(list_entries, safe=False, status=200)


@api_view(['GET'])
def fhir_export_patient(request, source, pid):
    patient = BasicDataPoint.objects.filter(source=source, pid=pid)
    if patient.exists():
        number_of_obs = len(patient)
        patient_object = {
            "active": True,
            "identifier": [
                {
                    "value": pid + "@" + source
                }
            ],
            "text": {
                "fhir_comments": [
                    "Number of observations for this patient: " + number_of_obs
                ]
            },
            "managingOrganization": {
                "reference": source
            }
        }
        patient = Patient(**patient_object)
        return JsonResponse(orjson.loads(patient.json()), status=200)
    else:
        return JsonResponse({}, status=404)


@api_view(['GET'])
def fhir_export_observation(request, id):
    observation = get_object_or_404(BasicDataPoint, id=id)
    # print(observation)
    observation_obj = {
        "subject": {
            "reference": settings.BASE_HTTP_URL + f"/fhir/get/patient/<source>/{observation.pid}"
        },
        "status": "final",
        "code": {
            "text": observation.variable.Attribute
        },
        "valueString": {
            observation.value
        },
        "effectiveTiming": {
            "code": {
                "text": observation.timestamp
            }
        }

    }
    observation = Observation(**observation)
    return JsonResponse(orjson.loads(observation.json()), status=200)
