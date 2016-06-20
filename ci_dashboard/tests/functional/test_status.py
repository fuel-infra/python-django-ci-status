from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from ci_dashboard.models import CiSystem, Status


class StatusFunctionalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.ci = CiSystem.objects.create(url='http://localhost/')
        self.user = User.objects.create_superuser(
            'tempo', 'temporary@gmail.com', 'tempo')

    def test_new_status_author_defaults_to_auth_user(self):
        short_summary = 'new status'
        self.client.login(username=self.user.username, password='tempo')

        self.client.get('/')

        response = self.client.post(reverse('status_new'), {
            'summary': short_summary,
            'ci_system': self.ci.pk,
            'status_type': 1
        })

        status = Status.objects.last()

        self.assertRedirects(response, expected_url=reverse(
            'status_detail',
            kwargs={'pk': status.pk})
        )
        self.assertEqual(status.summary, short_summary)
        self.assertEqual(status.user, self.user)

    def test_unauthenticated_user_can_not_set_status(self):
        response = Client().post(reverse('status_new'), {
            'summary': 'new',
            'ci_system': self.ci.pk,
            'status_type': 1
        })
        self.assertRedirects(response, reverse('admin:login') + '?next=' + reverse('status_new'))
