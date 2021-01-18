from django.db import models, transaction
from django.db.models import Prefetch
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

    def new_measurement(self, user, power, gas=None, solar=None, gpx_version=None):
        gas = gas or {}
        solar = solar or {}
        meter, created = self.update_or_create(
            defaults=dict(
                gpx_version=gpx_version or 'undefined',
                sn_power=power.get('sn'),
                power_timestamp=power.get('timestamp'),
                power_import_1=power.get('import_1'),
                power_import_2=power.get('import_2'),
                power_export_1=power.get('export_1'),
                power_export_2=power.get('export_2'),
                tariff=power.get('tariff'),
                actual_power_import=power.get('actual_import'),
                actual_power_export=power.get('actual_export'),
                sn_gas=gas.get('sn'),
                gas_timestamp=gas.get('timestamp'),
                gas=gas.get('gas'),
                solar_timestamp=solar.get('timestamp'),
                solar=solar.get('solar'),
                last_update=timezone.now(),
            ),
            user=user,
            sn_power=power.get('sn'),
        )

        new_power_measurement = None

        last_power = meter.last_power_measurement
        if power and power.get('timestamp'):
            new_power_measurement = meter.powermeasurement_set.add_new_power_measurement(created, last_power, **power)
        last_gas = meter.last_gas_measurement
        if gas and new_power_measurement and gas.get('timestamp'):
            meter.gasmeasurement_set.add_new_gas_measurement(created, last_gas, **gas)
        last_solar = meter.last_solar_measurement
        if solar and new_power_measurement and solar.get('timestamp'):
            meter.solarmeasurement_set.add_new_solar_measurement(created, last_solar, **solar)

        return meter


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
                power_imp=kwargs.get('actual_import'),
                power_exp=kwargs.get('actual_export'),
            )


class GasMeasurementManager(models.Manager):
    """
    Manager for the GasMeasurement model
    """
    use_for_related_fields = True
    minimum_store_duration = timezone.timedelta(minutes=5)

    def add_new_gas_measurement(self, meter_created, last_measurement, timestamp, gas, **kwargs):
        """
        Adds a new gas measurement to the meter
        :param meter_created: if the meter was initially created, if it was, it will always add the gas measurement
        :param last_measurement: timestamp of last gas measurement
        :param timestamp: timestamp of new measurement
        :param gas: gas value of new measurement
        :param kwargs: other gas measurement data
        :return:
        """
        if meter_created or not last_measurement or \
                last_measurement.timestamp + self.minimum_store_duration < timestamp:
            gas_val = 0  # initial gas usage is 0
            if last_measurement and gas > last_measurement.gas:
                # Gas value in measurement is difference between last measurement and this measurement
                gas_val = gas - last_measurement.total
            return self.create(
                timestamp=timestamp,
                gas=gas_val,
                total=gas,
            )


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
                solar=kwargs.get('solar')
            )


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
