from django.contrib import admin
from ci_system.models import CiSystem, ProductCi, Status, ProductCiStatus


admin.site.register([CiSystem, ProductCi, Status, ProductCiStatus])
