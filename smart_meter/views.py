from django.http import HttpResponse
from django.views.generic.base import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions
from rest_framework.decorators import authentication_classes
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateAPIView, ListCreateAPIView, \
    RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.views import APIView

from gpx_server.utils.authentication import ApiKeyAuthentication
from smart_meter.filters import GroupParticipantFilter, MeasurementFilter, MeterMeasurementFilter
from smart_meter.models import SmartMeter, GroupParticipant, GroupMeter, SolarMeasurement, GasMeasurement, \
    PowerMeasurement
from smart_meter.permissions import UserOwnerOfMeter, UserManagerOfGroupMeter, RequestUserIsRelatedToGroupMeter, \
    RequestFromNodejs
from smart_meter.serializers.serializers import MeterDetailSerializer, MeterListSerializer, GroupMeterDetailSerializer, \
    GroupMeterListSerializer, GroupParticipationDetailSerializer, GroupParticipationListSerializer, \
    GasMeasurementSerializer, SolarMeasurementSerializer, PowerMeasurementSerializer, NewMeasurementSerializer, \
    GroupMeterViewSerializer, GroupMeterInviteInfoSerializer, GroupLiveDataSerializer, NewMeasurementTestSerializer, \
    MeterMeasurementsDetailSerializer
from users.permissions import RequestUserIsRelatedToUser
from users.views import SubUserView


class SubMeterView(View):
    """
    Mixin for API views that are under the meter urls, like /users/x/meters/x/group/...
    """

    @property
    def meter_id(self):
        return self.kwargs.get('meter_pk')


class UserMeterListView(SubUserView, ListAPIView):
    """
    List of meters for a user. Required user to be logged in and will only retrieve meters for this user
    Available request methods: GET
    `GET`:
    """
    GET_permissions = [RequestUserIsRelatedToUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['pk', 'name', 'power_timestamp']
    ordering = ['name']
    filter_class = None  # TODO
    serializer_class = MeterListSerializer

    def get_queryset(self):
        return SmartMeter.objects.user_meters(self.user_id)


class UserMeterDetailView(SubUserView, RetrieveUpdateDestroyAPIView):
    """
    Detail of a meter, can retrieve or update. Requires meter to be related to the user
    Available request methods: GET, PUT, DELETE
    `GET`:
    `PUT`:
    `DELETE`:
    """
    GET_permissions = [RequestUserIsRelatedToUser]
    PUT_permissions = GET_permissions
    DELETE_permissions = GET_permissions
    filter_backends = [DjangoFilterBackend]
    filter_class = MeterMeasurementFilter

    def get_serializer_class(self):
        if self.request.query_params.get('measurements'):
            return MeterMeasurementsDetailSerializer
        return MeterDetailSerializer

    def get_queryset(self):
        return SmartMeter.objects.user_meters(self.user_id)


class PowerMeasurementListView(SubUserView, SubMeterView, ListAPIView):
    """
    List of power measurements for a meter (from user)
    Available request methods: GET
    `GET`:
    """
    GET_permissions = [RequestUserIsRelatedToUser, UserOwnerOfMeter]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['timestamp']
    ordering = ['timestamp']
    filter_class = MeasurementFilter
    serializer_class = PowerMeasurementSerializer

    def get_queryset(self):
        return PowerMeasurement.objects.filter(meter_id=self.meter_id)


class GasMeasurementListView(SubUserView, SubMeterView, ListAPIView):
    """
    List of gas measurements for a meter (from user)
    Available request methods: GET
    `GET`:
    """
    GET_permissions = [RequestUserIsRelatedToUser, UserOwnerOfMeter]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['timestamp']
    ordering = ['timestamp']
    filter_class = MeasurementFilter
    serializer_class = GasMeasurementSerializer

    def get_queryset(self):
        return GasMeasurement.objects.filter(meter_id=self.meter_id)


class SolarMeasurementListView(SubUserView, SubMeterView, ListAPIView):
    """
    List of solar measurements for a meter (from user)
    Available request methods: GET
    `GET`:
    """
    GET_permissions = [RequestUserIsRelatedToUser, UserOwnerOfMeter]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['timestamp']
    ordering = ['timestamp']
    filter_class = MeasurementFilter
    serializer_class = SolarMeasurementSerializer

    def get_queryset(self):
        return SolarMeasurement.objects.filter(meter_id=self.meter_id)


class GroupMeterListView(SubUserView, ListCreateAPIView):
    """
    List of group meters for a user (manager).
    Available request methods: GET, POST
    `GET`:
    `POST`:
    """
    GET_permissions = [RequestUserIsRelatedToUser]
    POST_permissions = GET_permissions
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['pk', 'name']
    ordering = ['pk']
    filter_class = None  # TODO
    serializer_class = GroupMeterListSerializer

    def get_queryset(self):
        return GroupMeter.objects.by_user(self.user_id)

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)


class GroupMeterDetailView(SubUserView, RetrieveUpdateDestroyAPIView):
    """
    Detail of a group meter, can retrieve or update. Requires meter to be related to the user
    Available request methods: GET, PUT, DELETE
    `GET`:
    `PUT`:
    `DELETE`:
    """
    GET_permissions = [RequestUserIsRelatedToUser]
    PUT_permissions = [RequestUserIsRelatedToUser, UserManagerOfGroupMeter]
    DELETE_permissions = PUT_permissions
    serializer_class = GroupMeterDetailSerializer

    def get_queryset(self):
        return GroupMeter.objects.by_user(self.user_id)


class MeterParticipationListView(SubUserView, ListCreateAPIView):
    """
    List of all participation for a meter.
    Available request methods: GET, POST
    `GET`:
    `POST`:
    """
    GET_permissions = [RequestUserIsRelatedToUser]
    POST_permissions = GET_permissions
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['group__name']
    ordering_fields = ['pk']
    ordering = ['pk']
    filter_class = GroupParticipantFilter
    serializer_class = GroupParticipationListSerializer

    def get_queryset(self):
        return GroupParticipant.objects.filter(meter__user_id=self.user_id)


class MeterGroupParticipationDetailView(SubUserView, RetrieveUpdateAPIView):
    """
    Detail of participation for a meter.
    Available request methods: GET, PUT
    `GET`:
    `PUT`:
    """
    serializer_class = GroupParticipationDetailSerializer
    GET_permissions = [RequestUserIsRelatedToUser]
    PUT_permissions = GET_permissions

    def get_queryset(self):
        return GroupParticipant.objects.filter(meter__user_id=self.user_id)


class GroupMeterInviteInfoView(RetrieveAPIView):
    """
    View to get group meter information when joining a group, based on the invitation key of a group.
    Available request methods: GET
    `GET`:
    Returns basic group meter info to show user what group he is joining
    """
    serializer_class = GroupMeterInviteInfoSerializer
    GET_permissions = [permissions.IsAuthenticated]
    lookup_field = 'invitation_key'

    def get_queryset(self):
        return GroupMeter.objects.filter(allow_invite=True)


class GroupDisplayView(SubUserView, RetrieveAPIView):
    """
    View to get data from a group meter for a user who is part of the group. View is used to generate
    the group meter dashboard. This returns the initial data
    Available request methods: GET
    `GET`:
    Returns group meter info and participant info
    """
    serializer_class = GroupMeterViewSerializer
    GET_permissions = [RequestUserIsRelatedToGroupMeter]

    def get_queryset(self):
        return GroupMeter.objects.all()


class PublicGroupDisplayView(RetrieveAPIView):
    """
    View to get data from a public group meter, based on the public key. View is used to generate the
    public group meter. This returns the initial data
    Available request methods: GET
    `GET`:
    Returns group meter info and participant info
    """
    serializer_class = GroupMeterViewSerializer
    lookup_field = 'public_key'

    def get_queryset(self):
        return GroupMeter.objects.public()


@authentication_classes((ApiKeyAuthentication,))
class NewMeasurementView(CreateAPIView):
    """
    View to create new measurements for a meter
    client will be the GPX-Connector, using the API key for authentication
    Available request methods: POST
    `POST`:
    After data validation, a meter is updated or created with the latest data, new measurements are
    created from the posted data
    """
    POST_permissions = [permissions.IsAuthenticated]
    serializer_class = NewMeasurementSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GroupLiveDataView(ListAPIView):
    """
    View used by nodejs, and only available for the nodejs service, to get latest data for all requested groups
    Available request methods: GET
    `GET`:
    Will return group if group had at least one change in the past 15 seconds
    The group will contain the participants that have been updated in the past 15 seconds
    (The dashboard starts with the latest data, so no need to send data that is already available on the dashboard)
    """
    GET_permissions = [RequestFromNodejs]
    serializer_class = GroupLiveDataSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['pk']
    ordering = ['pk']

    def get_queryset(self):
        group_ids = self.request.query_params.get('groups')
        group_ids = group_ids.split(',') if group_ids else []
        return GroupMeter.objects.live_groups(group_ids)


class PingView(APIView):
    """Debugging view for testing api connection"""

    def get(self, request, *args, **kwargs):
        return HttpResponse("OK\n", content_type="text/plain")


@authentication_classes((ApiKeyAuthentication,))
class NewMeasurementTestView(CreateAPIView):
    """Debugging view for gpx connector testing"""
    POST_permissions = [permissions.IsAuthenticated]
    serializer_class = NewMeasurementTestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
