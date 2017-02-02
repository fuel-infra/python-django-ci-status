from django.contrib import admin

from ci_dashboard.models import Rule, RuleCheck, CiSystem, ProductCi, Status, ProductCiStatus


class RuleAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'description',
        'rule_type',
        'trigger_type',
        'gerrit_refspec',
        'gerrit_branch',
        'ci_system',
        'is_active'
    )
    list_display = (
        'name',
        'rule_type',
        'trigger_type',
        'gerrit_refspec',
        'gerrit_branch',
        'ci_system',
        'last_updated',
        'is_active'
    )


admin.site.register(RuleCheck)
admin.site.register(Rule, RuleAdmin)
admin.site.register([CiSystem, ProductCi, Status, ProductCiStatus])
