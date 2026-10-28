"""Area selection for the assignment's weather calculations.

These are the course's administrative polygon unions, not surveyed catchments.
The NVE catalogue's four-area descriptions are retained separately as source data.
"""
VASS_WEATHER_REGIONS = {1: 'EAST', 2: 'WEST', 3: 'NORTH'}
PRECIPITATION_MEMBERS = {'EAST': ('RS', 'RØ'), 'WEST': ('RV',), 'NORTH': ('RM', 'RN')}


def weather_region(family, number):
    """Resolve a reservoir selection to its saved weather sampling region."""
    if family == 'EL' and number in range(1, 6):
        return 'electricity', f'NO{number}'
    if family == 'NO' and number == 0:
        return 'national', 'NORWAY'
    if family == 'VASS' and number in VASS_WEATHER_REGIONS:
        return 'assignment_precipitation', VASS_WEATHER_REGIONS[number]
    raise ValueError(f'No weather sampling region for {family} {number}.')
