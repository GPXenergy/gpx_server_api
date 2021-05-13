from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView

from smart_meter.models import SmartMeter, GroupMeter
from users.models import User


class StatisticsSerializer(serializers.Serializer):
    class Meta:
        fields = ('live_meters', 'total_meters', 'public_groups', 'total_groups', 'total_users')
        read_only_fields = fields

    live_meters = serializers.IntegerField(read_only=True)
    total_meters = serializers.IntegerField(read_only=True)
    public_groups = serializers.IntegerField(read_only=True)
    total_groups = serializers.IntegerField(read_only=True)
    total_users = serializers.IntegerField(read_only=True)


class StatisticsView(RetrieveAPIView):
    serializer_class = StatisticsSerializer

    def get_object(self):
        return {
            **SmartMeter.objects.meter_statistics(),
            **GroupMeter.objects.group_meter_statistics(),
            **User.objects.user_statistics(),
        }
