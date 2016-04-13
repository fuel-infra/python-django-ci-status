from django.contrib import admin

from ci_checks.models import Rule, RuleCheck


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
