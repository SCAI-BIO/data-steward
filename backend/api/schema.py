import graphene

from graphene_django.types import DjangoObjectType, ObjectType

from upload.models import DataPointsVisit, DatamodelAttribute


class DataPointsVisitType(DjangoObjectType):
    class Meta:
        model = DataPointsVisit

class AttributeType(DjangoObjectType):
    class Meta:
        model = DatamodelAttribute

class Query(ObjectType):
    all_datapoints = graphene.List(DataPointsVisitType)
    datapoints_from_pid_list = graphene.List(DataPointsVisitType, pids=graphene.String())
    all_attributes = graphene.List(AttributeType)

    def resolve_all_datapointsvisit(self, info, **kwargs):
        return DataPointsVisit.objects.all()

    def resolve_all_attributes(self, info, **kwargs):
        return DatamodelAttribute.objects.all()

    def resolve_datapoints_from_pid_list(self,info, **kwargs):
        patient_ids = kwargs.get('pids').split(",")
        return DataPointsVisit.objects.filter(PID__in=patient_ids)

schema = graphene.Schema(query=Query)
