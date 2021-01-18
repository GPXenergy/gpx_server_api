from django.test import TestCase, tag

from users.models import User
from users.tests.mixin import UserTestMixin


@tag('model')
class TestUserModel(UserTestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    @tag('standard')
    def test_user_manager_create_success(self):
        # given
        user_data = {
            'username': 'jimmy',
            'password': '123qweasd',
        }
        # when
        user = User.objects.create(**user_data)
        # then
        # Should have password hashed
        self.assertNotEqual(user_data['password'], user.password)
        self.assertTrue(user.check_password(user_data['password']))
