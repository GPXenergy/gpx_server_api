from django.contrib.auth.models import UserManager as BaseUserManager


class UserManager(BaseUserManager):
    """
    Manager class for the user
    """

    def active_users(self):
        return self.filter(is_active=True)

    def active_in_group(self, group_id):
        return self.filter(
            meters__group_participations__group=group_id,
            meters__group_participations__left_on__isnull=True,
        ).distinct()

    def create(self, **kwargs):
        """
        Makes sure the default create call for the user model call the create_user method
        :param kwargs: user data
        :rtype: users.models.User
        """
        return self.create_user(**kwargs)
