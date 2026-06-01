import os
import csv
import tempfile
import zipfile
from datetime import datetime, timezone as dt_timezone
from typing import Optional, Callable

from django.conf import settings

from smart_meter.models import SmartMeter, PowerMeasurement, GasMeasurement, SolarMeasurement

BATCH_SIZE = 1000

class MeterDataExporter:
    """Service to export meter data to CSV files in a ZIP archive"""

    def __init__(self, meter: SmartMeter, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the exporter with a meter and optional progress callback

        :param meter: The SmartMeter instance to export data for
        :param progress_callback: Optional callback function to report progress messages
        """
        self.meter = meter
        self.progress_callback = progress_callback

    def export_to_zip(self) -> str:
        """
        Export all measurements for the meter to CSV files in a ZIP archive

        :return: Full path to the saved file
        """
        # Generate filename based on meter name and current UTC timestamp
        timestamp = datetime.now(dt_timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"export_{timestamp}.zip"

        # Construct full file path in media directory
        file_path = os.path.join(settings.MEDIA_ROOT, 'export', self.meter.pk, filename)
        file_dir = os.path.dirname(file_path)

        # Ensure directory exists
        os.makedirs(file_dir, exist_ok=True)

        # Create temporary CSV files
        with tempfile.TemporaryDirectory() as temp_dir:
            power_csv = os.path.join(temp_dir, "power.csv")
            gas_csv = os.path.join(temp_dir, "gas.csv")
            solar_csv = os.path.join(temp_dir, "solar.csv")

            self._export_power(power_csv)
            self._export_gas(gas_csv)
            self._export_solar(solar_csv)

            # Create ZIP archive
            self._log("Creating ZIP archive...")
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(power_csv) and os.path.getsize(power_csv) > 0:
                    zipf.write(power_csv, "power.csv")
                if os.path.exists(gas_csv) and os.path.getsize(gas_csv) > 0:
                    zipf.write(gas_csv, "gas.csv")
                if os.path.exists(solar_csv) and os.path.getsize(solar_csv) > 0:
                    zipf.write(solar_csv, "solar.csv")

        return file_path

    def _export_power(self, file_path: str) -> None:
        """Export power measurements to a CSV file"""
        headers = [
            "timestamp",
            "actual_import",
            "actual_export",
            "total_import_1",
            "total_import_2",
            "total_export_1",
            "total_export_2",
        ]

        qs = (
            PowerMeasurement.objects
            .filter(meter=self.meter)
            .order_by("id")
        )

        self._write_queryset(
            file_path=file_path,
            queryset=qs,
            fields=headers,
            title="Power",
        )

    def _export_gas(self, file_path: str) -> None:
        """Export gas measurements to a CSV file"""
        headers = [
            "timestamp",
            "actual_gas",
            "total_gas",
        ]

        qs = (
            GasMeasurement.objects
            .filter(meter=self.meter)
            .order_by("id")
        )

        self._write_queryset(
            file_path=file_path,
            queryset=qs,
            fields=headers,
            title="Gas",
        )

    def _export_solar(self, file_path: str) -> None:
        """Export solar measurements to a CSV file"""
        headers = [
            "timestamp",
            "actual_solar",
            "total_solar",
        ]

        qs = (
            SolarMeasurement.objects
            .filter(meter=self.meter)
            .order_by("id")
        )

        self._write_queryset(
            file_path=file_path,
            queryset=qs,
            fields=headers,
            title="Solar",
        )

    def _write_queryset(self, file_path: str, queryset, fields, title):
        """Write queryset data to CSV file in batches"""
        self._log(f"{title}: starting export")

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write headers
            writer.writerow(fields)

            processed = 0
            last_pk = 0

            while True:
                batch = list(
                    queryset
                    .filter(pk__gt=last_pk)
                    .values_list(*fields, "pk")[:BATCH_SIZE]
                )

                if not batch:
                    break

                for row in batch:
                    *values, pk = row

                    # Convert timezone-aware datetime to naive UTC for the first field (timestamp)
                    if values and isinstance(values[0], datetime):
                        if values[0].tzinfo is not None:
                            values[0] = values[0].astimezone(dt_timezone.utc).replace(tzinfo=None)

                    writer.writerow(values)
                    last_pk = pk

                processed += len(batch)
                self._log(f"{title}: {processed:,} records exported")

        self._log(f"{title}: export complete ({processed:,} total records)")

    def _log(self, message: str) -> None:
        """Log a progress message if callback is provided"""
        if self.progress_callback:
            self.progress_callback(message)

