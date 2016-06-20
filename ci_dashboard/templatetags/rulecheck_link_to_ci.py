from django import template

from ci_dashboard import constants


register = template.Library()


@register.simple_tag
def rulecheck_link_to_ci(rule_check, type_product=False):
    rule = rule_check.rule
    href = rule_check.link_to_ci()

    if rule.rule_type == constants.RULE_JOB:
        href = href + '/' + str(rule_check.build_number)

    if type_product:
        link = '''
            <a class="job-link" href="{href}" target="_blank">
              <small>{text}</small>
            </a>
        '''

        text = '{rule_type} <em>{name} #{number}</em>'.format(
            rule_type=rule.rule_type_text(),
            name=rule.name,
            number=rule_check.build_number
        )
    else:
        link = '<a href="{href}" target="_blank">{text}</a>'
        text = rule.rule_type_text() + ' Link'

    return link.format(href=href, text=text)
