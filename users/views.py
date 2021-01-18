from django.contrib.auth import login
from django.utils import timezone
from django.views.generic.base import View
from knox.views import LoginView as KnoxLoginView
from rest_condition import Not
from rest_framework import permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.generics import CreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView

from users.models import User
from users.permissions import RequestUserIsRelatedToUser
from users.serializers import UserListSerializer, UserDetailSerializer


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
