from django.db import models
from django.db.models import QuerySet, Prefetch, Value, Min, Max
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from smart_meter.models import Measurement, GroupParticipant, SmartMeter, PowerMeasurement, GasMeasurement, \
    SolarMeasurement


class MeasurementFilter(filters.FilterSet):
    timestamp = filters.IsoDateTimeFromToRangeFilter(field_name='timestamp', required=True, method='filter_timestamp')

    class Meta:
        model = Measurement
        fields = ['timestamp']

    def filter_timestamp(self, qs, field, value):
        if value.start is None:
            raise ValidationError('Requires start timestamp')
        elif value.stop is None:
            raise ValidationError('Requires stop timestamp')

        return qs.filter_timestamp(value.start, value.stop)


class MeterMeasurementFilter(filters.FilterSet):
    timestamp = filters.IsoDateTimeFromToRangeFilter(method='filter_timestamp')
    measurements = filters.BooleanFilter(method='with_measurements')

    class Meta:
        model = SmartMeter
        fields = ['timestamp']

    def with_measurements(self, qs, field, value):
        return qs

    def filter_timestamp(self, qs, field, value):
        if value.start is None:
            raise ValidationError('Requires start timestamp')
        elif value.stop is None:
            raise ValidationError('Requires stop timestamp')

        qs = qs.annotate(
            timestamp_range_after_=Value(value.start, models.DateTimeField()),
            timestamp_range_before_=Value(value.stop, models.DateTimeField()),
        )
        return qs


class GroupParticipantFilter(filters.FilterSet):
    active = filters.BooleanFilter(method='filter_active')

    class Meta:
        model = GroupParticipant
        fields = ['active']

    def filter_active(self, qs: QuerySet, field, value):
        return qs.filter(left_on__isnull=value)
