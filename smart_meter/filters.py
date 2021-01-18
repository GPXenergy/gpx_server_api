from django.db.models import QuerySet, Min, Avg, Sum
from django.db.models.functions import TruncHour, TruncMinute, TruncDay
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from smart_meter.models import Measurement, GroupParticipant


class MeasurementFilter(filters.FilterSet):
    timestamp = filters.IsoDateTimeFromToRangeFilter(field_name='timestamp', required=True, method='filter_timestamp')

    class Meta:
        model = Measurement
        fields = ['timestamp']

    def filter_timestamp(self, qs: QuerySet, field, value):
        if value.start is None:
            raise ValidationError("Requires start timestamp")
        elif value.stop is None:
            raise ValidationError("Requires stop timestamp")

        qs = qs.filter(timestamp__range=(value.start, value.stop))
        delta: timezone.timedelta = value.stop - value.start
        if delta.days < 2:
            qs = qs.annotate(
                timestamp_trunc=TruncMinute('timestamp')
            ).values('timestamp_trunc')
        elif delta.days < 14:
            qs = qs.annotate(
                timestamp_trunc=TruncHour('timestamp')
            ).values('timestamp_trunc')
        else:
            qs = qs.annotate(
                timestamp_trunc=TruncDay('timestamp')
            ).values('timestamp_trunc')

        return self.filter_timestamp_aggregation(qs)

    def filter_timestamp_aggregation(self, qs):
        raise NotImplementedError


class PowerMeasurementFilter(MeasurementFilter):
    def filter_timestamp_aggregation(self, qs):
        qs = qs.annotate(
            id=Min('id'),
            power_imp=Avg('power_imp'),  # power as average over given time period
            power_exp=Avg('power_exp'),  # power as average over given time period
            timestamp=Min('timestamp')
        )
        return qs.values('id', 'timestamp', 'power_imp', 'power_exp')


class GasMeasurementFilter(MeasurementFilter):
    def filter_timestamp_aggregation(self, qs):
        qs = qs.annotate(
            id=Min('id'),
            gas=Sum('gas'),  # gas in m³ is better as total in given time period
            timestamp=Min('timestamp')
        )
        return qs.values('id', 'timestamp', 'gas')


class SolarMeasurementFilter(MeasurementFilter):
    def filter_timestamp_aggregation(self, qs):
        qs = qs.annotate(
            id=Min('id'),
            solar=Avg('solar'),  # solar power as average over given time period
            timestamp=Min('timestamp')
        )
        return qs.values('id', 'timestamp', 'solar')


class GroupParticipantFilter(filters.FilterSet):
    active = filters.BooleanFilter(method='filter_active')

    class Meta:
        model = GroupParticipant
        fields = ['active']

    def filter_active(self, qs: QuerySet, field, value):
        return qs.filter(left_on__isnull=value)
