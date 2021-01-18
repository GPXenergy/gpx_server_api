from django.urls import path
from knox import views as knox_views

from users.views import UserLoginView, AuthUserView

app_name = 'auth'

urlpatterns = [
    path('me/', AuthUserView.as_view(), name='knox_login'),
    path('login/', UserLoginView.as_view(), name='knox_login'),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]
