from django.urls import path, include

from users.views import UserListView, UserDetailView

app_name = 'users'

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('<int:user_pk>/meters/', include('smart_meter.urls.user_meter_urls')),
]
