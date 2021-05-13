from django.db import models, transaction
from django.db.models import Prefetch, functions
from django.utils import timezone


class SmartMeterManager(models.Manager):
    """
    Manager for the SmartMeter model
    """
    use_for_related_fields = True

    def user_meters(self, user_id):
        return self.filter(user_id=user_id)

    def create(self, user, **kwargs):
        meter = super().create(user=user, **kwargs)

        # Set new meter as user default, if user doesnt have a default yet
        if user.default_meter is None:
            user.default_meter = meter
            user.save(update_fields=['default_meter'])
        return meter

    def meter_statistics(self):
        return self.aggregate(
            live_meters=models.Count('pk', models.Q(last_update__gte=timezone.now() - timezone.timedelta(hours=2))),
            total_meters=models.Count('pk'),
        )

    def new_measurement(self, user, power, gas=None, solar=None, gpx_version=None):
        gas = gas or {}
        solar = solar or {}
        meter, created = self.update_or_create(
            defaults=dict(
                gpx_version=gpx_version or 'Unknown',
                sn_power=power.get('sn'),
                power_timestamp=power.get('timestamp'),
                actual_power_import=power.get('actual_import'),
                actual_power_export=power.get('actual_export'),
                tariff=power.get('tariff'),
                total_power_import_1=power.get('import_1'),
                total_power_import_2=power.get('import_2'),
                total_power_export_1=power.get('export_1'),
                total_power_export_2=power.get('export_2'),
                sn_gas=gas.get('sn'),
                gas_timestamp=gas.get('timestamp'),
                total_gas=gas.get('gas'),
                # actual_gas=gas.get('gas'),  -- Actual gas is set after measurement
                solar_timestamp=solar.get('timestamp'),
                actual_solar=solar.get('solar'),
                total_solar=solar.get('total'),
                last_update=timezone.now(),
            ),
            user=user,
            sn_power=power.get('sn'),
        )

        new_power_measurement = None

        if power and power.get('timestamp'):
            last_power = meter.last_power_measurement
            new_power_measurement = meter.powermeasurement_set.add_new_power_measurement(created, last_power, **power)
        if solar and new_power_measurement and solar.get('timestamp'):
            last_solar = meter.last_solar_measurement
            meter.solarmeasurement_set.add_new_solar_measurement(created, last_solar, **solar)
        if gas and gas.get('timestamp'):
            last_gas = meter.last_gas_measurement
            new_gas = meter.gasmeasurement_set.add_new_gas_measurement(created, last_gas, **gas)
            if new_gas:
                # Save the actual gas to the meter object
                meter.actual_gas = new_gas.actual_gas
                meter.save(update_fields=['actual_gas'])

        return meter


class MeasurementQuerySet(models.QuerySet):
    def filter_timestamp(self, after, before):
        qs = self.filter(timestamp__range=(after, before))
        delta: timezone.timedelta = before - after
        if delta.days < 2:
            qs = qs.annotate(
                timestamp_trunc=functions.TruncMinute('timestamp')
            ).values('timestamp_trunc')
        elif delta.days < 14:
            qs = qs.annotate(
                timestamp_trunc=functions.TruncHour('timestamp')
            ).values('timestamp_trunc')
        else:
            qs = qs.annotate(
                timestamp_trunc=functions.TruncDay('timestamp')
            ).values('timestamp_trunc')

        return self.filter_timestamp_aggregation(qs).order_by('id')

    def filter_timestamp_aggregation(self, qs):
        raise NotImplementedError


class PowerMeasurementQuerySet(MeasurementQuerySet):
    def filter_timestamp_aggregation(self, qs):
        qs = qs.annotate(
            id=models.Min('id'),
            actual_import=models.Avg('actual_import'),  # power as average over given time period
            actual_export=models.Avg('actual_export'),  # power as average over given time period
            timestamp=models.Min('timestamp'),
            total_import_1=models.Max('total_import_1') - models.Min('total_import_1'),
            total_import_2=models.Max('total_import_2') - models.Min('total_import_2'),
            total_export_1=models.Max('total_export_1') - models.Min('total_export_1'),
            total_export_2=models.Max('total_export_2') - models.Min('total_export_2'),
        )
        return qs.values(
            'id', 'timestamp', 'actual_import', 'actual_export',
            'total_import_1', 'total_import_2', 'total_export_1', 'total_export_2',
        )


class SolarMeasurementQuerySet(MeasurementQuerySet):
    def filter_timestamp_aggregation(self, qs):
        qs = qs.annotate(
            id=models.Min('id'),
            actual_solar=models.Avg('actual_solar'),
            total_solar=models.Max('total_solar') - models.Min('total_solar'),
            timestamp=models.Min('timestamp')
        )
        return qs.values('id', 'timestamp', 'actual_solar', 'total_solar', )


class GasMeasurementQuerySet(MeasurementQuerySet):
    def filter_timestamp_aggregation(self, qs):
        qs = qs.annotate(
            id=models.Min('id'),
            actual_gas=models.Avg('actual_gas'),
            total_gas=models.Max('total_gas') - models.Min('total_gas'),
            timestamp=models.Min('timestamp')
        )
        return qs.values('id', 'timestamp', 'actual_gas', 'total_gas', )


class PowerMeasurementManager(models.Manager):
    """
    Manager for the PowerMeasurement model
    """
    use_for_related_fields = True
    minimum_store_duration = timezone.timedelta(minutes=5)

    def add_new_power_measurement(self, meter_created, last_measurement, timestamp, **kwargs):
        """
        Adds a new power measurement to the meter
        :param meter_created: if the meter was initially created, if it was, it will always add the power measurement
        :param last_measurement: timestamp of last power measurement
        :param timestamp: timestamp of new measurement
        :param kwargs: other power measurement data
        :return:
        """
        if meter_created or not last_measurement or \
                last_measurement.timestamp + self.minimum_store_duration < timestamp:
            return self.create(
                timestamp=timestamp,
                actual_import=kwargs.get('actual_import'),
                actual_export=kwargs.get('actual_export'),
                total_import_1=kwargs.get('import_1'),
                total_import_2=kwargs.get('import_2'),
                total_export_1=kwargs.get('export_1'),
                total_export_2=kwargs.get('export_2'),
            )

    def get_queryset(self):
        return PowerMeasurementQuerySet(model=self.model, using=self._db)


class GasMeasurementManager(models.Manager):
    """
    Manager for the GasMeasurement model
    """
    use_for_related_fields = True
    minimum_store_duration = timezone.timedelta(minutes=4, seconds=30)

    def add_new_gas_measurement(self, meter_created, last_measurement, timestamp, gas, **kwargs):
        """
        Adds a new gas measurement to the meter
        :param meter_created: if the meter was initially created, if it was, it will always add the gas measurement
        :param last_measurement: timestamp of last gas measurement
        :param timestamp: timestamp of new measurement
        :param gas: gas value of new measurement
        :param kwargs: other gas measurement data
        :rtype: smart_meter.models.GasMeasurement
        """
        if meter_created or not last_measurement or \
                last_measurement.timestamp + self.minimum_store_duration < timestamp:
            actual_gas = 0  # actual default 0, also if new measurement is lower it will be 0
            if last_measurement and gas > last_measurement.total_gas:
                gas_difference = float(gas - last_measurement.total_gas)
                time_difference = timestamp - last_measurement.timestamp
                # actual gas in m3/h
                actual_gas = gas_difference * (timezone.timedelta(hours=1) / time_difference)
            return self.create(
                timestamp=timestamp,
                actual_gas=actual_gas,
                total_gas=gas,
            )

    def get_queryset(self):
        return GasMeasurementQuerySet(model=self.model, using=self._db)


class SolarMeasurementManager(models.Manager):
    """
    Manager for the SolarMeasurement model
    """
    use_for_related_fields = True
    minimum_store_duration = timezone.timedelta(minutes=5)

    def add_new_solar_measurement(self, meter_created, last_measurement, timestamp, **kwargs):
        """
        Adds a new solar measurement to the meter
        :param meter_created: if the meter was initially created, if it was, it will always add the solar measurement
        :param last_measurement: timestamp of last solar measurement
        :param timestamp: timestamp of new measurement
        :param kwargs: other solar measurement data
        :return:
        """
        if meter_created or not last_measurement or \
                last_measurement.timestamp + self.minimum_store_duration < timestamp:
            return self.create(
                timestamp=timestamp,
                actual_solar=kwargs.get('solar'),
                total_solar=kwargs.get('total', 0),
            )

    def get_queryset(self):
        return SolarMeasurementQuerySet(model=self.model, using=self._db)


class GroupMeterManager(models.Manager):
    """
    Manager for the GroupMeter model
    """
    use_for_related_fields = True

    def get_queryset(self):
        """
        Default queryset prefetches participants to reduce query count
        :return: qs
        """
        from .models import GroupParticipant
        return super().get_queryset().prefetch_related(
            Prefetch('participants', GroupParticipant.objects.select_related('meter', 'meter__user').order_by('pk'))
        )

    def managed_by(self, user_id):
        """
        Get groups by manager
        :param user_id:
        :return:
        """
        return self.filter(manager_id=user_id)

    def public(self):
        """
        Get all public meters
        :return:
        """
        return self.filter(public=True)

    def by_user(self, user_id):
        """
        Get active groups by user id
        :param user_id:
        :return:
        """
        return self.filter(participants__meter__user_id=user_id, participants__left_on__isnull=True).distinct()

    def live_groups(self, group_ids):
        just_now = timezone.now() - timezone.timedelta(seconds=15)
        return self.filter(participants__left_on__isnull=True,
                           participants__meter__last_update__gte=just_now, pk__in=group_ids).distinct()

    def group_meter_statistics(self):
        return self.aggregate(
            public_groups=models.Count('pk', models.Q(public=True)),
            total_groups=models.Count('pk'),
        )

    @transaction.atomic()
    def create(self, manager, meter, **kwargs):
        """
        Create a new group meter. also creates a participant for the initial user
        :param manager: user that created the meter
        :param meter: the meter from the user, as initial participant
        :param kwargs: other group meter data
        :return: group meter object
        """
        group = super().create(manager=manager, **kwargs)
        group.participants.create(meter=meter, display_name=meter.name)
        return group


class GroupParticipantManager(models.Manager):
    """
    Manager for the GroupParticipant model
    """
    use_for_related_fields = True

    def active(self):
        return self.filter(left_on__isnull=True)
