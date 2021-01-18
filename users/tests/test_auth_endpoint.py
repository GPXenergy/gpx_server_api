from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient

from users.tests.mixin import UserTestMixin


@tag('api')
class TestAuthKnoxLogin(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user(
            username='jimmy',
            password='123qweasd',
        )
        cls.inactive_user = cls.create_user(
            active=False,
            username='fred',
            password='pass123',
        )

    def setUp(self):
        self.client = APIClient()

    @tag('standard')
    def test_auth_knox_login_post_success(self):
        # given
        payload = {
            'username': 'jimmy',
            'password': '123qweasd',
        }
        # when
        response = self.client.post(self.UserUrls.auth_knox_login_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(response.data.get('token'))
        self.assertEqual(self.user.pk, response.data.get('user').get('pk'))
        self.assertEqual(self.user.username, response.data.get('user').get('username'))
        self.assertEqual(self.user.email, response.data.get('user').get('email'))
        self.assertEqual(self.user.first_name, response.data.get('user').get('first_name'))
        self.assertEqual(self.user.last_name, response.data.get('user').get('last_name'))
        self.assertEqual(self.user.default_meter, response.data.get('user').get('default_meter'))
        self.assertEqual(self.user.api_key, response.data.get('user').get('api_key'))

    @tag('validation')
    def test_auth_knox_login_post_fail_inactive_account(self):
        # given
        payload = {
            'username': 'fred',
            'password': 'pass123',
        }
        # when
        response = self.client.post(self.UserUrls.auth_knox_login_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('validation')
    def test_auth_knox_login_post_fail_invalid_password(self):
        # given
        payload = {
            'username': 'jimmy',
            'password': '123123123',
        }
        # when
        response = self.client.post(self.UserUrls.auth_knox_login_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @tag('validation')
    def test_auth_knox_login_post_fail_invalid_username(self):
        # given
        payload = {
            'username': 'johnny',
            'password': '123qweasd',
        }
        # when
        response = self.client.post(self.UserUrls.auth_knox_login_url(), payload, format='json')
        # then
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
