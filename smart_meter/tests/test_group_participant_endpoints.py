from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient

from smart_meter.tests.mixin import MeterTestMixin


@tag('api')
class TestMeterParticipationListGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter1 = cls.create_smart_meter(cls.user)
        group1 = cls.create_group_meter(cls.user, cls.meter1)
        cls.participant1 = group1.participants.first()
        cls.meter2 = cls.create_smart_meter(cls.user)
        group2 = cls.create_group_meter()
        cls.participant2 = cls.create_group_participation(cls.meter2, group2)
        cls.meter3 = cls.create_smart_meter(cls.user)
        group3 = cls.create_group_meter()
        cls.participant3 = cls.create_group_participation(cls.meter3, group3)
        cls.participant3.leave()
        cls.participant3.save()
        cls.meter_no_group = cls.create_smart_meter(cls.user)

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_participation_list_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.MeterUrls.meter_group_participation_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, len(response.data))

    @tag('filter')
    def test_user_meter_participation_list_get_filter_active_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filters = {
            'active': True
        }
        # when
        response = self.client.get(self.MeterUrls.meter_group_participation_url(self.user.pk), filters)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(self.meter1.pk, response.data[0].get('meter').get('pk'))
        self.assertEqual(self.meter2.pk, response.data[1].get('meter').get('pk'))

    @tag('filter')
    def test_user_meter_participation_list_get_filter_inactive_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        filters = {
            'active': False
        }
        # when
        response = self.client.get(self.MeterUrls.meter_group_participation_url(self.user.pk), filters)
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(self.meter3.pk, response.data[0].get('meter').get('pk'))

    @tag('permission')
    def test_user_meter_participation_list_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.MeterUrls.meter_group_participation_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_participation_list_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.MeterUrls.meter_group_participation_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestMeterParticipationListPost(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user)
        cls.meter_with_active_participation = cls.create_smart_meter(cls.user)
        cls.create_group_meter(cls.user, cls.meter_with_active_participation)
        cls.meter_without_active_participation = cls.create_smart_meter(cls.user)
        inactive_p = cls.create_group_participation(cls.meter_without_active_participation, cls.create_group_meter())
        inactive_p.leave()
        inactive_p.save()
        cls.group_to_join = cls.create_group_meter()
        cls.group_not_accepting = cls.create_group_meter(allow_invite=False)

    def setUp(self):
        self.client = APIClient()
        self.default_payload = {
            'meter': self.meter.pk,
            'group': self.group_to_join.pk,
            'invitation_key': self.group_to_join.invitation_key,
            'display_name': 'some name'
        }

    @tag('standard')
    def test_user_meter_participation_list_post_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    @tag('validation')
    def test_user_meter_participation_list_post_meter_without_active_participation_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        self.default_payload['meter'] = self.meter_without_active_participation.pk
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    @tag('validation')
    def test_user_meter_participation_list_post_meter_with_active_participation_as_user_fail_meter_in_group(self):
        # given
        self.client.force_authenticate(self.user)
        self.default_payload['meter'] = self.meter_with_active_participation.pk
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data['meter'])

    @tag('validation')
    def test_user_meter_participation_list_post_invalid_meter_invitation_combination_as_user_fail_invalid_invite(self):
        # given
        self.client.force_authenticate(self.user)
        self.default_payload['invitation_key'] = 'some invalid key'
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data['invitation_key'])

    @tag('validation')
    def test_user_meter_participation_list_post_as_user_fail_group_not_accepting(self):
        # given
        self.client.force_authenticate(self.user)
        self.default_payload['group'] = self.group_not_accepting.pk
        self.default_payload['invitation_key'] = self.group_not_accepting.invitation_key
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data['invitation_key'])

    @tag('permission')
    def test_user_meter_participation_list_post_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_participation_list_post_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.post(
            self.MeterUrls.meter_group_participation_url(self.user.pk), self.default_payload, format='json')
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestMeterParticipationDetailGet(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user)
        cls.group = cls.create_group_meter()
        cls.participant = cls.create_group_participation(cls.meter, cls.group)

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_meter_participation_detail_get_as_user_manager_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.participant.pk, response.data.get('pk'))
        self.assertEqual(self.meter.pk, response.data.get('meter').get('pk'))
        self.assertEqual(self.group.pk, response.data.get('group').get('pk'))

    @tag('permission')
    def test_user_meter_participation_detail_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_participation_detail_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestMeterParticipationDetailPatch(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user)
        cls.group = cls.create_group_meter()

    def setUp(self):
        self.client = APIClient()
        self.participant = self.create_group_participation(self.meter, self.group)

    @tag('standard')
    def test_user_meter_participation_detail_patch_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'display_name': 'my new display name!!!',
            'pk': 'field is ignored on update',
            'meter': 'field is ignored on update',
            'group': 'field is ignored on update',
        }
        # when
        response = self.client.patch(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(payload['display_name'], response.data.get('display_name'))
        self.assertEqual(self.participant.pk, response.data.get('pk'))
        self.assertEqual(self.meter.pk, response.data.get('meter').get('pk'))
        self.assertEqual(self.group.pk, response.data.get('group').get('pk'))

    @tag('validation')
    def test_user_meter_participation_detail_patch_leave_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        payload = {
            'active': True,
        }
        # when
        response = self.client.patch(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(response.data.get('active'))

    @tag('validation')
    def test_user_meter_participation_detail_patch_as_user_fail_participant_inactive(self):
        # given
        self.client.force_authenticate(self.user)
        self.participant.leave()
        self.participant.save()
        payload = {
            'display_name': 'my new display name!!!',
        }
        # when
        response = self.client.patch(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('permission')
    def test_user_meter_participation_detail_patch_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.patch(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk), format='json')
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_meter_participation_detail_patch_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.patch(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk), format='json')
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestMeterParticipationDetailDelete(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.user = cls.create_user()
        cls.meter = cls.create_smart_meter(cls.user)
        cls.group = cls.create_group_meter()

    def setUp(self):
        self.client = APIClient()
        self.participant = self.create_group_participation(self.meter, self.group)

    @tag('standard')
    def test_user_meter_participation_detail_delete_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.delete(
            self.MeterUrls.meter_group_participation_url(self.user.pk, self.participant.pk), format='json')
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)
