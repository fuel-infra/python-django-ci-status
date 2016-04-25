from ci_system import views
from django.conf.urls import url

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.status_detail, name='status_detail'),
    url(r'^new/(?P<ci_id>\d+)/$', views.status_new, name='status_new'),
    url(r'^new/$', views.status_new, name='status_new'),
    url(r'^(?P<pk>\d+)/edit/$', views.status_edit, name='status_edit'),
    url(r'^(?P<pk>\d+)/delete/$', views.status_delete, name='status_delete'),
]
