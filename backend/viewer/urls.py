"""viewer URL Configuration"""
from django.contrib import admin
from django.urls import include, path
from upload.views import drop_db,landing
from django.conf import settings
from django.conf.urls import url
from users.views import login_html_view, register, user_is_logged_in
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path(settings.BASEPATH + 'upload/', include('upload.urls')),
    path(settings.BASEPATH + '', landing, name="landing"),
    path(settings.BASEPATH + 'admin/', admin.site.urls),
    #path(settings.BASEPATH + 'api-auth/', include('rest_framework.urls')),
    path(settings.BASEPATH + "fhir/", include('fhir_apis.urls')),
    #path(settings.BASEPATH + 'keycloak/', include('django_keycloak.urls')),
    path(settings.BASEPATH + 'api-steward/', include('datastewardbackend.urls')),
    path(settings.BASEPATH + 'auth/', include('djoser.urls')),
    path(settings.BASEPATH + "auth/", include('djoser.urls.authtoken')),
    path(settings.BASEPATH + "login/", login_html_view),
    path(settings.BASEPATH + "register/", register),
    path(settings.BASEPATH + "is-logged-in/", user_is_logged_in),
    path(settings.BASEPATH + "graphql",csrf_exempt(GraphQLView.as_view(graphiql=True)))
]
