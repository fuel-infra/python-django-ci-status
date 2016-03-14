STATUS_SUCCESS = 1
STATUS_FAIL = 2
STATUS_SKIP = 4
STATUS_ABORTED = 8
STATUS_IN_PROGRESS = 16  # Q: Do we really need it?
STATUS_ERROR = 32

JENKINS_STATUSES = {
   'SUCCESS': STATUS_SUCCESS,
   'FAILURE': STATUS_FAIL,
   'SKIPPED': STATUS_SKIP,
   'ABORTED': STATUS_ABORTED,
   'IN_PROGRESS': STATUS_IN_PROGRESS,
   'ERROR': STATUS_ERROR,
}

STATUS_TYPE_CHOICES = (
    (STATUS_SUCCESS, 'Success'),
    (STATUS_FAIL, 'Failed'),
    (STATUS_SKIP, 'Skipped'),
    (STATUS_ABORTED, 'Aborted'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_ERROR, 'Error'),
)

RULE_JOB = JOB_RULE = 1
RULE_VIEW = VIEW_RULE = 2
RULE_TYPE_CHOICES = (
    (JOB_RULE, 'Job'),
    (VIEW_RULE, 'View'),
)
DEFAULT_RULE_TYPE = 'Job'

TRIGGER_TIMER = 1
TRIGGER_GERRIT = 2
TRIGGER_MANUAL = 4
TRIGGER_ANY = 7
TRIGGER_TYPE_CHOICES = (
    (TRIGGER_TIMER, 'Timer'),
    (TRIGGER_GERRIT, 'Gerrit trigger'),
    (TRIGGER_MANUAL, 'Manual'),
    (TRIGGER_ANY, 'Any'),
)
DEFAULT_TRIGGER_TYPE = 'Gerrit trigger'
TRIGGER_MESSAGES = {
    TRIGGER_TIMER: 'Started by timer',
    TRIGGER_GERRIT: 'Triggered by Gerrit',
    TRIGGER_MANUAL: 'Started by user',
    TRIGGER_ANY: '',
}

LDAP_USER_PERMISSIONS = (
    action + '_' + model
    for action in ('add', 'change', 'delete')
    for model in (
        'productci',
        'cisystem',
        'rulecheck',
        'rule',
        'status',
        'productcistatus',
    )
)
