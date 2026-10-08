"""Download two complete years of physical cross-border flows, without saving the key."""
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo
import json
import time
import xml.etree.ElementTree as ET

# Bidding zones from the ENTSO-E area codes used by entsoe-py.
AREAS = {
    'NO1': '10YNO-1--------2', 'NO2': '10YNO-2--------T',
    'NO3': '10YNO-3--------J', 'NO4': '10YNO-4--------9',
    'SE1': '10Y1001A1001A44P', 'SE2': '10Y1001A1001A45N',
    'SE3': '10Y1001A1001A46L', 'FI': '10YFI-1--------U',
    'DK1': '10YDK-1--------W', 'NL': '10YNL----------L',
    'DE-LU': '10Y1001A1001A82H', 'GB': '10YGB----------A',
}
BORDERS = [('NO1', 'SE3'), ('NO2', 'DK1'), ('NO2', 'NL'),
           ('NO2', 'DE-LU'), ('NO2', 'GB'), ('NO3', 'SE2'),
           ('NO4', 'SE1'), ('NO4', 'SE2'), ('NO4', 'FI')]
ROOT = Path(__file__).resolve().parent


def download(token, progress=lambda message: None):
    # Use the last 24 complete months: 1 October 2024 to 1 October 2026.
    # Boundaries follow Norwegian local time; API parameters use UTC.
    folder = ROOT / 'entsoe_raw'
    folder.mkdir(exist_ok=True)
    boundaries = [datetime(2024 + (9 + i) // 12, (9 + i) % 12 + 1,
                           1, tzinfo=ZoneInfo('Europe/Oslo')) for i in range(25)]
    manifest = []
    for norway, neighbour in BORDERS:
        for direction, source, destination in [('export', norway, neighbour),
                                                ('import', neighbour, norway)]:
            for start, end in zip(boundaries, boundaries[1:]):
                name = f'{norway}_{neighbour}_{direction}_{start:%Y-%m}.xml'
                target = folder / name
                record = dict(connection=f'{norway} - {neighbour}', direction=direction,
                              start=start.isoformat(), end=end.isoformat(), file=name)
                progress(f'{norway} - {neighbour}: {direction}, {start:%Y-%m}')
                if target.exists():
                    record['status'] = 'downloaded'
                else:
                    query = urlencode(dict(securityToken=token, documentType='A11',
                        out_Domain=AREAS[source], in_Domain=AREAS[destination],
                        periodStart=start.astimezone(ZoneInfo('UTC')).strftime('%Y%m%d%H%M'),
                        periodEnd=end.astimezone(ZoneInfo('UTC')).strftime('%Y%m%d%H%M')))
                    for attempt in range(3):
                        try:
                            with urlopen('https://web-api.tp.entsoe.eu/api?' + query, timeout=90) as response:
                                raw = response.read()
                            root = ET.fromstring(raw)
                            if not root.findall('.//{*}TimeSeries'):
                                raise ValueError('Response contains no time series')
                            target.write_bytes(raw)
                            record['status'] = 'downloaded'
                            break
                        except HTTPError as error:
                            # Do not log error URLs: the URL contains the API token.
                            body = error.read()
                            if error.code == 400 and b'No matching data' in body:
                                record['status'] = 'no publication'
                                break
                            if error.code in (401, 403):
                                raise RuntimeError('API access was refused. Check the new token.') from None
                            if attempt == 2:
                                raise RuntimeError(f'HTTP {error.code} for {name}') from None
                            time.sleep(3 * (attempt + 1))
                        except (URLError, TimeoutError):
                            if attempt == 2:
                                raise RuntimeError(f'Connection failed for {name}') from None
                            time.sleep(3 * (attempt + 1))
                    time.sleep(0.25)
                manifest.append(record)
                (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    progress('Download complete. The API token has not been saved.')
    return manifest


if __name__ == '__main__':
    from getpass import getpass
    download(getpass('ENTSO-E API token: ').strip(), print)
