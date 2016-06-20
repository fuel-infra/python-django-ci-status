from django.core.exceptions import ValidationError
from django.test import TestCase

from ci_dashboard import constants
from ci_dashboard.models import ProductCi, ProductCiStatus


class ProductCiStatusTests(TestCase):

    def setUp(self):
        self.summary = 'all down'
        self.product_ci = ProductCi.objects.create(
            name='Product', is_active=True, version='1.0')

    def test_string_representation(self):
        status = ProductCiStatus(
            summary=self.summary,
            status_type=constants.STATUS_SUCCESS,
            product_ci=self.product_ci)

        self.assertEqual(
            str(status),
            'Success (product: "Product")'
        )

    def test_created_with_valid_fields(self):
        ProductCiStatus.objects.create(
            summary=self.summary,
            product_ci=self.product_ci,
            version='1.0',
            status_type=constants.STATUS_SUCCESS).full_clean()

    def test_not_created_with_invalid_fields(self):
        with self.assertRaises(ValidationError):  # missed product_ci
            ProductCiStatus(summary='sum', version='1.0').full_clean()

        with self.assertRaises(ValidationError):  # missed summary
            ProductCiStatus(
                product_ci=self.product_ci,
                version='1.0'
            ).full_clean()

        with self.assertRaises(ValidationError):  # missed version
            ProductCiStatus(
                product_ci=self.product_ci,
                summary='sum'
            ).full_clean()

        ProductCiStatus(
            summary=self.summary,
            version='1.0',
            product_ci=self.product_ci
        ).full_clean()
