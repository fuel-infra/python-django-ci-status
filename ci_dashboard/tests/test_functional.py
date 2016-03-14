from django.test import Client, TestCase


class CiDashboardFunctionalTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_page(self):
        response = self.client.get('/')

        self.assertEqual(200, response.status_code)
        self.assertIn('Dashboard', response.content)
