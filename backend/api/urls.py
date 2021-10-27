from django.urls import path
from . import views
from graphene_django.views import GraphQLView

urlpatterns = [
    path('get/datapoints', views.datapoints_list, name="get_all_datapoints"),
    path('get/genetic-data', views.get_genetic_data, name="genetic_get"),
    path('post/genetic-data', views.post_genetic_data, name="genetic_post"),
    path('access-token', views.acces_token, name="access_token"),
    path("graphql", GraphQLView.as_view(graphiql=True)),
    path("getdata", views.getdata, name="getdata"),
    path('init', views.initialize_session, name="init"),
    path('filter-plot', views.filter_plot, name="filter_plot"),
    path('filter-reset', views.filter_reset, name="filter_reset"),
    path('filter-edit', views.filter_edit, name="filter_edit"),
    path('filter-recall', views.filter_recall,name="filter_recall"),
    path('filter-concept',views.filter_concept, name="filter_concept"),
    path('subgroup-define', views.subgroup_define, name="subgroup_define"),
    path('subgroup-delete', views.subgroup_delete, name="subgroup_delete"),
    path('reset-session', views.reset_session, name="session_reset"),
    path("update-filter", views.filter_update, name="update_filter")
]
