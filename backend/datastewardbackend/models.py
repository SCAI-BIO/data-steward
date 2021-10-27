from django.db import models
from upload.models import DatamodelAttribute, DatamodelAttributeMapping, DatamodelCodeMapping, DatamodelUnit, \
    DatamodelSource
import logging
import requests
from django.conf import settings

from urllib.parse import urlencode

class SemanticAsset(models.Model):
    name = models.CharField(max_length=1028)
    description = models.TextField()
    provenenace = models.CharField(max_length=1028, blank=True, null=True)


class LiteralModel(models.Model):
    label = models.CharField(max_length=1024)
    description = models.TextField(null=True, blank=True)
    synonyms = models.TextField(null=True, blank=True)

    def add_synonym(self, syn):
        self.synonyms += ";;" + syn

    def get_synonyms(self):
        return self.synonyms.split(";;")


class MeasurementLocation(LiteralModel):
    info = "This describes the WHERE of a measurement"


class MeasurementObject(LiteralModel):
    info = "This describes the WHAT of a measureemnt"


class MeasurementMethod(LiteralModel):
    info = "This describes the HOW of a measurement"


class Measurement(models.Model):
    object_of_measurement = models.ForeignKey(
        MeasurementObject, on_delete=models.CASCADE)
    location_of_measurement = models.ForeignKey(
        MeasurementLocation, on_delete=models.CASCADE, null=True, blank=True)
    method_of_measurement = models.ForeignKey(
        MeasurementMethod, on_delete=models.CASCADE, null=True, blank=True)


class BasicDataPoint(models.Model):
   
    timestamp = models.CharField(max_length=1024, null=True, blank=True)
    variable = models.ForeignKey(to=DatamodelAttribute, null=True, blank=True, on_delete=models.CASCADE)
    variable_raw = models.CharField(max_length=1024)
    value = models.CharField(max_length=1024)
    pid = models.CharField(max_length=1024)
    is_mapped = models.BooleanField(default=False)
    source = models.ForeignKey(to=DatamodelSource, null=True, blank=True, on_delete=models.CASCADE)
    

    def set_variable(self, all_attributes, all_mappings, all_code_mappings):
        logger = logging.getLogger("BasicDataPoint Logger")
        #logger.setLevel(logging.DEBUG)
        logger.debug("Trying to set variable...")
        found_variable = False
        created_new_from_ols = False
        for attr in all_attributes:
            if self.variable_raw == attr.Attribute:
                self.variable = attr
                logger.debug("Found variable in backend!")
                found_variable = True
                break
                
        if not found_variable:
            for mapping in all_mappings:
                if mapping.Source_Attribute == self.variable_raw:
                    self.variable = mapping.Target_Attribute
                    found_variable = True
                    logger.debug("Found mapping for variable!")
                    if mapping.Transformation: ## in case that there is a tranfromation the current value needs to be encoded
                        
                        cms = all_code_mappings.filter(Code_Mapping=mapping.Transformation)
                        conversion_map = {m.Source_Value: m.Target_Equivalent for m in cms}
                        if conversion_map:
                            try:
                                self.value = conversion_map[self.value]
                            except KeyError:
                                logger.error("Value '" + str(self.value) + "' not included in code mapping '" + mapping.Transformation + "'!")
                    break

        if not found_variable and settings.USE_OLS and False: ## search for the variable in OLS // dont use at the moment 
            logging.debug("Searching through OLS.")
            ols_response = requests.get(settings.OLS_URL + f"/ols/api/select?q={self.variable_raw}&rows=1000").json()['response']
            if ols_response['numFound']>0:
                description = ""
                for i in range(0, ols_response['numFound']):
                    print(i) ## search for description in all found ontologies
                    result = ols_response['docs'][i] ## Take the first one in the result 
                    iri = result['iri']
                    ontology = result["ontology_name"]
                    url_encoded_ = urlencode({'test':urlencode({'test':iri}).split("=")[1]}).split("=")[1] ## double encode url 
                    term_query = dict(requests.get(settings.OLS_URL + f"/ols/api/ontologies/{ontology}/terms/" + url_encoded_).json())
                    if 'description' in term_query.keys() and term_query['description'] != None and 'label' in term_query.keys():
                        description = term_query['description']
                        label = term_query['label']
                        ## Create a new variable 
                        none_unit = DatamodelUnit.objects.filter(Unit="None")[0]
                        attr = DatamodelAttribute(Attribute=self.variable_raw, Attribute_Description=description, Attribute_Tooltip=label,IRI=iri,  Unit=none_unit, Datatype="string")
                        
                        attr.save()
                        self.variable = attr
                        logger.debug("Imported from OLS!")
                        found_variable = True
                        created_new_from_ols= True
                        break
        return found_variable, created_new_from_ols