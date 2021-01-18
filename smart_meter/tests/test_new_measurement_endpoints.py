from decimal import Decimal

import pytz
from django.test import TestCase, tag
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from smart_meter.models import SmartMeter
from smart_meter.tests.mixin import MeterTestMixin


@tag('api')
class TestNewMeasurementGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.meter1 = cls.create_smart_meter(cls.user, name='Home')

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_new_measurement_view_get_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.new_measurement_url())
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)


@tag('api')
class TestNewMeasurementPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.meter1 = cls.create_smart_meter(cls.user, name='Home')
        cls.meter1.powermeasurement_set.create(
            timestamp=timezone.now() - timezone.timedelta(minutes=6),
            power_imp=1.33,
            power_exp=1.33,
        )
        cls.meter1.gasmeasurement_set.create(
            timestamp=timezone.now() - timezone.timedelta(minutes=6),
            gas=1.33,
            total=444.33,
        )
        cls.meter1.solarmeasurement_set.create(
            timestamp=timezone.now() - timezone.timedelta(minutes=6),
            solar=4.1,
        )

    def setUp(self):
        self.default_payload = {
            'power': {
                'sn': self.meter1.sn_power,
                'timestamp': timezone.now(),
                'import_1': Decimal('123.321'),
                'import_2': Decimal('124.421'),
                'export_1': Decimal('12.31'),
                'export_2': Decimal('31.12'),
                'actual_import': Decimal('1.321'),
                'actual_export': Decimal('0'),
                'tariff': 1,
            },
            'gas': {
                'sn': self.meter1.sn_gas,
                'timestamp': timezone.now(),
                'gas': Decimal('123.321'),
            },
            'solar': {
                'timestamp': timezone.now(),
                'solar': Decimal('0.5'),
            },
        }
        self.client = APIClient()

    @tag('standard')
    def test_new_measurement_view_post_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = self.default_payload
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.meter1.refresh_from_db()
        self.assertEqual(payload['power']['sn'], self.meter1.sn_power)
        self.assertEqual(payload['power']['timestamp'], self.meter1.power_timestamp)
        self.assertEqual(payload['power']['import_1'], self.meter1.power_import_1)
        self.assertEqual(payload['power']['import_2'], self.meter1.power_import_2)
        self.assertEqual(payload['power']['export_1'], self.meter1.power_export_1)
        self.assertEqual(payload['power']['export_2'], self.meter1.power_export_2)
        self.assertEqual(payload['power']['actual_import'], self.meter1.actual_power_import)
        self.assertEqual(payload['power']['actual_export'], self.meter1.actual_power_export)
        self.assertEqual(payload['power']['tariff'], self.meter1.tariff)
        self.assertEqual(payload['gas']['sn'], self.meter1.sn_gas)
        self.assertEqual(payload['gas']['timestamp'], self.meter1.gas_timestamp)
        self.assertEqual(payload['gas']['gas'], self.meter1.gas)
        self.assertEqual(payload['solar']['timestamp'], self.meter1.solar_timestamp)
        self.assertEqual(payload['solar']['solar'], self.meter1.solar)
        # Meter should now have 2 measurements of each
        self.assertEqual(2, self.meter1.powermeasurement_set.count())
        self.assertEqual(2, self.meter1.gasmeasurement_set.count())
        self.assertEqual(2, self.meter1.solarmeasurement_set.count())

    @tag('variation')
    def test_new_measurement_view_post_4_minute_measurement_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = self.default_payload
        # send with measurement payloads that are 4 minutes after last measurement
        payload['power']['timestamp'] = self.meter1.last_power_measurement.timestamp + timezone.timedelta(minutes=4)
        payload['gas']['timestamp'] = self.meter1.last_gas_measurement.timestamp + timezone.timedelta(minutes=4)
        payload['solar']['timestamp'] = self.meter1.last_solar_measurement.timestamp + timezone.timedelta(minutes=4)
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        new_meter = SmartMeter.objects.get(sn_power=payload['power']['sn'])
        self.assertEqual(payload['power']['sn'], new_meter.sn_power)
        # Meter should still be 1 measurement of each
        self.assertEqual(1, self.meter1.powermeasurement_set.count())
        self.assertEqual(1, self.meter1.gasmeasurement_set.count())
        self.assertEqual(1, self.meter1.solarmeasurement_set.count())

    @tag('variation')
    def test_new_measurement_view_post_new_meter_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = self.default_payload
        payload['power']['sn'] = '999999999newmeter'
        payload['gas']['sn'] = '999999999newmetergas'
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        new_meter = SmartMeter.objects.get(sn_power=payload['power']['sn'])
        self.assertEqual(payload['power']['sn'], new_meter.sn_power)
        self.assertEqual(payload['power']['timestamp'], new_meter.power_timestamp)
        self.assertEqual(payload['power']['import_1'], new_meter.power_import_1)
        self.assertEqual(payload['power']['import_2'], new_meter.power_import_2)
        self.assertEqual(payload['power']['export_1'], new_meter.power_export_1)
        self.assertEqual(payload['power']['export_2'], new_meter.power_export_2)
        self.assertEqual(payload['power']['actual_import'], new_meter.actual_power_import)
        self.assertEqual(payload['power']['actual_export'], new_meter.actual_power_export)
        self.assertEqual(payload['power']['tariff'], new_meter.tariff)
        self.assertEqual(payload['gas']['sn'], new_meter.sn_gas)
        self.assertEqual(payload['gas']['timestamp'], new_meter.gas_timestamp)
        self.assertEqual(payload['gas']['gas'], new_meter.gas)
        self.assertEqual(payload['solar']['timestamp'], new_meter.solar_timestamp)
        self.assertEqual(payload['solar']['solar'], new_meter.solar)

    @tag('variation')
    def test_new_measurement_view_post_no_gas_solar_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = self.default_payload
        del payload['gas']
        del payload['solar']
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        new_meter = SmartMeter.objects.get(sn_power=payload['power']['sn'])
        self.assertEqual(payload['power']['timestamp'], new_meter.power_timestamp)
        self.assertIsNone(new_meter.sn_gas)
        self.assertIsNone(new_meter.gas_timestamp)
        self.assertIsNone(new_meter.gas)
        self.assertIsNone(new_meter.solar_timestamp)
        self.assertIsNone(new_meter.solar)
        self.assertEqual(2, self.meter1.powermeasurement_set.count())
        self.assertEqual(1, self.meter1.gasmeasurement_set.count())
        self.assertEqual(1, self.meter1.solarmeasurement_set.count())

    @tag('variation')
    def test_new_measurement_view_post_meter_datetime_format_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = self.default_payload
        timestamp = timezone.now().astimezone(pytz.timezone('Europe/Amsterdam'))
        payload['power']['timestamp'] = timestamp.strftime('%y%m%d%H%M%S') + 'S'
        payload['gas']['timestamp'] = timestamp.strftime('%y%m%d%H%M%S') + 'S'
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.meter1.refresh_from_db()
        for_comparison = timestamp.astimezone(pytz.utc)
        self.assertEqual(for_comparison.year, self.meter1.power_timestamp.year)
        self.assertEqual(for_comparison.month, self.meter1.power_timestamp.month)
        self.assertEqual(for_comparison.day, self.meter1.power_timestamp.day)
        self.assertEqual(for_comparison.hour, self.meter1.power_timestamp.hour)
        self.assertEqual(for_comparison.minute, self.meter1.power_timestamp.minute)
        self.assertEqual(for_comparison.second, self.meter1.power_timestamp.second)
        self.assertEqual(for_comparison.year, self.meter1.gas_timestamp.year)
        self.assertEqual(for_comparison.month, self.meter1.gas_timestamp.month)
        self.assertEqual(for_comparison.day, self.meter1.gas_timestamp.day)
        self.assertEqual(for_comparison.hour, self.meter1.gas_timestamp.hour)
        self.assertEqual(for_comparison.minute, self.meter1.gas_timestamp.minute)
        self.assertEqual(for_comparison.second, self.meter1.gas_timestamp.second)

    @tag('variation')
    def test_new_measurement_view_post_real_data_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            "power": {
                "sn": "4530303331303033323035383733373136",
                "timestamp": "201015200857S",
                "import_1": "007409.325",
                "import_2": "007397.355",
                "export_1": "000000.000",
                "export_2": "000000.000",
                "tariff": 2,
                "actual_import": "00.462",
                "actual_export": "00.000"
            },
            "gas": {
                "sn": "4730303139333430323834343236393136",
                "timestamp": "201015200000S",
                "gas": "06146.079"
            },
            "solar": None
        }
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    @tag('variation')
    def test_new_measurement_test_view_post_data_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            "power": {
                "sn": "4530303331303033323035383733373136",
                "timestamp": "201015200857S",
                "import_1": "007409.325",
                "import_2": "007397.355",
                "export_1": "000000.000",
                "export_2": "000000.000",
                "tariff": 2,
                "actual_import": "00.462",
                "actual_export": "00.000"
            },
            "gas": {
                "sn": "4730303139333430323834343236393136",
                "timestamp": "201015200000S",
                "gas": "06146.079"
            },
            "solar": None
        }
        count_before = SmartMeter.objects.count()
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url() + 'test/', payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(count_before, SmartMeter.objects.count())

    @tag('permission')
    def test_new_measurement_view_post_as_user_api_key_success(self):
        # given
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.api_key)
        payload = self.default_payload
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    # @tag('permission')
    # def test_new_measurement_view_post_as_other_user_fail_meter_connected_to_another_user(self):
    #     # given
    #     self.client.force_authenticate(self.create_user())
    #     payload = self.default_payload
    #     # when
    #     response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
    #     # then
    #     self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
    #     self.assertEqual("Meter connected to another user", response.data[0])

    # @tag('permission')
    # def test_new_measurement_view_post_as_other_user_api_key_fail_meter_connected_to_another_user(self):
    #     # given
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.create_user().api_key)
    #     payload = self.default_payload
    #     # when
    #     response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
    #     # then
    #     self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
    #     self.assertEqual("Meter connected to another user", response.data[0])

    @tag('permission')
    def test_new_measurement_view_post_as_visitor_fail_unauthorized(self):
        # given
        payload = self.default_payload
        # when
        response = self.client.post(self.MeterUrls.new_measurement_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
