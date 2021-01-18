from rest_framework import serializers

from users.models import User


class SimpleUserSerializer(serializers.ModelSerializer):
    """
    Simple user serializer to use in nested serializer
    """

    class Meta:
        model = User
        fields = ('pk', 'username',)
