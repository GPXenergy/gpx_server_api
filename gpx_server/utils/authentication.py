from rest_framework.authentication import TokenAuthentication

from users.models import User


class ApiKeyAuthentication(TokenAuthentication):
    def authenticate_credentials(self, token):
        # Check the token and return a user.
        try:
            user = User.objects.get(api_key=token)
            return user, token
        except User.DoesNotExist:
            return None, token
