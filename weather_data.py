"""Read hourly ERA5 weather for saved regional sample locations."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent


def download_weather(region, start_date, end_date, *, region_type='electricity',
                     point_ids=None, cache_dir=ROOT / 'weather_cache'):
    """Download temperature and precipitation with inclusive UTC date bounds.

    By default, use every saved location in the region. ``point_ids`` restricts
    a diagnostic request to selected points; such a result is not a regional
    mean. Each response is cached independently so interrupted runs can resume.
    Requests are sequential. API quota planning is required before a full year
    is downloaded for all 1,000 locations.
    """
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if start.tzinfo is not None or end.tzinfo is not None or start != start.normalize() or end != end.normalize() or end < start:
        raise ValueError('Use ordered, timezone-free ISO calendar dates.')
    points = pd.read_csv(ROOT / 'data' / 'regions' / 'sampled_locations.csv')
    selected = points.loc[points.region.eq(region) & points.region_type.eq(region_type)]
    if point_ids is not None:
        wanted = set(point_ids)
        selected = selected.loc[selected.point_id.isin(wanted)]
        if set(selected.point_id) != wanted:
            raise ValueError('One or more point IDs do not belong to this region.')
    if selected.empty:
        raise ValueError('No locations match this region and point selection.')
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    expected = pd.date_range(start, end + pd.Timedelta(days=1), freq='h', inclusive='left', tz='UTC')
    frames = []
    for point in selected.itertuples(index=False):
        parameters = {'latitude': point.latitude, 'longitude': point.longitude,
                      'start_date': start.date().isoformat(), 'end_date': end.date().isoformat(),
                      'hourly': 'temperature_2m,precipitation', 'models': 'era5',
                      'timezone': 'UTC', 'temperature_unit': 'celsius', 'precipitation_unit': 'mm'}
        url = 'https://archive-api.open-meteo.com/v1/archive?' + urlencode(parameters)
        key = hashlib.sha256(url.encode()).hexdigest()
        target = cache_dir / f'{key}.json'
        if target.exists():
            record = json.loads(target.read_text())
            data = record['response']
        else:
            with urlopen(url, timeout=120) as response:
                data = json.load(response)
            if data.get('error'):
                raise ValueError(data.get('reason', 'Open-Meteo returned an error.'))
        units = data['hourly_units']
        if units['temperature_2m'] != '°C' or units['precipitation'] != 'mm':
            raise ValueError('Unexpected weather units.')
        frame = pd.DataFrame(data['hourly']).rename(columns={'time': 'time_utc'})
        frame['time_utc'] = pd.to_datetime(frame.time_utc, utc=True)
        if not pd.DatetimeIndex(frame.time_utc).equals(expected):
            raise ValueError('The response has incomplete or duplicate hourly timestamps.')
        if (frame.precipitation.dropna() < 0).any():
            raise ValueError('Negative precipitation is invalid.')
        if not target.exists():
            target.write_text(json.dumps({'request': parameters, 'response': data}) + '\n')
        frame['point_id'] = point.point_id
        frame['region'] = region
        frame['requested_latitude'] = point.latitude
        frame['requested_longitude'] = point.longitude
        frame['grid_latitude'] = data['latitude']
        frame['grid_longitude'] = data['longitude']
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)
