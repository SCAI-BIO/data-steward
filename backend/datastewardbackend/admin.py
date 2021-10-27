from django.contrib import admin#
from .models import SemanticAsset, BasicDataPoint

# Register your models here.


class BasicPointAdmin(admin.ModelAdmin):
    search_fields = ("variable_raw","variable__Attribute" )

admin.site.register(SemanticAsset)
admin.site.register(BasicDataPoint, BasicPointAdmin)


