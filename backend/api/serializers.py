

from rest_framework.serializers import ModelSerializer
from upload.models import DataPointsVisit, GeneticJson, DataPoints

class DataPointsVisitSerializer(ModelSerializer):
    class Meta:
        model = DataPointsVisit
        fields = ['VALUE','PID','TIMESTAMP','ATTRIBUTE','VISIT','SOURCE']
class DataPointsSerializer(ModelSerializer):
    class Meta:
        model = DataPoints
        fields = ['VALUE','PID','TIMESTAMP','ATTRIBUTE','VISIT','SOURCE']

class DataPointsVisitSerializer_light(ModelSerializer):
    class Meta:
        model = DataPointsVisit
        fields= ['PID', 'VISIT','TIMESTAMP','VALUE']



class GeneticJsonSerializer(ModelSerializer):
    class Meta:
        model = GeneticJson
        fields = ['json_string', 'data_id']
