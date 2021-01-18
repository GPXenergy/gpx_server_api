from unittest import TestCase

from django.urls import reverse

from users.models import User

user_increment = 0


class UserTestMixin(TestCase):
    """
    Mixin class adding easy user-related functions for testing
    """
    class UserUrls:
        @staticmethod
        def user_url(user_pk=None):
            """
            Users (/users/id?)
            :param user_pk: Id of user (optional)
            :return: url
            """
            if user_pk:
                return reverse('users:user_detail', kwargs={'pk': user_pk})
            return reverse('users:user_list')

        @staticmethod
        def auth_knox_login_url():
            """
            Auth token (/auth/login/)
            :return: url
            """
            return reverse('auth:knox_login')

        @staticmethod
        def auth_knox_verify_url():
            """
            Users (/auth/verify)
            :return: url
            """
            return reverse('auth:knox_verify')

        @staticmethod
        def auth_knox_logout_url():
            """
            Users (/auth/refresh)
            :return: url
            """
            return reverse('auth:knox_logout')

    @classmethod
    def setUpClass(cls):
        fixtures = ['test_user_data']
        cls.fixtures = fixtures + cls.fixtures if cls.fixtures else fixtures
        super().setUpClass()

    @classmethod
    def default_user_data(cls):
        global user_increment
        user_increment += 1
        name = 'user%s' % user_increment
        return {
            'username': name,
            'password': 'testpass123',
            'email': name + '@oanax.com',
        }

    @classmethod
    def create_user(cls, active=True, **user_data):
        user_data = {**cls.default_user_data(), **user_data}
        return User.objects.create_user(
            **user_data,
            is_active=active
        )
