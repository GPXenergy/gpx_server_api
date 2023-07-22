from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from smart_meter.models import SmartMeter, GroupMeter, GroupParticipant


class UserOwnerOfMeter(BasePermission):
    """
    Permission to check if the meter is related to the user that made the request (through models)
    """

    def has_permission(self, request, view):
        """
        Return `True` if the request user is owner of given meter, `False`
        otherwise.
        """
        assert hasattr(view, 'user_id'), (
                '%s requires property user_id' % (view.__class__.__name__,))
        assert hasattr(view, 'meter_id'), (
                '%s requires property meter_id' % (view.__class__.__name__,))
        return SmartMeter.objects.filter(user_id=getattr(view, 'user_id'), id=getattr(view, 'meter_id')).exists()


class UserManagerOfGroupMeter(BasePermission):
    """
    Permission to check if the user is manager of the group meter
    """

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if the request is related to user, `False`
        otherwise.
        """
        assert hasattr(view, 'user_id'), (
                '%s requires property user_id' % (view.__class__.__name__,))
        return obj.manager_id == getattr(view, 'user_id')


class RequestUserIsPartOfGroupMeter(BasePermission):
    """
    Permission to check if the user is related to the
    user that made the request (through models)
    """

    def has_permission(self, request, view):
        """
        Return `True` if the request user is part of the group meter, `False`
        otherwise.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        assert hasattr(view, 'group_id'), (
                '%s requires property group_id' % (view.__class__.__name__,))
        group_id = getattr(view, 'group_id')
        return GroupParticipant.objects.filter(
            meter__user_id=request.user.pk, left_on__isnull=True, group_id=group_id
        ).exists()


class RequestUserIsManagerOfGroupMeter(BasePermission):
    """
    Permission to check if the user is related to the
    user that made the request (through models)
    """

    def has_permission(self, request, view):
        """
        Return `True` if the request user is manager of the group meter, `False`
        otherwise.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        assert hasattr(view, 'group_id'), (
                '%s requires property group_id' % (view.__class__.__name__,))
        group_id = getattr(view, 'group_id')
        return GroupMeter.objects.filter(manager_id=request.user.pk, id=group_id).exists()


class RequestFromNodejs(BasePermission):
    """
    Permission to check if the user is related to the
    user that made the request (through models)
    """

    def has_permission(self, request: Request, view):
        """
        Return `True` if the request is made by our nodejs, `False` otherwise.
        """
        token = request.query_params.get('token')
        return token == settings.NODEJS_SECRET_TOKEN
