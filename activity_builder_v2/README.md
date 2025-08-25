# Activity Builder v2

Enhanced activity analysis tools for cycling and fitness data from Strava exports.

## Contents

- `activity_analyzer.py` - Main script for analyzing individual activities
- `test_setup.py` - Test script to verify setup and list available activities
- `README_activity_analyzer.md` - Detailed documentation for the activity analyzer
- `activity_analyzer_requirements.txt` - Dependencies (none required)

## Quick Start

1. Set your birth year environment variable:
   ```bash
   export USER_BIRTHYEAR=1990  # Replace with your birth year
   ```

2. (Optional) Set custom data path:
   ```bash
   export STRAVA_DATA_PATH="/path/to/your/strava/data"  # Custom data directory
   ```

3. Test the setup:
   ```bash
   python test_setup.py
   ```

4. Analyze an activity:
   ```bash
   # Basic analysis
   python activity_analyzer.py <activity_id>
   
   # With context (activities from same week/month/year)
   python activity_analyzer.py <activity_id> --context month
   ```

## Features

- **Activity Details**: Extracts basic activity information (time, distance, speed, elevation)
- **Heart Rate Analysis**: Calculates max HR based on age and analyzes HR zones
- **HR Zone Distribution**: Shows time spent in each training zone
- **Relative Effort**: Calculates training load based on HR zone intensity
- **Contextual Analysis**: Compare with activities from same week/month/year
- **LLM-Ready Output**: Single-line summary format optimized for AI analysis
- **JSON Export**: Detailed analysis saved to file

## Data Requirements

The script expects data in the following structure. By default, it looks for data in `../activity_fetcher/data/`, but you can customize this with the `STRAVA_DATA_PATH` environment variable:

```
[STRAVA_DATA_PATH or ../activity_fetcher/data/]
├── metadata/
│   └── activity_index.json
└── individual_activities/
    ├── {activity_id}_{date}_{name}.json
    ├── {activity_id}_{date}_{name}_streams_heartrate.json
    ├── {activity_id}_{date}_{name}_streams_time.json
    └── {activity_id}_{date}_{name}_streams_distance.json
```

## Documentation

See `README_activity_analyzer.md` for complete documentation and usage examples.
