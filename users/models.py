import os
from binascii import hexlify

from django.contrib.auth.models import AbstractUser
from django.db import models

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

    def new_api_key(self):
        self.api_key = api_key_gen()
