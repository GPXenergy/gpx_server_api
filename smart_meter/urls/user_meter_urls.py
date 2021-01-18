from django.urls import path, include

from smart_meter.views import UserMeterListView, UserMeterDetailView, GroupMeterDetailView, \
    GroupMeterListView, MeterGroupParticipationDetailView, MeterParticipationListView, \
    PowerMeasurementListView, GasMeasurementListView, SolarMeasurementListView

# urls under /users/<user_pk>/meters/...
urlpatterns = [
    path('', UserMeterListView.as_view(), name='user_meter_list'),
    path('<int:pk>/', UserMeterDetailView.as_view(), name='user_meter_detail'),
    path('<int:meter_pk>/', include([
        path('power/', PowerMeasurementListView.as_view(), name='power_measurement_list'),
        path('gas/', GasMeasurementListView.as_view(), name='gas_measurement_list'),
        path('solar/', SolarMeasurementListView.as_view(), name='solar_measurement_list'),
    ])),
    path('groups/', GroupMeterListView.as_view(), name='group_meter_list'),
    path('groups/<int:pk>/', GroupMeterDetailView.as_view(), name='group_meter_detail'),
    path('participation/', MeterParticipationListView.as_view(), name='meter_participation_list'),
    path('participation/<int:pk>/', MeterGroupParticipationDetailView.as_view(), name='meter_participation_detail'),
]
