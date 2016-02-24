from api import views
from django.conf.urls import url

urlpatterns = [
    url(r'^import_file/$', views.import_file, name='api_import_file'),
]
