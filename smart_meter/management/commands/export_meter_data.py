from django.core.management.base import BaseCommand, CommandError

from smart_meter.models import SmartMeter
from smart_meter.services.export_data import MeterDataExporter


class Command(BaseCommand):
    help = "Export all measurements for a meter to Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            "meter_id",
            type=int,
            help="Meter ID",
        )

        parser.add_argument(
            "filename",
            type=str,
            help="Output xlsx filename",
        )

    def handle(self, *args, **options):
        meter_id = options["meter_id"]
        filename = options["filename"]

        try:
            meter = SmartMeter.objects.get(pk=meter_id)
        except SmartMeter.DoesNotExist:
            raise CommandError(f"Meter {meter_id} does not exist")

        # Create exporter with progress callback
        exporter = MeterDataExporter(
            meter=meter,
            progress_callback=self.stdout.write
        )

        # Export to Excel
        file_path = exporter.export_to_excel(filename)

        self.stdout.write(
            self.style.SUCCESS(
                f"Export completed: {file_path}"
            )
        )
