# Activity Analyzer

A Python script that analyzes cycling/fitness activity data from Strava exports, providing detailed insights including heart rate zone analysis and relative effort calculations.

## Features

- **Activity Details**: Extracts basic activity information (time, distance, speed, elevation)
- **Heart Rate Analysis**: Calculates max HR based on age and analyzes HR zones
- **HR Zone Distribution**: Shows time spent in each training zone
- **Relative Effort**: Calculates training load based on HR zone intensity
- **Comprehensive Summary**: Provides formatted output with all key metrics

## Setup

1. Set your birth year as an environment variable:
   ```bash
   export USER_BIRTHYEAR=1990  # Replace with your birth year
   ```

2. (Optional) Set custom data path:
   ```bash
   export STRAVA_DATA_PATH="/path/to/your/strava/data"  # Custom data directory
   ```
   
   If not set, the script will look for data in `../activity_fetcher/data/` by default.

3. Ensure your activity data is in the expected directory structure:
   ```
   [STRAVA_DATA_PATH or default ../activity_fetcher/data/]
   ├── metadata/
   │   └── activity_index.json
   └── individual_activities/
       ├── {activity_id}_{date}_{name}.json
       ├── {activity_id}_{date}_{name}_streams_heartrate.json
       ├── {activity_id}_{date}_{name}_streams_time.json
       └── {activity_id}_{date}_{name}_streams_distance.json
   ```

## Usage

```bash
python activity_analyzer.py <activity_id> [--context {week,month,year}]
```

### Options

- `activity_id`: The ID of the activity to analyze (required)
- `--context`: Include summary of activities from the same timeframe (optional)
  - `week`: Activities from the same week (Monday to Sunday)
  - `month`: Activities from the same month
  - `year`: Activities from the same year

### Examples

```bash
# Basic analysis
python activity_analyzer.py 12047985131

# Analysis with weekly context
python activity_analyzer.py 12047985131 --context week

# Analysis with monthly context  
python activity_analyzer.py 12047985131 --context month

# Analysis with yearly context
python activity_analyzer.py 12047985131 --context year
```

## Heart Rate Zones

The script uses standard 5-zone heart rate training model:

| Zone | Name | % of Max HR | Effort Multiplier |
|------|------|-------------|-------------------|
| 1 | Active Recovery | 50-60% | 1.0x |
| 2 | Aerobic Base | 60-70% | 2.0x |
| 3 | Aerobic | 70-80% | 3.0x |
| 4 | Lactate Threshold | 80-90% | 4.0x |
| 5 | VO2 Max | 90-100% | 5.0x |

## Output

The script provides:

1. **Console Output**: Single-line summary optimized for LLM analysis
2. **JSON File**: Detailed analysis saved as `activity_analysis_{activity_id}.json` (includes the summary string)

### Sample Output

```
Activity Summary (LLM-ready):
--------------------------------------------------------------------------------
Activity: Morning Ride (Ride) on 2024-08-02 - Distance: 27.39km, Time: 01:56:44 (moving) / 01:56:44 (total), Avg_speed: 14.04km/h, Elevation: 78m, HR_zones:[Active_Recovery:13.1%,Aerobic_Base:44.0%,Aerobic:38.8%,Lactate_Threshold:4.1%], avg_HR:128.4bpm, relative_effort:318.2pts
--------------------------------------------------------------------------------

Month Context Summary:
--------------------------------------------------------------------------------
Month_summary: 8activities, 245.2km_total, 30.7km_avg, 17:45:32_total_time, types:[Ride:8activities/245.2km]
--------------------------------------------------------------------------------

Recent activities in the same month:
  1. Evening Ride - 15.2km on 2024-08-23
  2. Afternoon Ride - 29.5km on 2024-08-17
  3. Morning Ride - 27.1km on 2024-08-09
  4. Morning Ride - 27.4km on 2024-08-02
  5. Morning Ride - 21.5km on 2024-08-06
```

This shows both the individual activity analysis and contextual information about other activities in the specified timeframe.

## Heart Rate Calculation

Maximum heart rate is calculated using the formula: **220 - age**

Where age is calculated from the current year minus the birth year set in the `USER_BIRTHYEAR` environment variable.

## Environment Variables

The script uses the following environment variables:

- **`USER_BIRTHYEAR`** (Required): Your birth year (e.g., 1985) used to calculate maximum heart rate
- **`STRAVA_DATA_PATH`** (Optional): Custom path to your Strava data directory. If not set, defaults to `../activity_fetcher/data/`

Example setup:
```bash
export USER_BIRTHYEAR=1985
export STRAVA_DATA_PATH="/path/to/your/strava/data"
```

## Error Handling

The script handles various error conditions:

- Missing environment variable
- Invalid activity ID
- Missing activity files
- Missing heart rate data
- Data format issues

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Files Generated

- `activity_analysis_{activity_id}.json`: Detailed analysis in JSON format
