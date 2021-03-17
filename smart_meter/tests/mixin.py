import decimal
import random

from django.urls import reverse
from django.utils import timezone

from smart_meter.models import SmartMeter, SolarMeasurement, GasMeasurement, PowerMeasurement, GroupMeter, \
    GroupParticipant
from users.tests.mixin import UserTestMixin

# Incremental serial number for meter for uniqueness
meter_serial = 1


class MeterTestMixin(UserTestMixin):
    """
    Mixin class adding easy meter-related functions for testing
    """

    class MeterUrls:
        """
        Collection of urls for easy url generation from given params
        """

        @staticmethod
        def user_meter_url(user_pk, meter_pk=None):
            """
            user meters url (/users/id/meters/id?)
            :param user_pk: Id of user
            :param meter_pk: Id of meter  (optional)
            :return: url
            """
            if meter_pk:
                return reverse('users:user_meter_detail', kwargs={'user_pk': user_pk, 'pk': meter_pk})
            return reverse('users:user_meter_list', kwargs={'user_pk': user_pk})

        @staticmethod
        def power_measurement_url(user_pk, meter_pk):
            """
            power_measurement_list url (/users/id/meters/id/power/)
            :param user_pk: Id of user
            :param meter_pk: Id of meter
            :return: url
            """
            return reverse('users:power_measurement_list', kwargs={'user_pk': user_pk, 'meter_pk': meter_pk})

        @staticmethod
        def gas_measurement_url(user_pk, meter_pk):
            """
            gas_measurement_list url (/users/id/meters/id/gas/)
            :param user_pk: Id of user
            :param meter_pk: Id of meter
            :return: url
            """
            return reverse('users:gas_measurement_list', kwargs={'user_pk': user_pk, 'meter_pk': meter_pk})

        @staticmethod
        def solar_measurement_url(user_pk, meter_pk):
            """
            solar_measurement_list url (/users/id/meters/id/solar/)
            :param user_pk: Id of user
            :param meter_pk: Id of meter
            :return: url
            """
            return reverse('users:solar_measurement_list', kwargs={'user_pk': user_pk, 'meter_pk': meter_pk})

        @staticmethod
        def meter_group_participation_url(user_pk, participation_pk=None):
            """
            All group participation for a meter url (/users/id/meters/participation/id?/)
            :param user_pk: Id of user
            :param participation_pk: id of participation (optional)
            :return: url
            """
            if participation_pk:
                return reverse('users:meter_participation_detail',
                               kwargs={'user_pk': user_pk, 'pk': participation_pk})
            return reverse('users:meter_participation_list', kwargs={'user_pk': user_pk})

        @staticmethod
        def user_group_meter_url(user_pk, group_pk=None):
            """
            group meter url (/users/id/groups/id?/)
            :param user_pk: Id of user
            :param group_pk: Id of group meter (optional)
            :return: url
            """
            if group_pk:
                return reverse('users:group_meter_detail', kwargs={'user_pk': user_pk, 'pk': group_pk})
            return reverse('users:group_meter_list', kwargs={'user_pk': user_pk})

        @staticmethod
        def meter_display_url(meter_lookup, public):
            """
            public/private group detail url (/meters/group/public?/lookup/)
            :param meter_lookup: Id or public key for meter
            :param public: flag, true to get public url
            :return: url
            """
            if public:
                return reverse('smart_meter:public_group_meter_display', kwargs={'public_key': meter_lookup})
            return reverse('smart_meter:group_meter_display', kwargs={'pk': meter_lookup})

        @staticmethod
        def group_meter_invite_info(invitation_key):
            """
            Group meter invite info url (/meters/group/:invitekey/)
            :param invitation_key: invite key
            :return: url
            """
            return reverse('smart_meter:group_meter_invite_info', kwargs={'invitation_key': invitation_key})

        @staticmethod
        def new_measurement_url():
            """
            New measurement url (/meters/measurement/)
            :return: url
            """
            return reverse('smart_meter:new_measurement')

        @staticmethod
        def group_live_data_url():
            """
            New measurement url (/meters/groups/live-data/)
            :return: url
            """
            return reverse('smart_meter:group_live_data')

    @classmethod
    def default_smart_meter_data(cls):
        """
        Generate some random data to create a smart meter
        :return:
        """
        global meter_serial
        # Increment serial number for uniqueness
        meter_serial += 1
        return {
            'gpx_version': '1.2.3',
            'sn_power': '%d' % (meter_serial + 123123),
            'power_timestamp': timezone.now(),
            'actual_power_import': decimal.Decimal(random.randint(0, 1000) / 1000),
            'actual_power_export': decimal.Decimal(random.randint(0, 1000) / 1000),
            'tariff': 1,
            'total_power_import_1': decimal.Decimal(random.randint(0, 10000) / 1000),
            'total_power_import_2': decimal.Decimal(random.randint(0, 10000) / 1000),
            'total_power_export_1': decimal.Decimal(random.randint(0, 10000) / 1000),
            'total_power_export_2': decimal.Decimal(random.randint(0, 10000) / 1000),
            'sn_gas': '%d' % (meter_serial + 124124),
            'gas_timestamp': timezone.now(),
            'actual_gas': decimal.Decimal(random.randint(0, 1000) / 1000),
            'total_gas': decimal.Decimal(random.randint(0, 10000) / 1000),
            'solar_timestamp': timezone.now(),
            'actual_solar': decimal.Decimal(random.randint(0, 1000) / 1000),
            'total_solar': decimal.Decimal(random.randint(0, 10000) / 1000),
        }

    @classmethod
    def create_smart_meter(cls, user=None, **meter_data):
        """
        Create a smart meter object, if no user is given a new user is created, all meter data is optional
        :param user:
        :param meter_data:
        :return: new meter
        """
        meter_data = {
            **cls.default_smart_meter_data(),
            **meter_data,
            'user': user or cls.create_user(),
            'type': 'consumer'
        }
        return SmartMeter.objects.create(
            **meter_data
        )

    @classmethod
    def create_power_measurement(cls, meter, **measurement_data):
        """
        Create a power measurement object for given meter, all measurement data is optional
        :param meter:
        :param measurement_data:
        :return:
        """
        measurement_data = {
            'timestamp': timezone.now(),
            'actual_import': decimal.Decimal(random.randint(0, 1000) / 1000),
            'actual_export': decimal.Decimal(random.randint(0, 1000) / 1000),
            'total_import_1': decimal.Decimal(random.randint(0, 10000) / 1000),
            'total_import_2': decimal.Decimal(random.randint(0, 10000) / 1000),
            'total_export_1': decimal.Decimal(random.randint(0, 10000) / 1000),
            'total_export_2': decimal.Decimal(random.randint(0, 10000) / 1000),
            **measurement_data,
            'meter': meter,
        }
        return PowerMeasurement.objects.create(
            **measurement_data
        )

    @classmethod
    def create_gas_measurement(cls, meter, **measurement_data):
        """
        Create a gas measurement object for given meter, all measurement data is optional
        :param meter:
        :param measurement_data:
        :return:
        """
        measurement_data = {
            'timestamp': timezone.now(),
            'actual_gas': decimal.Decimal(random.randint(0, 1000) / 1000),
            'total_gas': decimal.Decimal(random.randint(0, 10000) / 1000),
            **measurement_data,
            'meter': meter,
        }
        return GasMeasurement.objects.create(
            **measurement_data
        )

    @classmethod
    def create_solar_measurement(cls, meter, **measurement_data):
        """
        Create a solar measurement object for given meter, all measurement data is optional
        :param meter:
        :param measurement_data:
        :return:
        """
        measurement_data = {
            'timestamp': timezone.now(),
            'actual_solar': decimal.Decimal(random.randint(0, 1000) / 1000),
            'total_solar': decimal.Decimal(random.randint(0, 10000) / 1000),
            **measurement_data,
            'meter': meter,
        }
        return SolarMeasurement.objects.create(
            **measurement_data
        )

    @classmethod
    def create_group_meter(cls, manager=None, meter=None, **group_data):
        """
        Create a new group meter for given manager. If no meter is given a new meter will be created for the user
        :param manager: the user (manager)
        :param meter: group for meter
        :param group_data: other group data (optional)
        :return:
        """
        manager = manager or cls.create_user()
        meter = meter or cls.create_smart_meter(manager)
        assert meter.user_id == manager.id  # Just to make sure the meter is from manager

        group_data = {
            'manager': manager,
            'meter': meter,
            'name': 'My group',
            **group_data,
        }
        return GroupMeter.objects.create(
            **group_data
        )

    @classmethod
    def create_group_participation(cls, meter, group, **participant_data):
        """
        Create a new group participant for given meter. If no meter is given a new meter will be created for the user
        :param meter: meter to join a group
        :param group: the group to join
        :param participant_data: other participant data (optional)
        :return:
        """
        participant_data = {
            'group': group,
            'meter': meter,
            **participant_data,
        }
        return GroupParticipant.objects.create(
            **participant_data
        )
