from decimal import Decimal

from django.test import TestCase, tag
from django.utils import timezone

from smart_meter.models import SmartMeter
from smart_meter.tests.mixin import MeterTestMixin


@tag('model')
class TestUserMeterModel(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()

    @tag('manager')
    def test_meter_manager_user_meters_success(self):
        # given
        self.create_smart_meter(self.user)
        self.create_smart_meter()  # some other meter
        self.create_smart_meter(self.user)
        self.create_smart_meter()  # some other meter
        self.create_smart_meter(self.user)
        # when
        meters = SmartMeter.objects.user_meters(self.user.id)
        # then
        self.assertEqual(3, meters.count())
        for m in meters:
            self.assertEqual(m.user_id, self.user.id)

    @tag('manager')
    def test_meter_manager_create_success(self):
        # given
        meter_data = self.default_smart_meter_data()
        # when
        meter = SmartMeter.objects.create(self.user, **meter_data)
        # then
        self.assertEqual(meter.user_id, self.user.id)
        self.assertEqual(meter.sn_power, meter_data['sn_power'])
        self.assertEqual(meter.sn_gas, meter_data['sn_gas'])
        self.assertEqual(meter.power_import_1, meter_data['power_import_1'])
        self.assertEqual(meter.power_import_2, meter_data['power_import_2'])

    @tag('manager')
    def test_meter_manager_new_measurement_success(self):
        # given
        meter_data = {
            'power': {
                'sn': '132jimmy456',
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
                'sn': '132johnny456',
                'timestamp': timezone.now(),
                'gas': Decimal('123.321'),
            },
            'solar': {
                'timestamp': timezone.now(),
                'solar': Decimal('0.5'),
            },
        }
        # when
        meter = SmartMeter.objects.new_measurement(self.user, **meter_data)
        # then
        self.assertEqual(meter.user_id, self.user.id)
        self.assertEqual(1, meter.powermeasurement_set.count())
        self.assertEqual(1, meter.gasmeasurement_set.count())
        self.assertEqual(1, meter.solarmeasurement_set.count())

    @tag('manager')
    def test_meter_manager_new_measurement_minimal_data_success(self):
        # given
        meter_data = {
            'power': {
                'sn': '132jimmy456',
                'timestamp': timezone.now(),
                'import_1': Decimal('123.321'),
                'import_2': Decimal('124.421'),
                'export_1': Decimal('12.31'),
                'export_2': Decimal('31.12'),
                'actual_import': Decimal('1.321'),
                'actual_export': Decimal('0'),
                'tariff': 1,
            },
        }
        # when
        meter = SmartMeter.objects.new_measurement(self.user, **meter_data)
        # then
        self.assertEqual(meter.user_id, self.user.id)
        self.assertEqual(1, meter.powermeasurement_set.count())
        self.assertEqual(0, meter.gasmeasurement_set.count())
        self.assertEqual(0, meter.solarmeasurement_set.count())
