from django.contrib.auth.models import UserManager as BaseUserManager


class UserManager(BaseUserManager):
    """
    Manager class for the user
    """

    def active_users(self):
        return self.filter(is_active=True)

    def create(self, **kwargs):
        """
        Makes sure the default create call for the user model call the create_user method
        :param kwargs: user data
        :rtype: users.models.User
        """
        return self.create_user(**kwargs)
