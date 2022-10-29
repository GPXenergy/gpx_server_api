from django.contrib.auth import login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic.base import View
from knox.views import LoginView as KnoxLoginView
from rest_condition import Not
from rest_framework import permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView, \
    UpdateAPIView

from users.models import User, ResetPasswordAction
from users.permissions import RequestUserIsRelatedToUser
from users.serializers import UserListSerializer, UserDetailSerializer, ResetPasswordRequestSerializer, \
    ResetPasswordSerializer, VerifyEmailSerializer


class SubUserView(View):
    """
    Mixin for API views that are under the user urls, like /users/x/meters/
    """

    @property
    def user_id(self):
        return self.kwargs.get('user_pk')


class AuthUserView(RetrieveAPIView):
    GET_permissions = [permissions.IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user


class UserLoginView(KnoxLoginView):
    """
    User login view, post username/password,  authenticates and returns a token
    """
    permission_classes = []

    def get_token_ttl(self):
        """
        If `remember` is part of the request, the token will expire after 60 days, else it will expire in 10 hours
        :return: duration for the token to live
        """
        return timezone.timedelta(days=60) if self.request.data.get('remember', False) else timezone.timedelta(hours=10)

    def post(self, request, **kwargs):
        """
        extends post method to add custom login implementation, to be used as 
        from https://james1345.github.io/django-rest-knox/auth/
        :return:
        """
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super().post(request, **kwargs)


class UserListView(CreateAPIView):
    serializer_class = UserListSerializer
    POST_permissions = [Not(permissions.IsAuthenticated)]


class UserDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserDetailSerializer
    GET_permissions = [RequestUserIsRelatedToUser]
    PUT_permissions = GET_permissions
    DELETE_permissions = GET_permissions

    @property
    def user_id(self):
        return self.kwargs.get('pk')

    def get_queryset(self):
        return User.objects.active_users()

    def perform_destroy(self, instance: User):
        group = instance.manager_groups.first()
        if group:
            raise ValidationError(
                'Kan account "%s" niet verwijderen, je bent momenteel manager van de groep "%s". Draag de groep eerst '
                'over of verwijder de groep en probeer het daarna nog eens.' % (instance.username, group.name)
            )
        super().perform_destroy(instance)


class ResetPasswordRequestView(CreateAPIView):
    serializer_class = ResetPasswordRequestSerializer

    def perform_create(self, serializer):
        reset_password: ResetPasswordAction = serializer.save()

        context = {
            'username': reset_password.user.username,
            'uuid': reset_password.uuid,
        }

        text_content = render_to_string('emails/password_reset.txt', context, request=self.request)
        html_content = render_to_string('emails/password_reset.html', context, request=self.request)

        print(text_content, html_content)
        send_mail(
            subject='Nieuw wachtwoord instellen',
            message=text_content,
            html_message=html_content,
            from_email='GPX Dashboard <dashboard@gpx.nl>',
            recipient_list=[reset_password.user.email],
        )


class ResetPasswordView(RetrieveUpdateAPIView):
    serializer_class = ResetPasswordSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        return ResetPasswordAction.objects.filter(expire__gt=timezone.now())


class VerifyEmailView(RetrieveUpdateAPIView):
    serializer_class = VerifyEmailSerializer

    def get_object(self):
        instance = super().get_object()

        user = instance.user
        user.verified_email = instance.email
        user.save()
        return instance


