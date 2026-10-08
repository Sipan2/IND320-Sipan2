"""Validate downloaded intervals and prepare JSON lines for Spark."""
import json
from pathlib import Path
from download_entsoe import AREAS, ROOT
from transfer_data import parse_flow, utc


def prepare():
    folder = ROOT / 'entsoe_raw'
    manifest = json.loads((folder / 'manifest.json').read_text())
    if len(manifest) != 9 * 2 * 24:
        raise ValueError('The two-year download is not complete.')
    report = []
    output = folder / 'intervals.jsonl'
    with output.open('w') as destination:
        for request in manifest:
            norway, neighbour = request['connection'].split(' - ')
            source, target = (norway, neighbour) if request['direction'] == 'export' else (neighbour, norway)
            start, end = utc(request['start']), utc(request['end'])
            rows = [] if request['status'] != 'downloaded' else parse_flow(
                (folder / request['file']).read_text(), AREAS[source], AREAS[target])
            previous_end = start
            seconds = 0
            count = 0
            for row in rows:
                left, right = max(utc(row['start_utc']), start), min(utc(row['end_utc']), end)
                if right <= left:
                    continue
                if left < previous_end:
                    raise ValueError('Overlapping intervals would double-count energy.')
                duration = (right - left).total_seconds()
                row.update(connection=request['connection'], direction=request['direction'],
                           month=request['start'][:7], start_utc=left.isoformat(),
                           end_utc=right.isoformat(), energy_mwh=row['power_mw'] * duration / 3600)
                destination.write(json.dumps(row) + '\n')
                previous_end = right
                seconds += duration
                count += 1
            report.append(dict(connection=request['connection'], direction=request['direction'],
                               month=request['start'][:7], intervals=count,
                               observed_hours=seconds / 3600,
                               expected_hours=(end - start).total_seconds() / 3600,
                               status=request['status']))
    (folder / 'coverage.json').write_text(json.dumps(report, indent=2))
    print('Prepared', sum(r['intervals'] for r in report), 'intervals.')
    print('Months with incomplete coverage:', sum(r['observed_hours'] != r['expected_hours'] for r in report))
    return output, report


if __name__ == '__main__':
    prepare()
