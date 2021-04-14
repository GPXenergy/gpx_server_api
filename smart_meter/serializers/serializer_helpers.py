import pytz
from django.utils import timezone, dateparse
from django.utils.datetime_safe import datetime
from rest_framework import serializers

from smart_meter.models import SmartMeter, GroupParticipant, GroupMeter, SolarMeasurement, PowerMeasurement, \
    GasMeasurement


class PowerMeasurementSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerMeasurement
        fields = ()
        read_only_fields = fields

    def to_representation(self, instance):
        return [
            instance.get('timestamp'),
            instance.get('actual_import'),
            instance.get('actual_export'),
            instance.get('total_import_1'),
            instance.get('total_import_2'),
            instance.get('total_export_1'),
            instance.get('total_export_2'),
        ]


class GasMeasurementSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = GasMeasurement
        fields = ()
        read_only_fields = fields

    def to_representation(self, instance):
        return [
            instance.get('timestamp'),
            instance.get('actual_gas'),
            instance.get('total_gas'),
        ]


class SolarMeasurementSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolarMeasurement
        fields = ()
        read_only_fields = fields

    def to_representation(self, instance):
        return [
            instance.get('timestamp'),
            instance.get('actual_solar'),
            instance.get('total_solar'),
        ]


class SimpleMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartMeter
        fields = ('pk', 'name',)
        read_only_fields = fields


class SimpleGroupMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMeter
        fields = ('pk', 'name',)
        read_only_fields = fields


class MeterGroupParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupParticipant
        fields = (
            'pk',
            'group',
            'display_name',
        )
        read_only_fields = fields

    group = serializers.IntegerField(source='group_id')


class GroupParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupParticipant
        fields = (
            'pk',
            'display_name',
            'joined_on',
            'type',
            'left_on',
            'active',
            'total_import',
            'total_export',
            'total_gas',
        )
        read_only_fields = fields


class RealTimeParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupParticipant
        fields = (
            'pk',
            'display_name',
            'joined_on',
            'type',
            'last_activity',
            'total_import',
            'total_export',
            'total_gas',
            'actual_power',
            'actual_gas',
            'actual_solar',
        )
        read_only_fields = fields

    last_activity = serializers.SerializerMethodField()

    def get_last_activity(self, obj: GroupParticipant):
        return obj.meter.last_update


class _NewMeasurementSerializer(serializers.Serializer):
    timestamp = serializers.CharField(max_length=30)

    def validate_timestamp(self, value):
        timestamp = dateparse.parse_datetime(value)
        if not timestamp and value[-1] in ['W', 'S']:
            # timestamp format from smart meter
            timestamp = datetime.strptime(value[:-1], "%y%m%d%H%M%S")
            return timezone.make_aware(timestamp, timezone=pytz.timezone('Europe/Amsterdam'), is_dst=value[-1] == 'W')
        if not timestamp and value:
            # timestamp format from smart meter dsmr2.2 (without W or S indication)
            try:
                timestamp = datetime.strptime(value, "%y%m%d%H%M%S")
            except ValueError as e:
                # not a valid timestamp
                timestamp = None
        if not timestamp and value == 'now':
            # for dsmr2.2 power stamps, where there is none, the connector sends "now" for the api to define
            timestamp = timezone.now()

        if not timestamp:
            raise serializers.ValidationError('Invalid timestamp')

        if timezone.is_aware(timestamp):
            return timestamp
        return timezone.make_aware(timestamp, timezone=pytz.timezone('Europe/Amsterdam'))


class NewPowerMeasurementSerializer(_NewMeasurementSerializer):
    class Meta:
        fields = (
            'sn',
            'timestamp',
            'import_1',
            'import_2',
            'export_1',
            'export_2',
            'tariff',
            'actual_import',
            'actual_export',
        )

    sn = serializers.CharField(max_length=40)
    import_1 = serializers.DecimalField(9, 3)
    import_2 = serializers.DecimalField(9, 3)
    export_1 = serializers.DecimalField(9, 3)
    export_2 = serializers.DecimalField(9, 3)
    tariff = serializers.ChoiceField(choices=[(1, 1), (2, 2)])
    actual_import = serializers.DecimalField(9, 3)
    actual_export = serializers.DecimalField(9, 3)


class NewGasMeasurementSerializer(_NewMeasurementSerializer):
    class Meta:
        fields = (
            'sn',
            'timestamp',
            'gas',
        )

    sn = serializers.CharField(max_length=40)
    gas = serializers.DecimalField(9, 3)


class NewSolarMeasurementSerializer(_NewMeasurementSerializer):
    class Meta:
        fields = (
            'timestamp',
            'solar',
        )

    solar = serializers.DecimalField(9, 3)


class ParticipantLiveDataSerializer(serializers.ModelSerializer):
    """
    GroupParticipant serializer used by nodejs to get latest data for all active live views
    """

    class Meta:
        model = GroupParticipant
        fields = (
            'pk',
            'ti',  # total_import
            'te',  # total_export
            'tg',  # total_gas
            'p',  # actual_power
            'g',  # actual_gas
            's',  # actual_solar
        )
        read_only_fields = fields

    ti = serializers.DecimalField(9, 3, read_only=True, source='total_import')
    te = serializers.DecimalField(9, 3, read_only=True, source='total_export')
    tg = serializers.DecimalField(9, 3, read_only=True, source='total_gas')
    p = serializers.DecimalField(9, 3, read_only=True, source='actual_power')
    g = serializers.DecimalField(9, 3, read_only=True, source='actual_gas')
    s = serializers.DecimalField(9, 3, read_only=True, source='actual_solar')
