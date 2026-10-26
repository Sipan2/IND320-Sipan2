"""Download NVE boundaries and sample locations uniformly by projected area."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parent
LAYERS = {
    'electricity': ('Omradekonsesjoner', 8, 'ElSpotOmr'),
    'nve_regions': ('Administrasjon2', 0, 'REGION'),
}


def download_boundaries(directory=ROOT / 'data' / 'regions'):
    """Cache original GeoJSON and export equivalent shapefiles for local use.

    NVE's separate shapefile download portal was unavailable when this workflow
    was prepared. These exports come from NVE's published Atlas map layers.
    Administrative regions are kept under their original names: their mapping
    to reservoir precipitation regions requires a separate documented decision.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, (service, layer, field) in LAYERS.items():
        base = f'https://gis3.nve.no/map/rest/services/Mapservices/{service}/MapServer/{layer}'
        query = urlencode({'where': '1=1', 'outFields': field,
                           'returnGeometry': 'true', 'outSR': 4326, 'f': 'geojson'})
        path = directory / f'{name}.geojson'
        record_path = directory / f'{name}.source.json'
        if not path.exists():
            with urlopen(base + '/query?' + query, timeout=120) as response:
                raw = response.read()
            payload = json.loads(raw)
            if payload.get('type') != 'FeatureCollection' or not payload.get('features'):
                raise ValueError(f'NVE did not return a feature collection: {name}')
            if payload.get('exceededTransferLimit'):
                raise ValueError('NVE truncated the geometry response.')
            path.write_bytes(raw)
            record_path.write_text(json.dumps({
                'source': base, 'query': query,
                'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(raw).hexdigest(),
                'format_note': 'Original GeoJSON; shapefiles exported locally.',
            }, indent=2) + '\n')
        frame = gpd.read_file(path)
        expected = {'NO1', 'NO2', 'NO3', 'NO4', 'NO5'} if name == 'electricity' else {'RS', 'RØ', 'RV', 'RM', 'RN'}
        if set(frame[field]) != expected or len(frame) != len(expected):
            raise ValueError(f'Unexpected or duplicate area identifiers: {name}')
        if frame.crs is None or frame.geometry.is_empty.any() or not frame.geometry.is_valid.all():
            raise ValueError(f'Missing CRS or invalid region geometry: {name}')
        # Short field names avoid the shapefile format's ten-character limit.
        export = frame[[field, 'geometry']].rename(columns={field: 'region'})
        target = directory / name
        target.mkdir(exist_ok=True)
        export.to_crs(25833).to_file(target / f'{name}.shp', encoding='UTF-8')
        manifest[name] = json.loads(record_path.read_text())
    return manifest


def sample_region(geometry, count=1000, seed=320):
    """Return reproducible uniform samples from an EPSG:3035 polygon.

    Rejection sampling honours islands and polygon holes. Sampling in an
    equal-area CRS avoids the latitude bias of uniform longitude/latitude.
    """
    if count < 1 or int(count) != count:
        raise ValueError('count must be a positive integer')
    if geometry.is_empty or not geometry.is_valid or geometry.area <= 0:
        raise ValueError('A valid polygon with positive area is required.')
    rng = np.random.default_rng(seed)
    xmin, ymin, xmax, ymax = geometry.bounds
    selected = []
    remaining = int(count)
    for _ in range(10000):
        candidates = shapely.points(rng.uniform(xmin, xmax, max(remaining * 4, 256)),
                                    rng.uniform(ymin, ymax, max(remaining * 4, 256)))
        accepted = candidates[shapely.contains(geometry, candidates)][:remaining]
        selected.extend(accepted)
        remaining -= len(accepted)
        if not remaining:
            return gpd.GeoSeries(selected, crs=3035)
    raise ValueError('Sampling did not converge; check the region geometry.')


def prepare_samples(directory=ROOT / 'data' / 'regions', count=1000, seed=320):
    """Sample each original region, preserving source identifiers in the CSV."""
    directory = Path(directory)
    rows = []
    for name, (_, _, field) in LAYERS.items():
        frame = gpd.read_file(directory / f'{name}.geojson').to_crs(3035)
        for identifier in sorted(frame[field]):
            polygon = frame.loc[frame[field].eq(identifier)].geometry.iloc[0]
            # Derive an independent stable seed without Python's randomised hash.
            area_seed = int.from_bytes(hashlib.sha256(f'{seed}:{name}:{identifier}'.encode()).digest()[:4], 'big')
            sampled = sample_region(polygon, count, area_seed)
            if not sampled.within(polygon).all():
                raise AssertionError('A sampled point lies outside its source polygon.')
            geographic = sampled.to_crs(4326)
            rows.append(pd.DataFrame({'region_type': name, 'region': identifier,
                                     'point_id': range(count),
                                     'longitude': geographic.x, 'latitude': geographic.y,
                                     'seed': seed}))
    points = pd.concat(rows, ignore_index=True)
    points.to_csv(directory / 'sampled_locations.csv', index=False)
    return points


def prepare_assignment_regions(directory=ROOT / 'data' / 'regions', count=1000, seed=320):
    """Build the three unions explicitly described in the Canvas assignment.

    These names deliberately do not assert a mapping to VASS1–VASS4: the API
    catalogue currently lists four VASS identifiers, while observations have
    three. Sample the dissolved polygon rather than concatenate equally sized
    component samples, which would overweight the smaller component region.
    """
    directory = Path(directory)
    source = gpd.read_file(directory / 'nve_regions.geojson').to_crs(3035)
    combinations = {'EAST': ['RS', 'RØ'], 'WEST': ['RV'], 'NORTH': ['RM', 'RN']}
    regions, rows = [], []
    for identifier, members in combinations.items():
        polygon = source.loc[source.REGION.isin(members)].geometry.union_all()
        regions.append({'region': identifier, 'members': '+'.join(members), 'geometry': polygon})
        area_seed = int.from_bytes(hashlib.sha256(f'{seed}:assignment_precipitation:{identifier}'.encode()).digest()[:4], 'big')
        sampled = sample_region(polygon, count, area_seed).to_crs(4326)
        rows.append(pd.DataFrame({'region_type': 'assignment_precipitation', 'region': identifier,
                                 'point_id': range(count), 'longitude': sampled.x,
                                 'latitude': sampled.y, 'seed': seed}))
    gpd.GeoDataFrame(regions, crs=3035).to_crs(4326).to_file(directory / 'assignment_precipitation.geojson', driver='GeoJSON')
    original = pd.read_csv(directory / 'sampled_locations.csv')
    original = original.loc[original.region_type.ne('assignment_precipitation')]
    result = pd.concat([original] + rows, ignore_index=True)
    result.to_csv(directory / 'sampled_locations.csv', index=False)
    (directory / 'assignment_precipitation.source.json').write_text(json.dumps({
        'source': 'https://nmbu.instructure.com/courses/14185/assignments/59074',
        'grouping': combinations, 'sampling_crs': 'EPSG:3035', 'seed': seed,
        'vass_mapping': 'Unresolved: catalogue lists VASS1–VASS4; observations contain VASS1–VASS3.',
        'method': 'Dissolve component polygons before sampling 1,000 points per combined region.',
    }, ensure_ascii=False, indent=2) + '\n')
    return result


def prepare_national_sample(directory=ROOT / 'data' / 'regions', count=1000, seed=320):
    """Sample Norway's covered land area from the union of electricity areas."""
    directory = Path(directory)
    source = gpd.read_file(directory / 'electricity.geojson').to_crs(3035)
    polygon = source.geometry.union_all()
    area_seed = int.from_bytes(hashlib.sha256(f'{seed}:national:NORWAY'.encode()).digest()[:4], 'big')
    sampled = sample_region(polygon, count, area_seed).to_crs(4326)
    result = pd.DataFrame({'region_type': 'national', 'region': 'NORWAY', 'point_id': range(count),
                           'longitude': sampled.x, 'latitude': sampled.y, 'seed': seed})
    result.to_csv(directory / 'national_locations.csv', index=False)
    return result


if __name__ == '__main__':
    download_boundaries()
    prepare_samples()
    points = prepare_assignment_regions()
    prepare_national_sample()
    print(points.groupby(['region_type', 'region']).size().to_string())
