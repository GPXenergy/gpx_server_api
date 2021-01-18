from decimal import Decimal

from django.test import TestCase, tag
from django.utils import timezone, dateparse
from rest_framework import status
from rest_framework.test import APIClient

from smart_meter.tests.mixin import MeterTestMixin


@tag('api')
class TestPowerMeasurementListGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        # create 60 measurements for past hour
        cls.start = timezone.now() - timezone.timedelta(minutes=50 * 5)
        cls.measurements = [
            cls.create_power_measurement(cls.meter, timestamp=cls.start + timezone.timedelta(minutes=i * 5))
            for i in range(50)
        ]
        for m in cls.measurements:
            m.refresh_from_db()

        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_power_measurement_list_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start,
            'timestamp_before': self.start + timezone.timedelta(hours=6),
        }
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(50, len(response.data))
        for i in range(50):
            # Averages equal the actual value
            self.assertEqual(str(self.measurements[i].power_imp), response.data[i].get('power_imp'))

    @tag('filter')
    def test_power_measurement_list_get_filter_days_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start - timezone.timedelta(days=2),
            'timestamp_before': self.start + timezone.timedelta(days=2),
        }
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(5, len(response.data))
        for i in range(5):
            # Averages equal averages of the hour
            timestamp = dateparse.parse_datetime(response.data[i].get('timestamp')).astimezone(timezone.utc)
            this_hour_measurements = [
                measurement.power_exp
                for measurement in self.measurements
                if measurement.timestamp.day == timestamp.day and measurement.timestamp.hour == timestamp.hour
            ]
            avg_import = sum(this_hour_measurements) / len(this_hour_measurements)

            self.assertAlmostEqual(avg_import, Decimal(response.data[i].get('power_exp')), 3)

    @tag('filter')
    def test_power_measurement_list_get_filter_timestamp_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start + timezone.timedelta(minutes=20),
            'timestamp_before': self.start + timezone.timedelta(minutes=40),
        }
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(5, len(response.data))

    @tag('validation')
    def test_power_measurement_list_get_filter_no_timestamp_as_user_fail_missing_start_stop(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': '',
            'timestamp_before': '',
        }
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('validation')
    def test_power_measurement_list_get_no_filter_as_user_fail_timestamp_filter_required(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('permission')
    def test_power_measurement_list_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_power_measurement_list_get_other_meter_as_user_fail_forbidden(self):
        # given
        other_meter = self.create_smart_meter()
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, other_meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_power_measurement_list_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestPowerMeasurementListPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_power_measurement_list_post_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.post(self.MeterUrls.power_measurement_url(self.user.pk, self.meter.pk), {})
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)


@tag('api')
class TestGasMeasurementListGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        # create 60 measurements for past hour
        cls.start = timezone.now() - timezone.timedelta(minutes=60)
        for i in range(60):
            cls.create_gas_measurement(cls.meter, timestamp=cls.start + timezone.timedelta(minutes=i))
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_gas_measurement_list_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start - timezone.timedelta(hours=2),
            'timestamp_before': self.start + timezone.timedelta(hours=2),
        }
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(60, len(response.data))

    @tag('filter')
    def test_gas_measurement_list_get_filter_timestamp_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start + timezone.timedelta(minutes=20),
            'timestamp_before': self.start + timezone.timedelta(minutes=40),
        }
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(21, len(response.data))

    @tag('filter')
    def test_gas_measurement_list_get_filter_no_timestamp_as_user_fail_missing_start_stop(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': '',
            'timestamp_before': '',
        }
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('filter')
    def test_gas_measurement_list_get_no_filter_as_user_fail_timestamp_filter_required(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('permission')
    def test_gas_measurement_list_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_gas_measurement_list_get_other_meter_as_user_fail_forbidden(self):
        # given
        other_meter = self.create_smart_meter()
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, other_meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_gas_measurement_list_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestGasMeasurementListPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_gas_measurement_list_post_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.post(self.MeterUrls.gas_measurement_url(self.user.pk, self.meter.pk), {})
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)


@tag('api')
class TestSolarMeasurementListGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        # create 60 measurements for past hour
        cls.start = timezone.now() - timezone.timedelta(minutes=60)
        for i in range(60):
            cls.create_solar_measurement(cls.meter, timestamp=cls.start + timezone.timedelta(minutes=i))
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_solar_measurement_list_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start - timezone.timedelta(hours=2),
            'timestamp_before': self.start + timezone.timedelta(hours=2),
        }
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(60, len(response.data))

    @tag('filter')
    def test_solar_measurement_list_get_filter_timestamp_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': self.start + timezone.timedelta(minutes=20),
            'timestamp_before': self.start + timezone.timedelta(minutes=40),
        }
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(21, len(response.data))

    @tag('filter')
    def test_solar_measurement_list_get_filter_no_timestamp_as_user_fail_missing_start_stop(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'timestamp_after': '',
            'timestamp_before': '',
        }
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('filter')
    def test_solar_measurement_list_get_no_filter_as_user_fail_timestamp_filter_required(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('permission')
    def test_solar_measurement_list_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_solar_measurement_list_get_other_meter_as_user_fail_forbidden(self):
        # given
        other_meter = self.create_smart_meter()
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, other_meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_solar_measurement_list_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestSolarMeasurementListPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_solar_measurement_list_post_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.post(self.MeterUrls.solar_measurement_url(self.user.pk, self.meter.pk), {})
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)
