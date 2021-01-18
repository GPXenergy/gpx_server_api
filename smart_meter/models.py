import uuid

from django.db import models
from django.utils import timezone

from smart_meter.managers import SmartMeterManager, PowerMeasurementManager, GasMeasurementManager, \
    SolarMeasurementManager, GroupMeterManager, GroupParticipantManager
from users.models import User


class SmartMeter(models.Model):
    """
    Meter model that keeps track of constant meter data (serial number, meter values kWh m³, etc.)
    Instance is updated each time a new measurement is posted
    """
    objects = SmartMeterManager()

    METER_TYPE_OPTIONS = (
        ('consumer', 'Consument'),
        ('prosumer', 'Prosument'),
        ('battery', 'Batterij'),
        ('producer_solar', 'Producent solar'),
        ('producer_wind', 'Producent wind'),
        ('producer_other', 'Producent wind'),
    )

    # Related to user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meters')
    # Customizable name for this meter, for identification to the user
    name = models.CharField(max_length=30)
    # If the meter name and relations are made public when the group meter is made public
    public = models.BooleanField(default=False)
    # GPX-Connector version
    gpx_version = models.CharField(max_length=20, default='undefined')  # 'x.y.z'
    # Timestamp of last change to this model due to measurements
    last_update = models.DateTimeField(auto_now_add=True)

    # Latest power data (required part)
    sn_power = models.CharField(max_length=40)
    power_timestamp = models.DateTimeField()
    power_import_1 = models.DecimalField(max_digits=9, decimal_places=3)
    power_import_2 = models.DecimalField(max_digits=9, decimal_places=3)
    power_export_1 = models.DecimalField(max_digits=9, decimal_places=3)
    power_export_2 = models.DecimalField(max_digits=9, decimal_places=3)
    tariff = models.SmallIntegerField()
    actual_power_import = models.DecimalField(max_digits=9, decimal_places=3)
    actual_power_export = models.DecimalField(max_digits=9, decimal_places=3)

    # Latest gas data
    sn_gas = models.CharField(max_length=40, null=True)
    gas_timestamp = models.DateTimeField(null=True)
    gas = models.DecimalField(max_digits=9, decimal_places=3, null=True)

    # Latest solar data, not P1 data, but keeps track of latest value
    solar_timestamp = models.DateTimeField(null=True)
    solar = models.DecimalField(max_digits=9, decimal_places=3, null=True)

    type = models.CharField(choices=METER_TYPE_OPTIONS, max_length=20, default='consumer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def active(self):
        """
        Property if the meter was updated in the past day
        :return: bool
        """
        return self.last_update > timezone.now() - timezone.timedelta(days=1)

    @property
    def last_power_measurement(self):
        """
        Get the last power measurement
        :return: PowerMeasurement
        """
        if not hasattr(self, 'last_power_measurement_'):
            self.last_power_measurement_ = self.powermeasurement_set.last()
        return self.last_power_measurement_

    @property
    def last_gas_measurement(self):
        """
        Get the last gas measurement
        :return: GasMeasurement
        """
        if not hasattr(self, 'last_gas_measurement_'):
            self.last_gas_measurement_ = self.gasmeasurement_set.last()
        return self.last_gas_measurement_

    @property
    def last_solar_measurement(self):
        """
        Get the last gas measurement
        :return: GasMeasurement
        """
        if not hasattr(self, 'last_solar_measurement_'):
            self.last_solar_measurement_ = self.solarmeasurement_set.last()
        return self.last_solar_measurement_

    @property
    def power_import(self):
        return self.power_import_1 + self.power_import_2

    @property
    def power_export(self):
        return self.power_export_1 + self.power_export_2

    @property
    def group_participation(self):
        if not hasattr(self, 'group_participation_'):
            self.group_participation_ = self.group_participations.active().select_related('group', 'meter').first()
        return self.group_participation_

    def save(self, **kwargs):
        if not self.pk and not self.name:
            # New instance, give default name `meter x`, where x is the amount of meters the user has + 1
            self.name = '%s %s' % (self.user.username, self.user.meters.count() + 1)
        super().save(**kwargs)

    def __str__(self):
        return "Meter %s" % self.sn_power


class Measurement(models.Model):
    """
    Abstract measurement class, extended by PowerMeasurement and GasMeasurement
    """

    class Meta:
        abstract = True
        unique_together = ('meter', 'timestamp')

    timestamp = models.DateTimeField()
    meter = models.ForeignKey(SmartMeter, models.CASCADE)

    def __str__(self):
        return "%s %s %s" % (self.meter, self.__class__.__name__, self.timestamp.strftime("%Y-%m-%d %H:%M:%S"))


class PowerMeasurement(Measurement):
    """
    A single power measurement from 1 meter
    """
    objects = PowerMeasurementManager()

    power_imp = models.DecimalField(max_digits=9, decimal_places=3)
    power_exp = models.DecimalField(max_digits=9, decimal_places=3)


class GasMeasurement(Measurement):
    """
    A single gas measurement from 1 meter
    """
    objects = GasMeasurementManager()

    # Difference in gas m³ since last measurement
    total = models.DecimalField(max_digits=9, decimal_places=3)
    gas = models.DecimalField(max_digits=9, decimal_places=3)


class SolarMeasurement(Measurement):
    """
    A solar export measurement from the inverter
    """
    objects = SolarMeasurementManager()

    solar = models.DecimalField(max_digits=9, decimal_places=3)


def default_public_key():
    return str(uuid.uuid4())


class GroupMeter(models.Model):
    """
    The group meter model, contains some information about the group meter itself, and related to user (the manager)
    and participants
    """
    objects = GroupMeterManager()

    name = models.CharField(max_length=50)
    # Short summary for extra description of the group meter, optional
    summary = models.TextField(max_length=1000, blank=True, default='')
    created_on = models.DateTimeField(auto_now_add=True)
    # flag if the group is accessible by visitors
    public = models.BooleanField(default=False)
    # If public, this key can be used to access it (Slug, [-a-zA-Z0-9_]+)
    public_key = models.SlugField(default=default_public_key, unique=True, max_length=40)
    invitation_key = models.UUIDField(default=uuid.uuid4, unique=True)
    allow_invite = models.BooleanField(default=True)

    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manager_groups')
    meters = models.ManyToManyField(SmartMeter, related_name='groups', through='GroupParticipant')

    @property
    def active_participants(self):
        """
        Get all active participants
        :return: 
        """
        return self.participants.active()

    @property
    def recent_participants(self):
        """
        Get all recent active participants (where the meter was updated in the past 15 seconds)
        :return:
        """
        just_now = timezone.now() - timezone.timedelta(seconds=15)
        return self.active_participants.filter(meter__last_update__gte=just_now)

    @property
    def total_import(self):
        """
        Get total_import from all participants
        :return: total_import in the group
        """
        return sum([participant.total_import for participant in self.participants.all()])

    @property
    def total_export(self):
        """
        Get total_export from all participants
        :return: total_export in the group
        """
        return sum([participant.total_export for participant in self.participants.all()])

    @property
    def total_gas(self):
        """
        Get total_gas from all participants
        :return: total_gas in the group
        """
        return sum([participant.total_gas for participant in self.participants.all()])

    @property
    def actual_power(self):
        """
        Get actual_power from all active_participants
        :return: actual_power in the group
        """
        return sum([participant.actual_power for participant in self.active_participants])

    @property
    def actual_gas(self):
        """
        Get actual_gas from all active_participants
        :return: actual_gas in the group
        """
        return sum([participant.actual_gas for participant in self.active_participants])

    @property
    def actual_solar(self):
        """
        Get actual_solar from all active_participants
        :return: actual_solar in the group
        """
        return sum([participant.actual_solar for participant in self.active_participants])

    def new_invitation_key(self):
        self.invitation_key = uuid.uuid4()

    def new_public_key(self):
        self.public_key = default_public_key()


class GroupParticipant(models.Model):
    objects = GroupParticipantManager()

    group = models.ForeignKey(GroupMeter, on_delete=models.CASCADE, related_name='participants')
    meter = models.ForeignKey(SmartMeter, on_delete=models.CASCADE, related_name='group_participations')
    joined_on = models.DateTimeField(auto_now_add=True)
    left_on = models.DateTimeField(default=None, null=True)

    # Customizable name for this meter, for displaying in the group
    display_name = models.CharField(max_length=30)

    # Values at time of joining
    power_import_joined = models.DecimalField(max_digits=9, decimal_places=3)
    power_export_joined = models.DecimalField(max_digits=9, decimal_places=3)
    gas_joined = models.DecimalField(max_digits=9, decimal_places=3, null=True)

    # Values at time of leaving, default null
    power_import_left = models.DecimalField(max_digits=9, decimal_places=3, null=True)
    power_export_left = models.DecimalField(max_digits=9, decimal_places=3, null=True)
    gas_left = models.DecimalField(max_digits=9, decimal_places=3, null=True)

    @property
    def active(self):
        """
        Property if the participant is active
        :return:
        """
        return self.left_on is None

    @property
    def total_import(self):
        if self.active:
            return self.meter.power_import - self.power_import_joined
        return self.power_import_left - self.power_import_joined

    @property
    def total_export(self):
        if self.active:
            return self.meter.power_export - self.power_export_joined
        return self.power_export_left - self.power_export_joined

    @property
    def total_gas(self):
        if not self.gas_joined:
            return 0
        if self.active:
            return self.meter.gas - self.gas_joined
        return self.gas_left - self.gas_joined

    @property
    def actual_power(self):
        if self.active and self.meter.active:
            return self.meter.actual_power_export - self.meter.actual_power_import
        return 0

    @property
    def actual_gas(self):
        if self.active and self.meter.gas and self.meter.active:
            return self.meter.gas
        return 0

    @property
    def actual_solar(self):
        if self.active and self.meter.solar and self.meter.active:
            return self.meter.solar
        return 0

    @property
    def type(self):
        if self.active:
            return self.meter.type
        return None

    def save(self, **kwargs):
        if not self.pk:
            # New participant, set default values
            if not self.display_name:
                self.display_name = self.meter.name
            self.power_import_joined = self.meter.power_import
            self.power_export_joined = self.meter.power_export
            self.gas_joined = self.meter.gas
        super().save(**kwargs)

    def leave(self):
        self.left_on = timezone.now()
        self.power_import_left = self.meter.power_import
        self.power_export_left = self.meter.power_export
        self.gas_left = self.meter.gas
