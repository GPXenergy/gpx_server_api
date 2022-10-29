from django.conf import settings
from django.test import TestCase, tag
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APIClient

from smart_meter.models import GroupMeter, SmartMeter
from smart_meter.tests.mixin import MeterTestMixin


@tag('api')
class TestGroupMeterListGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        # meter 1 has group managed by user
        cls.meter_1 = cls.create_smart_meter(cls.user)
        cls.group_1 = cls.create_group_meter(cls.user, cls.meter_1)
        # meter 2 has group managed by another user
        cls.meter_2 = cls.create_smart_meter(cls.user)
        cls.group_2 = cls.create_group_meter()
        cls.create_group_participation(cls.meter_2, cls.group_2)
        # meter 3 had a group but no active participation
        cls.meter_3 = cls.create_smart_meter(cls.user)
        cls.group_3 = cls.create_group_meter()
        participation_3 = cls.create_group_participation(cls.meter_3, cls.group_3)
        participation_3.leave()
        participation_3.save()
        # meter 4 has no group
        cls.meter_4 = cls.create_smart_meter(cls.user)
        # some other group meter
        cls.some_other_group = cls.create_group_meter()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_group_meter_list_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        # group 1
        self.assertEqual(self.group_1.pk, response.data[0].get('pk'))
        self.assertEqual(self.group_1.name, response.data[0].get('name'))
        self.assertEqual(self.group_1.manager_id, response.data[0].get('manager'))
        self.assertEqual(self.group_1.created_on, parse_datetime(response.data[0].get('created_on')))
        self.assertEqual(self.group_1.public, response.data[0].get('public'))
        self.assertEqual(str(self.group_1.public_key), response.data[0].get('public_key'))
        self.assertEqual(str(self.group_1.invitation_key), response.data[0].get('invitation_key'))
        # group 2
        self.assertEqual(self.group_2.pk, response.data[1].get('pk'))
        self.assertEqual(self.group_2.name, response.data[1].get('name'))
        self.assertEqual(self.group_2.manager_id, response.data[1].get('manager'))
        self.assertEqual(self.group_2.created_on, parse_datetime(response.data[1].get('created_on')))
        self.assertEqual(self.group_2.public, response.data[1].get('public'))
        self.assertEqual(str(self.group_2.public_key), response.data[1].get('public_key'))
        self.assertIsNone(response.data[1].get('invitation_key'))  # Not manager

    @tag('permission')
    def test_user_group_meter_list_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_group_meter_list_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestGroupMeterListPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.meter_1 = cls.create_smart_meter(cls.user)
        # meter 2 already in a group
        cls.meter_2 = cls.create_smart_meter(cls.user)
        cls.group_2 = cls.create_group_meter(cls.user, cls.meter_2)
        # meter 3 had a group but no active participation
        cls.meter_3 = cls.create_smart_meter(cls.user)
        cls.group_3 = cls.create_group_meter()
        participation_3 = cls.create_group_participation(cls.meter_3, cls.group_3)
        participation_3.leave()
        participation_3.save()
        # some other meter
        cls.meter_other = cls.create_smart_meter()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_group_meter_list_post_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'meter': self.meter_1.pk,
            'name': 'my group!!',
            'public': True
        }
        # when
        response = self.client.post(self.MeterUrls.user_group_meter_url(self.user.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(payload['name'], response.data.get('name'))
        self.assertEqual(self.user.pk, response.data.get('manager'))
        self.assertEqual(payload['public'], response.data.get('public'))
        self.assertIsNotNone(response.data.get('pk'))
        self.assertIsNotNone(response.data.get('created_on'))
        self.assertIsNotNone(response.data.get('public_key'))

    @tag('validation')
    def test_user_group_meter_list_post_as_user_fail_meter_already_active_in_group(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'meter': self.meter_2.pk,
            'name': 'my group!!',
            'public': True
        }
        # when
        response = self.client.post(self.MeterUrls.user_group_meter_url(self.user.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('meter'))

    @tag('validation')
    def test_user_group_meter_list_post_as_user_fail_meter_not_from_user(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'meter': self.meter_other.pk,
            'name': 'my group!!',
            'public': True
        }
        # when
        response = self.client.post(self.MeterUrls.user_group_meter_url(self.user.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('meter'))

    @tag('validation')
    def test_user_group_meter_list_post_meter_inactive_group_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'meter': self.meter_3.pk,
            'name': 'my group!!',
            'public': True
        }
        # when
        response = self.client.post(self.MeterUrls.user_group_meter_url(self.user.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(2, self.meter_3.group_participations.count())
        self.assertEqual(1, self.meter_3.group_participations.active().count())

    @tag('permission')
    def test_user_group_meter_list_post_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        payload = {
            'meter': self.meter_1.pk,
            'name': 'my group!!',
            'public': True
        }
        # when
        response = self.client.post(self.MeterUrls.user_group_meter_url(self.user.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_group_meter_list_post_as_visitor_fail_forbidden(self):
        # given
        payload = {
            'meter': self.meter_1.pk,
            'name': 'my group!!',
            'public': True
        }
        # when
        response = self.client.post(self.MeterUrls.user_group_meter_url(self.user.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestGroupMeterDetailGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        # meter 1 has group managed by user
        cls.meter_1 = cls.create_smart_meter(cls.user)
        cls.group_1 = cls.create_group_meter(cls.user, cls.meter_1)
        # meter 2 has group managed by another user
        cls.meter_2 = cls.create_smart_meter(cls.user)
        cls.group_2 = cls.create_group_meter()
        cls.create_group_participation(cls.meter_2, cls.group_2)
        # meter 3 had a group but no active participation
        cls.meter_3 = cls.create_smart_meter(cls.user)
        cls.group_3 = cls.create_group_meter()
        participation_3 = cls.create_group_participation(cls.meter_3, cls.group_3)
        participation_3.leave()
        participation_3.save()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_group_meter_detail_get_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.group_1.pk, response.data.get('pk'))
        self.assertEqual(self.group_1.name, response.data.get('name'))
        self.assertEqual(self.group_1.manager_id, response.data.get('manager'))
        self.assertEqual(self.group_1.created_on, parse_datetime(response.data.get('created_on')))
        self.assertEqual(self.group_1.public, response.data.get('public'))
        self.assertEqual(str(self.group_1.public_key), response.data.get('public_key'))
        self.assertEqual(str(self.group_1.invitation_key), response.data.get('invitation_key'))

        self.assertEqual(self.group_1.active_participants.count(), len(response.data.get('participants')))

    @tag('variation')
    def test_user_group_meter_detail_get_as_user_participant_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_2.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.group_2.pk, response.data.get('pk'))
        self.assertEqual(self.group_2.name, response.data.get('name'))
        self.assertEqual(self.group_2.manager_id, response.data.get('manager'))
        self.assertEqual(self.group_2.created_on, parse_datetime(response.data.get('created_on')))
        self.assertEqual(self.group_2.public, response.data.get('public'))
        self.assertEqual(str(self.group_2.public_key), response.data.get('public_key'))
        self.assertIsNone(response.data.get('invitation_key'))

        self.assertEqual(self.group_2.active_participants.count(), len(response.data.get('participants')))

    @tag('variation')
    def test_user_group_meter_detail_get_as_user_old_participant_fail_no_longer_active(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_3.pk))
        # then
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    @tag('permission')
    def test_user_group_meter_detail_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_group_meter_detail_get_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestGroupMeterDetailPatch(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        # meter 1 has group managed by user
        cls.meter_1 = cls.create_smart_meter(cls.user)
        cls.group_1 = cls.create_group_meter(cls.user, cls.meter_1)
        # meter 2 has group managed by another user
        cls.meter_2 = cls.create_smart_meter(cls.user)
        cls.group_2 = cls.create_group_meter()
        cls.create_group_participation(cls.meter_2, cls.group_2)
        # some other meter
        cls.meter_other = cls.create_smart_meter()

    def setUp(self):
        self.meter_1.refresh_from_db()  # refresh changes in tests
        self.client = APIClient()

    @tag('standard')
    def test_user_group_meter_detail_patch_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'name': 'new name!!!',
            'public': True,
            'public_key': 'our-meter',
            # read only fields should be ignored by serializer
            'pk': 'read only field',
            'created_on': 'read only field',
            'invitation_key': 'read only field',
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(payload['name'], response.data.get('name'))
        self.assertEqual(payload['public'], response.data.get('public'))
        self.assertEqual(self.group_1.pk, response.data.get('pk'))
        self.assertEqual(self.group_1.created_on, parse_datetime(response.data.get('created_on')))
        self.assertEqual(str(self.group_1.invitation_key), response.data.get('invitation_key'))
        self.assertEqual(self.group_1.manager.pk, response.data.get('manager'))

    @tag('validation')
    def test_user_group_meter_detail_patch_new_manager_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        other_participant = self.create_group_participation(self.create_smart_meter(), self.group_1)
        payload = {
            'manager': other_participant.meter.user_id,
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(other_participant.meter.user_id, response.data.get('manager'))

    @tag('validation')
    def test_user_group_meter_detail_patch_new_manager_as_user_manager_fail_old_participant(self):
        # given
        self.client.force_authenticate(self.user)
        other_participant = self.create_group_participation(self.create_smart_meter(), self.group_1)
        other_participant.leave()
        other_participant.save()
        payload = {
            'manager': other_participant.meter.user_id,
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('manager'))

    @tag('validation')
    def test_user_group_meter_detail_patch_new_manager_as_user_manager_fail_not_group_member(self):
        # given
        self.client.force_authenticate(self.user)
        some_user = self.create_user()
        payload = {
            'manager': some_user.pk,
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('manager'))

    @tag('validation')
    def test_user_group_meter_detail_patch_reset_invitation_key_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'new_invitation_key': True,
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(response.data.get('invitation_key'))
        self.assertNotEqual(str(self.group_1.invitation_key), response.data.get('invitation_key'))

    @tag('validation')
    def test_user_group_meter_detail_patch_reset_public_key_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'public_key': '',
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(response.data.get('public_key'))
        self.assertNotEqual(str(self.group_1.public_key), response.data.get('public_key'))

    @tag('validation')
    def test_user_group_meter_detail_patch_as_user_manager_fail_public_key_in_use(self):
        # given
        self.create_group_meter(public_key='a-name-in-use', public=True)  # create group meter with
        self.client.force_authenticate(self.user)
        payload = {
            'public_key': 'a-name-in-use',
        }
        # when
        response = self.client.patch(
            self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('public_key'))

    @tag('permission')
    def test_user_group_meter_detail_patch_as_participant_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.patch(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_2.pk), {})
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_group_meter_detail_patch_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.patch(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), {})
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_group_meter_detail_patch_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.patch(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk), {})
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestGroupMeterDetailDelete(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()

    def setUp(self):
        # group managed by user
        self.group_1 = self.create_group_meter(self.user)
        self.client = APIClient()

    @tag('standard')
    def test_user_group_meter_detail_delete_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.delete(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, GroupMeter.objects.managed_by(self.user.pk).count())

    @tag('permission')
    def test_user_group_meter_detail_delete_as_group_participant_fail_forbidden(self):
        # given
        user = self.create_user()
        self.create_group_participation(self.create_smart_meter(user), self.group_1)
        self.client.force_authenticate(user)
        # when
        response = self.client.delete(self.MeterUrls.user_group_meter_url(user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(1, GroupMeter.objects.managed_by(self.user.pk).count())

    @tag('permission')
    def test_user_group_meter_detail_delete_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.delete(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(1, GroupMeter.objects.managed_by(self.user.pk).count())

    @tag('permission')
    def test_user_group_meter_detail_delete_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.delete(self.MeterUrls.user_group_meter_url(self.user.pk, self.group_1.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(1, GroupMeter.objects.managed_by(self.user.pk).count())


@tag('api')
class TestGroupMeterDisplayGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        # meter 1 has group managed by user
        cls.meter_1 = cls.create_smart_meter(cls.user)
        cls.group_1 = cls.create_group_meter(cls.user, cls.meter_1)
        cls.create_group_participation(cls.create_smart_meter(), cls.group_1)
        cls.create_group_participation(cls.create_smart_meter(), cls.group_1)
        cls.create_group_participation(cls.create_smart_meter(), cls.group_1)
        cls.create_group_participation(cls.create_smart_meter(), cls.group_1)
        # meter 2 has group managed by another user
        cls.meter_2 = cls.create_smart_meter(cls.user)
        cls.group_2 = cls.create_group_meter()
        cls.create_group_participation(cls.meter_2, cls.group_2)
        # meter 3 had a group but no active participation
        cls.meter_3 = cls.create_smart_meter(cls.user)
        cls.group_3 = cls.create_group_meter()
        participation_3 = cls.create_group_participation(cls.meter_3, cls.group_3)
        participation_3.leave()
        participation_3.save()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_group_meter_display_get_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.group_1.pk, public=False))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.group_1.name, response.data.get('name'))
        self.assertEqual(self.group_1.public, response.data.get('public'))
        self.assertEqual(str(self.group_1.public_key), response.data.get('public_key'))

        # 5 participants, first one is user with meter 1
        self.assertEqual(5, len(response.data.get('participants')))
        participant = response.data.get('participants')[0]
        self.assertEqual(self.meter_1.group_participation.pk, participant.get('pk'))
        self.assertEqual(self.meter_1.group_participation.display_name, participant.get('display_name'))
        self.assertEqual(self.meter_1.group_participation.total_import, participant.get('total_import'))
        self.assertEqual(self.meter_1.group_participation.total_export, participant.get('total_export'))
        self.assertEqual(self.meter_1.group_participation.total_gas, participant.get('total_gas'))
        self.assertEqual(self.meter_1.group_participation.actual_power, participant.get('actual_power'))
        self.assertEqual(self.meter_1.group_participation.actual_gas, participant.get('actual_gas'))
        self.assertEqual(self.meter_1.group_participation.actual_solar, participant.get('actual_solar'))
        self.assertEqual(self.meter_1.residence_type, participant.get('residence').get('residence_type'))

    @tag('permission')
    def test_group_meter_display_get_as_user_participant_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.group_2.pk, public=False))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.group_2.name, response.data.get('name'))
        self.assertEqual(self.group_2.public, response.data.get('public'))
        self.assertEqual(str(self.group_2.public_key), response.data.get('public_key'))

        self.assertEqual(self.group_2.active_participants.count(), len(response.data.get('participants')))

    @tag('permission')
    def test_group_meter_display_get_as_user_old_participant_fail_no_longer_active(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.group_3.pk, public=False))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_group_meter_display_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.group_1.pk, public=False))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_group_meter_display_get_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.group_1.pk, public=False))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestPublicGroupMeterDisplayGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        some_user = cls.create_user()
        cls.some_meter = cls.create_smart_meter(some_user)
        cls.public_group = cls.create_group_meter(some_user, cls.some_meter, public=True)
        cls.create_group_participation(cls.create_smart_meter(), cls.public_group)
        cls.create_group_participation(cls.create_smart_meter(), cls.public_group)
        cls.create_group_participation(cls.create_smart_meter(), cls.public_group)
        cls.create_group_participation(cls.create_smart_meter(), cls.public_group)
        cls.private_group = cls.create_group_meter(public=False)

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_public_group_meter_display_get_public_group_as_visitor_success(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.public_group.public_key, public=True))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.public_group.name, response.data.get('name'))
        self.assertEqual(self.public_group.public, response.data.get('public'))
        self.assertEqual(str(self.public_group.public_key), response.data.get('public_key'))

        self.assertEqual(self.public_group.active_participants.count(), len(response.data.get('participants')))
        self.assertEqual(5, len(response.data.get('participants')))
        participant = response.data.get('participants')[0]
        self.assertEqual(self.some_meter.group_participation.pk, participant.get('pk'))
        self.assertEqual(self.some_meter.group_participation.display_name, participant.get('display_name'))
        self.assertEqual(self.some_meter.group_participation.total_import, participant.get('total_import'))
        self.assertEqual(self.some_meter.group_participation.total_export, participant.get('total_export'))
        self.assertEqual(self.some_meter.group_participation.total_gas, participant.get('total_gas'))
        self.assertEqual(self.some_meter.group_participation.actual_power, participant.get('actual_power'))
        self.assertEqual(self.some_meter.group_participation.actual_gas, participant.get('actual_gas'))
        self.assertEqual(self.some_meter.group_participation.actual_solar, participant.get('actual_solar'))

    @tag('permission')
    def test_public_group_meter_display_get_private_group_as_visitor_fail_not_found(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.meter_display_url(self.private_group.public_key, public=True))
        # then
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)


@tag('api')
class TestGroupMeterInviteInfoGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.group = cls.create_group_meter(allow_invite=True)
        cls.group_not_accepting = cls.create_group_meter(allow_invite=False)

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_group_meter_invite_info_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.group_meter_invite_info(self.group.invitation_key))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.group.name, response.data.get('name'))
        self.assertEqual(self.group.public, response.data.get('public'))
        self.assertEqual(self.group.manager.username, response.data.get('manager').get('username'))

    @tag('permission')
    def test_group_meter_invite_info_get_now_allowing_group_as_user_fail_not_found(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.group_meter_invite_info(self.group_not_accepting.invitation_key))
        # then
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    @tag('permission')
    def test_group_meter_invite_info_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.group_meter_invite_info(self.group.public_key))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestGroupLiveDataGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # A long time ago is 16 seconds
        long_time_ago = timezone.now() - timezone.timedelta(seconds=16)
        # 3 groups total
        # First group has 3 participants, all "last updated" within the past 15 seconds (`now` on create)
        cls.group_all_active = cls.create_group_meter()
        cls.create_group_participation(cls.create_smart_meter(), cls.group_all_active)
        cls.create_group_participation(cls.create_smart_meter(), cls.group_all_active)
        # Second group has 3 participants, but two of the participants were active a long time ago
        cls.group_one_active = cls.create_group_meter()
        goa_1 = cls.create_group_participation(cls.create_smart_meter(), cls.group_one_active)
        goa_2 = cls.create_group_participation(cls.create_smart_meter(), cls.group_one_active)
        SmartMeter.objects.filter(pk__in=[goa_1.meter_id, goa_2.meter_id]).update(last_update=long_time_ago)
        # Third group has 3 participants, but all of them were last active a long time ago
        cls.group_inactive = cls.create_group_meter()
        cls.create_group_participation(cls.create_smart_meter(), cls.group_inactive)
        cls.create_group_participation(cls.create_smart_meter(), cls.group_inactive)
        SmartMeter.objects.filter(groups=cls.group_inactive).update(last_update=long_time_ago)

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_group_live_data_get_as_nodejs_success(self):
        # given
        params = {
            'groups': ','.join([
                str(self.group_all_active.pk),
                str(self.group_one_active.pk),
                str(self.group_inactive.pk)
            ]),
            'token': settings.NODEJS_SECRET_TOKEN
        }
        # when
        response = self.client.get(self.MeterUrls.group_live_data_url(), params)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(self.group_all_active.pk, response.data[0].get('pk'))
        self.assertEqual(3, len(response.data[0].get('r')))
        self.assertEqual(self.group_one_active.pk, response.data[1].get('pk'))
        self.assertEqual(1, len(response.data[1].get('r')))

    @tag('variation')
    def test_group_live_data_get_all_meters_inactive_as_nodejs_success(self):
        # given
        long_time_ago = timezone.now() - timezone.timedelta(seconds=16)
        SmartMeter.objects.update(last_update=long_time_ago)
        params = {
            'groups': ','.join([
                str(self.group_all_active.pk),
                str(self.group_one_active.pk),
                str(self.group_inactive.pk)
            ]),
            'token': settings.NODEJS_SECRET_TOKEN
        }
        # when
        response = self.client.get(self.MeterUrls.group_live_data_url(), params)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(0, len(response.data))

    @tag('permission')
    def test_group_live_data_get_as_authenticated_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.group_live_data_url())
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_group_live_data_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.group_live_data_url())
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
