from django.contrib.auth import password_validation
from django.utils import timezone
from rest_framework import serializers

from smart_meter.models import SmartMeter
from users.models import User, ResetPasswordAction


class ResetPasswordRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetPasswordAction
        fields = ('username',)

    _user: User = None
    username = serializers.CharField(max_length=80, write_only=True)

    def validate_username(self, username):
        user = User.objects.filter(username=username).first()
        if not user:
            raise serializers.ValidationError('Geen gebruiker gevonden met deze gebruikersnaam')
        if not user.email:
            raise serializers.ValidationError('Dit account heeft geen email gekoppeld, neem direct contact op met GPX')
        self._user = user
        return username

    def create(self, validated_data):
        expire = timezone.now() + timezone.timedelta(days=2)
        return ResetPasswordAction.objects.create(user=self._user, expire=expire)


class ResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetPasswordAction
        fields = ('password',)

    password = serializers.CharField(max_length=128, write_only=True)

    def validate_password(self, password):
        password_validation.validate_password(password)
        return password

    def update(self, instance, validated_data):
        if instance.expired:
            instance.delete()
            raise serializers.ValidationError('Deze link is verlopen')
        password = validated_data.pop('password')
        user = instance.user
        user.set_password(password)
        user.save()
        instance.delete()
        return instance


class VerifyEmailSerializer(serializers.Serializer):
    class Meta:
        fields = ()


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
            'verified_email',
            'first_name',
            'last_name',
            'password',
            'new_password',
            'confirm_password',
            'default_meter',
            'api_key',
            'new_api_key',
        )
        read_only_fields = ('pk', 'username', 'api_key', 'verified_email')
        extra_kwargs = {
            'password': {'write_only': True},
            'new_api_key': {'write_only': True},
        }

    default_meter = serializers.PrimaryKeyRelatedField(queryset=[])
    new_api_key = serializers.BooleanField(default=False)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def get_fields(self):
        fields = super().get_fields()
        # Limit selection of default meter to those of the user
        fields['default_meter'].queryset = SmartMeter.objects.filter(user_id=self.context['view'].kwargs.get('pk'))
        return fields

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        if attrs.get('new_password') and attrs.get('confirm_password') != attrs.get('new_password'):
            raise serializers.ValidationError({'confirm_password': ['Wachtwoord komt niet overeen!']})
        return super().validate(attrs)

    def update(self, instance: User, validated_data):
        new_password = validated_data.pop('new_password', None)
        if new_password:
            old_password = validated_data.pop('password', None)
            if not instance.check_password(old_password):
                raise serializers.ValidationError({'password': ['Onjuist wachtwoord!']})
            # Set new raw password before saving
            instance.set_password(new_password)

        new_key = validated_data.pop('new_api_key', None)
        if new_key:
            # Set new api key
            instance.new_api_key()

        # TODO: implement verified emailing at some point
        # new_email = validated_data.pop('email', instance.email)
        # if instance.email != new_email and new_email != instance.verified_email:
        #     validated_data['']

        return super().update(instance, validated_data)
