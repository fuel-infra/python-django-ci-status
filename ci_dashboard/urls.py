"""ci_dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from ci_dashboard import views
import ci_system.views

admin.autodiscover()

urlpatterns = [
    url(r'^$', views.index, name='ci_dashboard_index'),
    url(r'^dashboard/$', views.dashboard, name='ci_dashboard_dashboard'),
    url(r'^statuses/', include('ci_system.urls')),
    url(r'^import_file/$', ci_system.views.import_file, name='import_file'),
    url(r'^admin/', admin.site.urls),
    url(
        r'^history/(?P<pk>\d+)/$',
        views.ci_status_history,
        name='ci_status_history'
    ),

    url(r'^api/', include('api.urls')),

    url(r'^accounts/login/$',
        'django.contrib.auth.views.login',
        {'template_name': 'ci_dashboard/login.html'}, name='login'),
    url(r'^accounts/logout/$',
        'django.contrib.auth.views.logout',
        name='logout'),
]
