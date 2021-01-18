from rest_framework.permissions import BasePermission


class MethodPermission(BasePermission):
    message = ''
    any_permission_property_name = 'ANY_permissions'
    method_permission_property_names = {
        'HEAD': 'HEAD_permissions',
        'GET': 'GET_permissions',
        'OPTIONS': 'GET_permissions',
        'POST': 'POST_permissions',
        'PUT': 'PUT_permissions',
        'PATCH': 'PUT_permissions',
        'DELETE': 'DELETE_permissions',
    }

    def get_method_permissions(self, view, method):
        """
        get list of permission objects for given view
        :param view: api view object
        :param method: request method
        :return: list of permission objects
        """
        # permissions for any method
        permissions = list(getattr(view, self.any_permission_property_name, []))
        method_property_name = self.method_permission_property_names.get(method.upper())
        # add method permissions
        permissions += list(getattr(view, method_property_name, []))
        return [permission() for permission in permissions]

    def has_permission(self, request, view):
        """
        """
        for permission in self.get_method_permissions(view, request.method):
            if not permission.has_permission(request, view):
                self.message = getattr(permission, 'message', None)
                return False
        return True

    def has_object_permission(self, request, view, obj):
        """
        """
        for permission in self.get_method_permissions(view, request.method):
            if not permission.has_object_permission(request, view, obj):
                self.message = getattr(permission, 'message', None)
                return False
        return True
