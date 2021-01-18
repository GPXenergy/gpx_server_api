from rest_framework.permissions import BasePermission


class RequestUserIsRelatedToUser(BasePermission):
    """
    Permission to check if the user is related to the
    user that made the request (through models)
    """

    def has_permission(self, request, view):
        """
        Return `True` if the request is related to user, `False`
        otherwise.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        assert hasattr(view, 'user_id'), (
                '%s requires property user_id' % (view.__class__.__name__,))
        return request.user.pk == getattr(view, 'user_id')
