from django.contrib import admin


from .models import *

admin.site.register(DatamodelSource)
admin.site.register(DatamodelUnit)

admin.site.register(DatamodelCode)

admin.site.register(DatamodelCodeMapping)
admin.site.register(DataPointsVisit)


class DatamodelAtributeAdmin(admin.ModelAdmin):

    search_fields = ('Attribute', "Attribute_Description")

class DatamodelAttributeMappingAdmin(admin.ModelAdmin):
    search_fields = ("Source_Attribute", "Target_Attribute__Attribute", "Source__Source", "Source__Abbreviation")


admin.site.register(DatamodelAttribute, DatamodelAtributeAdmin)
admin.site.register(DatamodelAttributeMapping, DatamodelAttributeMappingAdmin)