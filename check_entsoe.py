"""Make a small access check before attempting the two-year download."""
from getpass import getpass
from pathlib import Path
import pandas as pd
from entsoe import EntsoeRawClient
from entsoe.exceptions import NoMatchingDataError
from requests.exceptions import RequestException


def main():
    # A hidden prompt keeps the API token out of code and notebook outputs.
    token = getpass('ENTSO-E API token: ').strip()
    if not token:
        raise SystemExit('No token supplied. Nothing was requested.')
    client = EntsoeRawClient(api_key=token)
    start = pd.Timestamp('2026-10-01', tz='Europe/Oslo')
    end = start + pd.DateOffset(days=1)
    folder = Path(__file__).parent / 'entsoe_raw'
    folder.mkdir(exist_ok=True)
    # A border request returns one direction; reverse the areas for imports.
    for source, destination, direction in [('NO_2', 'DK_1', 'export'), ('DK_1', 'NO_2', 'import')]:
        try:
            xml = client.query_crossborder_flows(source, destination, start=start, end=end)
        except NoMatchingDataError:
            print(f'No matching {direction} data for this test day. Do not treat this as zero flow.')
            continue
        except RequestException:
            # HTTP error messages may include the URL and its token.
            raise SystemExit('The API request failed. Check access, the token and the connection.') from None
        (folder / f'no2_dk1_{direction}_2026-10-01.xml').write_text(xml)
        print(f'Saved the {direction} response. Inspect its units, intervals and coverage before calculating totals.')


if __name__ == '__main__':
    main()
