"""gpx_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.settings import api_settings
from rest_framework.urlpatterns import format_suffix_patterns

from gpx_server.stats_view import StatisticsView


def _root(request):
    return HttpResponse("<html><body>GPX API v1.0</body></html>")


urlpatterns = [
    path('api/admin/', admin.site.urls),
]

api_routing = [
    path('api/', _root),
    path('api/stats/', StatisticsView.as_view()),
    path('api/auth/', include('users.urls.auth_urls')),
    path('api/users/', include('users.urls.user_urls')),
    path('api/meters/', include('smart_meter.urls.meter_urls')),
]

if any([isinstance(renderer(), BrowsableAPIRenderer) for renderer in api_settings.DEFAULT_RENDERER_CLASSES]):
    api_routing = format_suffix_patterns(api_routing)

urlpatterns += api_routing
