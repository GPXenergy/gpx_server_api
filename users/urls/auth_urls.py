from django.urls import path
from knox import views as knox_views

from users.views import UserLoginView, AuthUserView, ResetPasswordRequestView, ResetPasswordView, VerifyEmailView

app_name = 'auth'

urlpatterns = [
    path('me/', AuthUserView.as_view(), name='knox_login'),
    path('login/', UserLoginView.as_view(), name='knox_login'),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    path('reset-password/', ResetPasswordRequestView.as_view(), name='reset_password_request'),
    path('reset-password/<uuid:uuid>/', ResetPasswordView.as_view(), name='reset_password'),
    # path('verify-email/<uuid:uuid>/', VerifyEmailView.as_view(), name='verify_email'),

]
