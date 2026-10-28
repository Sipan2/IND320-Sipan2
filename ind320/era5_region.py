"""Cache ERA5 grid series and compute means over the original random sample."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class QuotaBudgetReached(RuntimeError):
    """The conservative local API budget is exhausted; resume later."""


def reserve_call(cache, weight):
    """Record usage before a request, including requests that later fail.

    The public server counts max(1, variables/10 * days/14) per location.
    Local limits leave headroom below the published 600/5,000/10,000 limits.
    Server-side 429 responses always take precedence over this local ledger.
    """
    ledger = cache / 'usage.json'
    records = json.loads(ledger.read_text()) if ledger.exists() else []
    now = time.time()
    records = [r for r in records if now - r['time'] < 86400]
    for seconds, limit in [(3600, 4500), (86400, 9000)]:
        if sum(r['weight'] for r in records if now - r['time'] < seconds) + weight > limit:
            raise QuotaBudgetReached(f'Local {seconds}-second budget reached. Cached data are retained.')
    recent = [r for r in records if now - r['time'] < 60]
    if sum(r['weight'] for r in recent) + weight > 540:
        delay = max(0, 60 - (now - min(r['time'] for r in recent))) + 0.1
        time.sleep(min(delay, 60))
        return reserve_call(cache, weight)
    records.append({'time': time.time(), 'weight': weight})
    ledger.write_text(json.dumps(records) + '\n')


def regional_weather(region, start_date, end_date, *, region_type='electricity',
                     cache_dir=ROOT / 'weather_cache', progress=None):
    """Return complete hourly means for all saved points, or raise.

    ERA5 has a regular 0.25-degree grid. Nearest-cell selection is explicit,
    and elevation=nan disables point-specific temperature downscaling. Points
    selecting the same cell therefore share a time series. A representative
    original coordinate is requested for each occupied cell. The returned cell
    must match the expected grid centre before it is accepted. Cell means are
    weighted by the number of original points, rather than equally by cell.
    """
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if (start.tzinfo is not None or end.tzinfo is not None or end < start
            or start != start.normalize() or end != end.normalize()):
        raise ValueError('Use ordered timezone-free calendar dates.')
    sample_path = ROOT / 'data/regions' / ('national_locations.csv' if region_type == 'national' else 'sampled_locations.csv')
    points = pd.read_csv(sample_path)
    selected = points.loc[points.region.eq(region) & points.region_type.eq(region_type)].copy()
    if len(selected) != 1000 or selected.point_id.nunique() != 1000:
        raise ValueError('A complete sample of 1,000 distinct point IDs is required.')
    selected['cell_lat'] = np.floor(selected.latitude * 4 + 0.5) / 4
    selected['cell_lon'] = np.floor(selected.longitude * 4 + 0.5) / 4
    groups = list(selected.groupby(['cell_lat', 'cell_lon'], sort=True))
    expected = pd.date_range(start, end + pd.Timedelta(days=1), freq='h', inclusive='left', tz='UTC')
    numerator = np.zeros((len(expected), 2))
    valid_weight = np.zeros((len(expected), 2), dtype=int)
    cache = Path(cache_dir)
    cache.mkdir(exist_ok=True, parents=True)
    manifest = []
    weight_per_call = max(1, 2 / 10 * ((end - start).days + 1) / 14)
    for index, ((lat, lon), group) in enumerate(groups):
        representative = group.iloc[0]
        parameters = {'latitude': float(representative.latitude),
                      'longitude': float(representative.longitude),
                      'start_date': start.date().isoformat(), 'end_date': end.date().isoformat(),
                      'hourly': 'temperature_2m,precipitation', 'models': 'era5',
                      'timezone': 'UTC', 'temperature_unit': 'celsius', 'precipitation_unit': 'mm',
                      'cell_selection': 'nearest', 'elevation': 'nan'}
        url = 'https://archive-api.open-meteo.com/v1/archive?' + urlencode(parameters)
        key = hashlib.sha256(url.encode()).hexdigest()
        target = cache / f'{key}.json'
        if target.exists():
            record = json.loads(target.read_text())
        else:
            reserve_call(cache, weight_per_call)
            try:
                with urlopen(url, timeout=120) as response:
                    data = json.load(response)
            except HTTPError as error:
                if error.code == 429:
                    raise QuotaBudgetReached('Open-Meteo rate limit reached. Resume from cache later.') from error
                raise
            record = {'request': parameters, 'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'response': data}
        data = record['response']
        if data.get('error'):
            raise ValueError(data.get('reason', 'Open-Meteo error'))
        if not np.allclose([data['latitude'], data['longitude']], [lat, lon], atol=1e-5, rtol=0):
            raise ValueError('Returned cell differs from expected ERA5 grid. Do not deduplicate these points.')
        if data['hourly_units']['temperature_2m'] != '°C' or data['hourly_units']['precipitation'] != 'mm':
            raise ValueError('Unexpected units.')
        frame = pd.DataFrame(data['hourly'])
        if not pd.DatetimeIndex(pd.to_datetime(frame.time, utc=True)).equals(expected):
            raise ValueError('Incomplete, duplicate or shifted hourly timestamps.')
        values = frame[['temperature_2m', 'precipitation']].to_numpy(dtype=float)
        if np.isinf(values).any() or (values[:, 1][np.isfinite(values[:, 1])] < 0).any():
            raise ValueError('Invalid weather measurements.')
        if not target.exists():
            target.write_text(json.dumps(record) + '\n')
        good = np.isfinite(values)
        numerator += np.where(good, values, 0) * len(group)
        valid_weight += good.astype(int) * len(group)
        manifest.append({'cell_latitude': lat, 'cell_longitude': lon, 'sample_weight': len(group),
                         'point_ids': group.point_id.tolist(), 'request_hash': key,
                         'response_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        if progress:
            progress(index + 1, len(groups))
        # A short delay also limits request bursts, independently of the ledger.
        time.sleep(0.15)
    # Never silently turn partial spatial coverage into an apparently full mean.
    if not np.all(valid_weight == len(selected)):
        raise ValueError('At least one hourly mean has incomplete spatial coverage.')
    means = numerator / valid_weight
    result = pd.DataFrame({'time_utc': expected, 'temperature_2m': means[:, 0],
                           'precipitation': means[:, 1], 'sample_count': len(selected),
                           'grid_cell_count': len(groups)})
    output = ROOT / 'data/weather'
    output.mkdir(exist_ok=True, parents=True)
    stem = f'{region_type}_{region}_{start.date()}_{end.date()}'
    result.to_csv(output / f'{stem}.csv', index=False)
    (output / f'{stem}.source.json').write_text(json.dumps({
        'region': region, 'region_type': region_type, 'start_date': str(start.date()),
        'end_date': str(end.date()), 'model': 'ERA5', 'timezone': 'UTC',
        'elevation_downscaling': False, 'cell_selection': 'nearest',
        'sample_sha256': hashlib.sha256(sample_path.read_bytes()).hexdigest(),
        'weighting': 'Each original sampled point has equal weight; occupied cells retain their point counts.',
        'source': 'https://open-meteo.com/en/docs/historical-weather-api',
        'licence': 'CC BY 4.0; Open-Meteo and Copernicus ERA5', 'cells': manifest,
    }, indent=2) + '\n')
    return result


if __name__ == '__main__':
    data = regional_weather('NO3', '2024-01-01', '2024-12-31',
                            progress=lambda done, total: print(f'ERA5 cells {done}/{total}', flush=True) if done % 10 == 0 or done == total else None)
    print('Complete hourly regional means:', len(data), flush=True)
