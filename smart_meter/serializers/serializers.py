from rest_framework import serializers

from smart_meter.models import SmartMeter, PowerMeasurement, GasMeasurement, GroupParticipant, GroupMeter, \
    SolarMeasurement
from users.models import User
from users.serializers import SimpleUserSerializer
from .serializer_helpers import SimpleMeterSerializer, GroupParticipantSerializer, NewPowerMeasurementSerializer, \
    NewSolarMeasurementSerializer, NewGasMeasurementSerializer, RealTimeParticipantSerializer, \
    MeterGroupParticipationSerializer, SimpleGroupMeterSerializer, ParticipantLiveDataSerializer, \
    PowerMeasurementSetSerializer, GasMeasurementSetSerializer, SolarMeasurementSetSerializer


class PowerMeasurementSerializer(serializers.ModelSerializer):
    """
    Serializer for power measurements, both list and detail, read only
    """

    class Meta:
        model = PowerMeasurement
        fields = (
            'timestamp',
            'actual_import',
            'actual_export',
            'total_import_1',
            'total_import_2',
            'total_export_1',
            'total_export_2',
        )
        read_only_fields = fields


class GasMeasurementSerializer(serializers.ModelSerializer):
    """
    Serializer for gas measurements, both list and detail, read only
    """

    class Meta:
        model = GasMeasurement
        fields = (
            'timestamp',
            'actual_gas',
            'total_gas',
        )
        read_only_fields = fields


class SolarMeasurementSerializer(serializers.ModelSerializer):
    """
    Serializer for solar measurements, both list and detail, read only
    """

    class Meta:
        model = SolarMeasurement
        fields = (
            'timestamp',
            'actual_solar',
            'total_solar',
        )
        read_only_fields = fields


class MeterListSerializer(serializers.ModelSerializer):
    """
    Meter list serializer, for retrieving a list of meters
    """

    class Meta:
        model = SmartMeter
        fields = (
            'pk',
            'name',
            'type',
            'gpx_version',
            'visibility_type',
            'last_update',
            'power_timestamp',
            'group_participation',
            'total_power_import_1',
            'total_power_import_2',
            'total_power_export_1',
            'total_power_export_2',
            'total_gas',
            'total_solar',
        )
        read_only_fields = fields

    group_participation = MeterGroupParticipationSerializer(read_only=True)


class MeterDetailSerializer(MeterListSerializer):
    """
    Meter detail serializer, for retrieving and updating a single meter object. Only the name and
    public fields can be updated
    """

    class Meta(MeterListSerializer.Meta):
        fields = MeterListSerializer.Meta.fields + (
            'sn_power',
            'tariff',
            'actual_power_import',
            'actual_power_export',
            'gas_timestamp',
            'sn_gas',
            'actual_gas',
            'solar_timestamp',
            'actual_solar',
        )
        read_only_fields = [field for field in fields if field not in ['name', 'visibility_type', 'type']]


class MeterMeasurementsDetailSerializer(MeterDetailSerializer):
    class Meta(MeterDetailSerializer.Meta):
        fields = MeterDetailSerializer.Meta.fields + (
            'power_set',
            'gas_set',
            'solar_set',
            'period_import_1',
            'period_import_2',
            'period_export_1',
            'period_export_2',
            'period_gas',
            'period_solar',
        )
        read_only_fields = fields

    power_set = PowerMeasurementSetSerializer(many=True, read_only=True)
    gas_set = GasMeasurementSetSerializer(many=True, read_only=True)
    solar_set = SolarMeasurementSetSerializer(many=True, read_only=True)


class GroupMeterListSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving a list of group meters from a user, or creating a new one
    """

    class Meta:
        model = GroupMeter
        fields = (
            'pk',
            'name',
            'summary',
            'meter',
            'manager',
            'created_on',
            'public',
            'public_key',
            'invitation_key',
            'allow_invite',
        )
        read_only_fields = (
            'pk',
            'created_on',
            'invitation_key',
            'manager',
        )
        extra_kwargs = {
            'meter': {'write_only': True}
        }

    meter = serializers.PrimaryKeyRelatedField(queryset=[], write_only=True)

    def get_fields(self):
        fields = super().get_fields()
        if fields.get('meter'):
            # The list serializer had meter field for creating, write only. not available in detail
            fields['meter'].queryset = SmartMeter.objects.user_meters(self.context['view'].user_id)
        return fields

    def to_representation(self, instance):
        if self.context['view'].user_id != instance.manager_id:
            del self.fields['invitation_key']
            del self.fields['allow_invite']
        return super().to_representation(instance)

    def validate_meter(self, val: SmartMeter):
        if val.group_participation is not None:
            raise serializers.ValidationError('Deze meter heeft al een groep')
        return val


class GroupMeterDetailSerializer(GroupMeterListSerializer):
    """
    Serializer for retrieving a group meter, or updating the group meter (as manager)
    """

    class Meta(GroupMeterListSerializer.Meta):
        fields = (
            'pk',
            'name',
            'summary',
            'created_on',
            'public',
            'public_key',
            'invitation_key',
            'new_invitation_key',
            'manager',
            'participants',
            'allow_invite',
        )
        read_only_fields = (
            'pk',
            'created_on',
            'invitation_key',
        )

    new_invitation_key = serializers.BooleanField(default=False, required=False, write_only=True)
    public_key = serializers.CharField(allow_blank=True)
    participants = GroupParticipantSerializer(many=True, read_only=True, source='active_participants')
    manager = serializers.PrimaryKeyRelatedField(queryset=[])

    def get_fields(self):
        fields = super().get_fields()
        fields['manager'].queryset = User.objects.active_in_group(self.context['view'].meter_id).exclude(pk=self.context['view'].user_id)
        return fields

    def validate_public_key(self, key):
        meter_id = self.context['view'].kwargs.get('pk')
        if GroupMeter.objects.exclude(pk=meter_id).filter(public_key=key).exists():
            raise serializers.ValidationError('Deze link is al in gebruik!')
        return key

    def update(self, instance: GroupMeter, validated_data):
        new_invitation_key = validated_data.pop('new_invitation_key', False)
        if new_invitation_key:
            # Reset invitation key
            instance.new_invitation_key()
        if validated_data.get('public_key') == '':
            # Reset public key
            validated_data.pop('public_key')
            instance.new_public_key()
        return super().update(instance, validated_data)


class GroupMeterViewSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving a group meter to display on the group meter real time view (public and dashboard)
    """

    class Meta:
        model = GroupMeter
        fields = (
            'pk',
            'name',
            'summary',
            'public',
            'public_key',
            'participants',
            'created_on',
            'total_import',
            'total_export',
            'total_gas',
            'actual_power',
            'actual_gas',
            'actual_solar',
        )
        read_only_fields = fields

    participants = RealTimeParticipantSerializer(many=True, read_only=True, source='active_participants')


class GroupMeterInviteInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving a group meter to display on the group meter real time view (public and dashboard)
    """

    class Meta:
        model = GroupMeter
        fields = (
            'pk',
            'name',
            'public',
            'manager',
            'invitation_key',
        )
        read_only_fields = fields

    manager = SimpleUserSerializer(read_only=True)


class GroupParticipationListSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving list of group participation from a user, or creating a new one (accepting an invitation)
    """

    class Meta:
        model = GroupParticipant
        fields = (
            'pk', 'group', 'meter', 'joined_on', 'left_on', 'active', 'total_import', 'total_export', 'total_gas',
            'invitation_key', 'display_name', 'type',
        )
        read_only_fields = (
            'pk', 'joined_on', 'left_on', 'active', 'total_import', 'total_export', 'total_gas', 'type',
        )
        extra_kwargs = {
            'invitation_key': {'write_only': True},
            'display_name': {'allow_null': True, 'allow_blank': True, 'required': False}
        }

    _group = None
    meter = serializers.PrimaryKeyRelatedField(queryset=[])
    group = serializers.PrimaryKeyRelatedField(queryset=GroupMeter.objects.all())
    invitation_key = serializers.CharField(write_only=True, required=True)

    def get_fields(self):
        fields = super().get_fields()
        fields['meter'].queryset = SmartMeter.objects.user_meters(self.context['view'].user_id)
        return fields

    def to_representation(self, instance):
        self.fields['meter'] = SimpleMeterSerializer(read_only=True)
        self.fields['group'] = SimpleGroupMeterSerializer(read_only=True)
        return super().to_representation(instance)

    def validate_meter(self, meter: SmartMeter):
        if meter.group_participations.active().exists():
            raise serializers.ValidationError('Deze meter heeft is al onderdeel van een groepsmeter!')
        return meter

    def validate_group(self, group: GroupMeter):
        if group.participants.count() >= 10:
            raise serializers.ValidationError('Groep "%s" heeft geen ruimte voor nieuwe leden!' % group.name)
        return group

    def validate(self, attrs):
        group = attrs.get('group')
        invitation_key = attrs.pop('invitation_key')
        if not group.allow_invite or str(group.invitation_key) != invitation_key:
            raise serializers.ValidationError({'invitation_key': ['Deze uitnodiging is niet geldig']})
        return super().validate(attrs)

    def create(self, validated_data):
        return super().create(validated_data)


class GroupParticipationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detail of group participation from a user, or updating one
    Has extra write only field 'active', if set to true, the participant will leave the group (set to inactive)
    """

    class Meta:
        model = GroupParticipant
        fields = (
            'pk', 'group', 'meter', 'joined_on', 'left_on', 'active', 'total_import', 'total_export', 'total_gas',
            'display_name', 'type',
        )
        read_only_fields = (
            'pk', 'group', 'meter', 'joined_on', 'left_on', 'total_import', 'total_export', 'total_gas', 'type',
        )

    group = SimpleGroupMeterSerializer(read_only=True)
    meter = SimpleMeterSerializer(read_only=True)
    active = serializers.BooleanField(write_only=True, default=True)

    def update(self, instance: GroupParticipant, validated_data):
        if not instance.active:
            raise serializers.ValidationError('Groepparticipatie is niet meer actief')
        if validated_data.pop('active', None) is False:
            instance.leave()
        return super().update(instance, validated_data)


class NewMeasurementSerializer(serializers.ModelSerializer):
    """
    Meter serializer that accepts a new measurement from the GPX-Connector. Upon saving, the serializer will
    get or create the meter object, and create measurements for that meter.
    """

    class Meta:
        model = SmartMeter
        fields = (
            'power',
            'gas',
            'solar',
        )

    power = NewPowerMeasurementSerializer(write_only=True)
    gas = NewGasMeasurementSerializer(write_only=True, allow_null=True, required=False)
    solar = NewSolarMeasurementSerializer(write_only=True, allow_null=True, required=False)

    def create(self, validated_data):
        return SmartMeter.objects.new_measurement(
            **validated_data,
        )


class NewMeasurementTestSerializer(NewMeasurementSerializer):
    """
    Meter serializer that accepts a new measurement from the GPX-Connector. Upon saving, the serializer will
    get or create the meter object, and create measurements for that meter.
    """
    power = NewPowerMeasurementSerializer()
    gas = NewGasMeasurementSerializer(allow_null=True, required=False)
    solar = NewSolarMeasurementSerializer(allow_null=True, required=False)

    def create(self, validated_data):
        return validated_data


class GroupLiveDataSerializer(serializers.ModelSerializer):
    """
    Group serializer used by nodejs to get latest data for all active live views
    """

    class Meta:
        model = GroupMeter
        fields = (
            'pk',
            'r',  # recent participants, but shorter to save data
            'ti',  # total_import
            'te',  # total_export
            'tg',  # total_gas
            'p',  # actual_power
            'g',  # actual_gas
            's',  # actual_solar
        )
        read_only_fields = fields

    r = ParticipantLiveDataSerializer(many=True, read_only=True, source='recent_participants')
    ti = serializers.DecimalField(9, 3, read_only=True, source='total_import')
    te = serializers.DecimalField(9, 3, read_only=True, source='total_export')
    tg = serializers.DecimalField(9, 3, read_only=True, source='total_gas')
    p = serializers.DecimalField(9, 3, read_only=True, source='actual_power')
    g = serializers.DecimalField(9, 3, read_only=True, source='actual_gas')
    s = serializers.DecimalField(9, 3, read_only=True, source='actual_solar')
