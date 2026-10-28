"""Read physical-flow XML while preserving units and publication gaps."""
from datetime import datetime, timedelta, timezone
import math
import re
import xml.etree.ElementTree as ET


def utc(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(timezone.utc)


def parse_flow(xml, source, destination):
    root = ET.fromstring(xml)
    rows = {}
    for series in root.findall('.//{*}TimeSeries'):
        # Check that the returned direction matches the API request.
        if (series.findtext('{*}out_Domain.mRID') != source or
                series.findtext('{*}in_Domain.mRID') != destination):
            raise ValueError('The response has an unexpected flow direction.')
        unit = series.findtext('{*}quantity_Measure_Unit.name')
        curve = series.findtext('{*}curveType')
        if unit != 'MAW' or curve not in ('A01', 'A03'):
            raise ValueError('Unsupported unit or curve type.')
        for period in series.findall('{*}Period'):
            start = utc(period.findtext('{*}timeInterval/{*}start'))
            end = utc(period.findtext('{*}timeInterval/{*}end'))
            resolution = period.findtext('{*}resolution')
            match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?', resolution)
            if not match:
                raise ValueError('Unsupported time resolution.')
            minutes = int(match[1] or 0) * 60 + int(match[2] or 0)
            if minutes <= 0 or (end - start).total_seconds() % (minutes * 60):
                raise ValueError('Invalid interval boundaries.')
            count = int((end - start).total_seconds() / (minutes * 60))
            points = sorted((int(point.findtext('{*}position')),
                             float(point.findtext('{*}quantity')))
                            for point in period.findall('{*}Point'))
            if len({position for position, _ in points}) != len(points):
                raise ValueError('Duplicate positions in a period.')
            for index, (position, power) in enumerate(points):
                if not 1 <= position <= count or not math.isfinite(power) or power < 0:
                    raise ValueError('Invalid position or physical flow value.')
                # A03 holds a value until the next point or the end of its period.
                # A01 describes individual intervals; absent positions stay absent.
                stop = (points[index + 1][0] if index + 1 < len(points) else count + 1) if curve == 'A03' else position + 1
                for step in range(position, stop):
                    instant = start + timedelta(minutes=(step - 1) * minutes)
                    value = (instant + timedelta(minutes=minutes), power, minutes, curve)
                    if instant in rows and rows[instant] != value:
                        raise ValueError('Conflicting time series overlap.')
                    rows[instant] = value
    return [dict(start_utc=t.isoformat(), end_utc=end.isoformat(), power_mw=power,
                 energy_mwh=power * minutes / 60, resolution_minutes=minutes,
                 curve_type=curve) for t, (end, power, minutes, curve) in sorted(rows.items())]
