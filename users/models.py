import os
import uuid
from binascii import hexlify

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from users.managers import UserManager


def api_key_gen():
    """
    Generates 16 character random hex to be used as key
    :return: a new api key for the user
    """
    return hexlify(os.urandom(8)).decode('ascii')


class User(AbstractUser):
    """
    User model, extends from the default django user and adds an api key
    """
    objects = UserManager()

    api_key = models.CharField(unique=True, max_length=20, default=api_key_gen)
    default_meter = models.ForeignKey('smart_meter.SmartMeter', on_delete=models.SET_NULL, null=True,
                                      related_name='default')
    verified_email = models.EmailField(null=True, unique=True)

    def new_api_key(self):
        self.api_key = api_key_gen()


class UserEmailAction(models.Model):
    class Meta:
        abstract = True

    email = models.EmailField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expire = models.DateTimeField()
    uuid = models.UUIDField(default=uuid.uuid4)

    @property
    def expired(self):
        return timezone.now() > self.expire


class VerifyEmailAction(UserEmailAction):
    ...


class ResetPasswordAction(UserEmailAction):
    ...

