from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(SmartMeter)
admin.site.register(GroupMeter)
admin.site.register(GroupParticipant)
admin.site.register(GasMeasurement)
admin.site.register(SolarMeasurement)
admin.site.register(PowerMeasurement)
