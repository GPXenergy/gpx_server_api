from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient

from smart_meter.tests.mixin import MeterTestMixin
from users.models import User
from users.tests.mixin import UserTestMixin


@tag('api')
class TestUserListGet(UserTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_list_get_as_user_fail_method_not_allowed(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.UserUrls.user_url())
        # then
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)


@tag('api')
class TestUserListPost(UserTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_list_post_as_visitor_success(self):
        # given
        new_user_payload = {
            'username': 'jimjordan',
            'password': 'AverySecUre14Password99!',
            'first_name': 'Jim',
            'last_name': 'Jordan',
            'email': 'jimmy@oanax.com',
        }
        # when
        response = self.client.post(self.UserUrls.user_url(), new_user_payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(new_user_payload['username'], response.data.get('username'))
        self.assertEqual(new_user_payload['first_name'], response.data.get('first_name'))
        self.assertEqual(new_user_payload['last_name'], response.data.get('last_name'))
        self.assertEqual(new_user_payload['email'], response.data.get('email'))
        self.assertIsNone(response.data.get('password'))

    @tag('validation')
    def test_user_list_post_minimum_as_visitor_success(self):
        # given
        new_user_payload = {
            'username': 'jimjordan',
            'password': 'AverySecUre14Password99!'
        }
        # when
        response = self.client.post(self.UserUrls.user_url(), new_user_payload, format='json')
        # then
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(new_user_payload['username'], response.data.get('username'))
        self.assertEqual('', response.data.get('first_name'))
        self.assertEqual('', response.data.get('last_name'))
        self.assertEqual('', response.data.get('email'))
        self.assertIsNone(response.data.get('password'))

    @tag('validation')
    def test_user_list_post_as_visitor_fail_short_password(self):
        # given
        new_user_payload = {
            'username': 'jimjordan',
            'password': 'Sh0r!rt'  # less than 8
        }
        # when
        response = self.client.post(self.UserUrls.user_url(), new_user_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('password'))

    @tag('validation')
    def test_user_list_post_as_visitor_fail_common_password(self):
        # given
        new_user_payload = {
            'username': 'jimjordan',
            'password': '123qweasd'
        }
        # when
        response = self.client.post(self.UserUrls.user_url(), new_user_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('password'))

    @tag('validation')
    def test_user_list_post_as_visitor_fail_missing_username_password(self):
        # given
        new_user_payload = {}  # Empty payload
        # when
        response = self.client.post(self.UserUrls.user_url(), new_user_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        # Errors on the username / password fields
        self.assertIsNotNone(response.data.get('username'))
        self.assertIsNotNone(response.data.get('password'))

    @tag('permission')
    def test_user_list_post_as_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())  # Authenticate as some user
        new_user_payload = {
            'username': 'jimjordan',
            'password': 'AverySecUre14Password99!'
        }
        # when
        response = self.client.post(self.UserUrls.user_url(), new_user_payload, format='json')
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


@tag('api')
class TestUserDetailGet(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_detail_get_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        # when
        response = self.client.get(self.UserUrls.user_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.user.username, response.data.get('username'))
        self.assertEqual(self.user.first_name, response.data.get('first_name'))
        self.assertEqual(self.user.last_name, response.data.get('last_name'))
        self.assertEqual(self.user.email, response.data.get('email'))
        self.assertIsNone(response.data.get('password'))

    @tag('permission')
    def test_user_detail_get_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.get(self.UserUrls.user_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_detail_get_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.get(self.UserUrls.user_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestUserDetailPatch(MeterTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user(
            password='something123',
            first_name='Jimmy',
            last_name='Neutron',
            email='jim@oanax.com',
        )

    def setUp(self):
        self.user.refresh_from_db()  # refresh user object between tests
        self.client = APIClient()

    @tag('standard')
    def test_user_detail_patch_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        update_payload = {
            'username': 'This should not be changed',
            'password': 'mynewpass123',
            'first_name': 'John',
            'last_name': 'Johansonn',
            'email': 'john@oanax.com',
        }
        # when
        response = self.client.patch(self.UserUrls.user_url(self.user.pk), update_payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(update_payload['first_name'], response.data.get('first_name'))
        self.assertEqual(update_payload['last_name'], response.data.get('last_name'))
        self.assertEqual(update_payload['email'], response.data.get('email'))
        self.assertIsNone(response.data.get('password'))
        # username should not be changed
        self.assertNotEqual(update_payload['username'], response.data.get('username'))
        self.assertEqual(self.user.username, response.data.get('username'))
        # refresh user object to check the new hashed password
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(update_payload['password']))

    @tag('validation')
    def test_user_detail_patch_default_meter_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        meter1 = self.create_smart_meter(self.user)
        meter2 = self.create_smart_meter(self.user)
        meter3 = self.create_smart_meter(self.user)
        update_payload = {
            'default_meter': meter2.id,
        }
        # when
        response = self.client.patch(self.UserUrls.user_url(self.user.pk), update_payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(update_payload['default_meter'], response.data.get('default_meter'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.default_meter_id, response.data.get('default_meter'))

    @tag('validation')
    def test_user_detail_patch_default_meter_as_user_fail_invalid_meter(self):
        # given
        self.client.force_authenticate(self.user)
        meter_from_someone_else = self.create_smart_meter()
        update_payload = {
            'default_meter': meter_from_someone_else.id,
        }
        # when
        response = self.client.patch(self.UserUrls.user_url(self.user.pk), update_payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNotNone(response.data.get('default_meter'))

    @tag('validation')
    def test_user_detail_patch_new_api_key_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        update_payload = {
            'new_api_key': True,
        }
        # when
        response = self.client.patch(self.UserUrls.user_url(self.user.pk), update_payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotEqual(self.user.api_key, response.data.get('api_key'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.api_key, response.data.get('api_key'))

    @tag('permission')
    def test_user_detail_patch_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.patch(self.UserUrls.user_url(self.user.pk), {})
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_detail_patch_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.patch(self.UserUrls.user_url(self.user.pk), {})
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)


@tag('api')
class TestUserDetailDelete(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user(
            password='something123',
            first_name='Jimmy',
            last_name='Neutron',
            email='jim@oanax.com',
        )

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_user_detail_delete_as_user_success(self):
        # given
        self.client.force_authenticate(self.user)
        pre_user_count = User.objects.count()
        # when
        response = self.client.delete(self.UserUrls.user_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(pre_user_count - 1, User.objects.count())

    @tag('permission')
    def test_user_detail_delete_as_other_user_fail_forbidden(self):
        # given
        self.client.force_authenticate(self.create_user())
        # when
        response = self.client.delete(self.UserUrls.user_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @tag('permission')
    def test_user_detail_delete_as_visitor_fail_unauthorized(self):
        # given
        # when
        response = self.client.delete(self.UserUrls.user_url(self.user.pk))
        # then
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
