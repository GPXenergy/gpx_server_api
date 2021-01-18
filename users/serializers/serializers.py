from django.contrib.auth import password_validation
from rest_framework import serializers

from smart_meter.models import SmartMeter
from users.models import User


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer used for creating a user, listing users is not available at this time
    """

    class Meta:
        model = User
        fields = (
            'pk',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('pk',)
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_password(self, password):
        password_validation.validate_password(password)
        return password

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    """
    User detail serializer to retrieve and update a user instance.
    """

    class Meta:
        model = User
        fields = (
            'pk',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'default_meter',
            'api_key',
            'new_api_key',
        )
        read_only_fields = ('pk', 'username', 'api_key')
        extra_kwargs = {
            'password': {'write_only': True},
            'new_api_key': {'write_only': True},
        }

    default_meter = serializers.PrimaryKeyRelatedField(queryset=[])
    new_api_key = serializers.BooleanField(default=False)

    def get_fields(self):
        fields = super().get_fields()
        # Limit selection of default meter to those of the user
        fields['default_meter'].queryset = SmartMeter.objects.filter(user_id=self.context['view'].kwargs.get('pk'))
        return fields

    def update(self, instance: User, validated_data):
        password = validated_data.pop('password', None)
        if password:
            # Set new raw password before saving
            instance.set_password(password)

        new_key = validated_data.pop('new_api_key', None)
        if new_key:
            # Set new api key
            instance.new_api_key()

        return super().update(instance, validated_data)
