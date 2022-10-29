from django.urls import path

from smart_meter.views import NewMeasurementView, GroupDisplayView, PublicGroupDisplayView, NewMeasurementTestView, \
    GroupMeterInviteInfoView, GroupLiveDataView, GroupParticipantDetailView, GroupParticipantListView

app_name = 'smart_meter'

urlpatterns = [
    # urls used by GPX connector
    path('measurement/', NewMeasurementView.as_view(), name='new_measurement'),
    path('measurement/test/', NewMeasurementTestView.as_view(), name='new_measurement_test'),

    # urls used by frontend
    path('groups/<int:pk>/', GroupDisplayView.as_view(), name='group_meter_display'),
    path('groups/public/<slug:public_key>/', PublicGroupDisplayView.as_view(), name='public_group_meter_display'),
    path('groups/invite/<uuid:invitation_key>/', GroupMeterInviteInfoView.as_view(), name='group_meter_invite_info'),

    # For participant management TODO: activate these endpoints for history view
    path('groups/<int:group_pk>/participants/', GroupParticipantListView.as_view(), name='group_participant_list'),
    path('groups/<int:group_pk>/participants/<int:pk>/', GroupParticipantDetailView.as_view(), name='group_participant_detail'),

    # urls used by nodejs
    path('groups/live-data/', GroupLiveDataView.as_view(), name='group_live_data'),
]
