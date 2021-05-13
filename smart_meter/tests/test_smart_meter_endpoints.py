from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, tag
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APIClient

from smart_meter.tests.mixin import MeterTestMixin


@tag('api')
class TestUserMeterListGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter1 = cls.create_smart_meter(cls.user, name='Home')
        cls.meter2 = cls.create_smart_meter(cls.user, name='Work')
        cls.meter3 = cls.create_smart_meter(cls.user, name='Patat')
        cls.group_meter = cls.create_group_meter(cls.user, cls.meter3)
        cls.meter_other = cls.create_smart_meter()
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_list_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, len(response.data))

        # Default ordering on name (Home -> Patat -> Work)
        self.assertEqual(self.meter1.pk, response.data[0]['pk'])
        self.assertEqual(self.meter3.pk, response.data[1]['pk'])
        self.assertEqual(self.meter2.pk, response.data[2]['pk'])

        meter_1_data = response.data[0]
        self.assertEqual(self.meter1.name, meter_1_data['name'])
        self.assertEqual(self.meter1.visibility_type, meter_1_data['visibility_type'])
        self.assertEqual(self.meter1.last_update, parse_datetime(meter_1_data['last_update']))
        self.assertIsNone(meter_1_data['group_participation'])

        meter_3_data = response.data[1]
        self.assertEqual(self.meter3.name, meter_3_data['name'])
        self.assertIsNotNone(meter_3_data['group_participation'])
        self.assertEqual(self.group_meter.pk, meter_3_data['group_participation']['group'])

    @tag('ordering')
    def test_user_meter_list_get_order_pk_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'ordering': 'pk'
        }
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, len(response.data))
        self.assertEqual(self.meter1.pk, response.data[0]['pk'])
        self.assertEqual(self.meter2.pk, response.data[1]['pk'])
        self.assertEqual(self.meter3.pk, response.data[2]['pk'])

    @tag('ordering')
    def test_user_meter_list_get_order_timestamp_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filter_data = {
            'ordering': '-power_timestamp'
        }
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk), filter_data)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, len(response.data))
        self.assertEqual(self.meter3.pk, response.data[0]['pk'])
        self.assertEqual(self.meter2.pk, response.data[1]['pk'])
        self.assertEqual(self.meter1.pk, response.data[2]['pk'])

    @tag('permission')
    def test_user_meter_list_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_list_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestUserMeterListPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_list_post_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.post(self.MeterUrls.user_meter_url(self.user.pk), {})
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)


@tag('api')
class TestUserMeterDetailGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        super().setUpTestData()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_detail_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.meter.pk, response.data['pk'])
        self.assertEqual(self.meter.name, response.data['name'])
        self.assertEqual(self.meter.visibility_type, response.data['visibility_type'])
        self.assertEqual(self.meter.power_timestamp, parse_datetime(response.data['power_timestamp']))
        self.assertEqual(self.meter.sn_power, response.data['sn_power'])
        self.assertEqual(self.meter.sn_gas, response.data['sn_gas'])

    @tag('permission')
    def test_user_meter_detail_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_detail_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestUserMeterDetailPut(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user, name='Home')
        super().setUpTestData()

    def setUp(self):
        self.meter.refresh_from_db()
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_detail_patch_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        patch_data = {
            'pk': 'not editable',
            'name': 'new name!!!',
            'visibility_type': 'group',
            'power_timestamp': 'not editable',
            'sn_power': 'not editable',
            'sn_gas': 'not editable',
        }
        # when
        response = self.client.patch(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk), patch_data,
                                     format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(patch_data['name'], response.data['name'])
        self.assertEqual(patch_data['visibility_type'], response.data['visibility_type'])
        # These values should stay unchanged
        self.assertEqual(self.meter.pk, response.data['pk'])
        self.assertEqual(self.meter.power_timestamp, parse_datetime(response.data['power_timestamp']))
        self.assertEqual(self.meter.sn_power, response.data['sn_power'])
        self.assertEqual(self.meter.sn_gas, response.data['sn_gas'])

    @tag('permission')
    def test_user_meter_detail_patch_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.patch(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk), {})
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_detail_patch_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.patch(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk), {})
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestUserMeterDetailDelete(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        super().setUpTestData()

    def setUp(self):
        self.meter = self.create_smart_meter(self.user, name='Home')
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_detail_delete_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        as_participant = self.create_group_participation(self.meter, self.create_group_meter())
        # when
        response = self.client.delete(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, self.user.meters.count())
        with self.assertRaises(ObjectDoesNotExist):
            # Group participant should no longer exist
            as_participant.refresh_from_db()

    @tag('validation')
    def test_user_meter_detail_delete_as_user_fail_is_manager_of_group(self):
        # given
        self.client.force_authenticate(self.user)
        group = self.create_group_meter(self.user, self.meter)
        # when
        response = self.client.delete(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('permission')
    def test_user_meter_detail_delete_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.delete(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(1, self.user.meters.count())

    @tag('permission')
    def test_user_meter_detail_delete_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.delete(self.MeterUrls.user_meter_url(self.user.pk, self.meter.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(1, self.user.meters.count())
