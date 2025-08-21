#!/usr/bin/env python3
"""
Quick Strava Activity Stats Calculator

A simplified version for quick statistical analysis of Strava activities.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

def load_strava_data(data_path):
    """Load all Strava activity JSON files and their stream data."""
    activities = []
    streams = {}
    json_files = list(Path(data_path).glob("*.json"))
    
    # Separate activity files and stream files
    activity_files = [f for f in json_files if "_streams_" not in f.name]
    stream_files = [f for f in json_files if "_streams_" in f.name]
    
    print(f"Found {len(json_files)} total JSON files")
    print(f"Loading {len(activity_files)} activity files...")
    print(f"Loading {len(stream_files)} stream files...")
    
    # Load activities
    for file_path in activity_files:
        try:
            with open(file_path, 'r') as f:
                activity = json.load(f)
                activities.append(activity)
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")
    
    # Load stream data
    for file_path in stream_files:
        try:
            with open(file_path, 'r') as f:
                stream_data = json.load(f)
                activity_id = stream_data.get('activity_id')
                stream_type = stream_data.get('stream_type')
                
                if activity_id not in streams:
                    streams[activity_id] = {}
                streams[activity_id][stream_type] = stream_data['data']
        except Exception as e:
            print(f"Error loading stream {file_path.name}: {e}")
    
    df = pd.DataFrame(activities)
    
    # Add stream data statistics to activities
    if not df.empty and streams:
        df = add_stream_stats(df, streams)
    
    return df

def add_stream_stats(df, streams):
    """Add stream data statistics to the activities dataframe."""
    # Initialize new columns
    df['hr_data_points'] = 0
    df['hr_avg_detailed'] = np.nan
    df['hr_max_detailed'] = np.nan
    df['hr_min_detailed'] = np.nan
    df['distance_data_points'] = 0
    df['time_data_points'] = 0
    df['position_data_points'] = 0
    
    for idx, row in df.iterrows():
        activity_id = row['id']
        if activity_id in streams:
            activity_streams = streams[activity_id]
            
            # Heart rate stream analysis
            if 'heartrate' in activity_streams:
                hr_data = activity_streams['heartrate']
                if hr_data and any(hr > 0 for hr in hr_data):
                    valid_hr = [hr for hr in hr_data if hr > 0]
                    df.at[idx, 'hr_data_points'] = len(hr_data)
                    df.at[idx, 'hr_avg_detailed'] = np.mean(valid_hr)
                    df.at[idx, 'hr_max_detailed'] = max(valid_hr)
                    df.at[idx, 'hr_min_detailed'] = min(valid_hr)
            
            # Distance stream
            if 'distance' in activity_streams:
                df.at[idx, 'distance_data_points'] = len(activity_streams['distance'])
            
            # Time stream
            if 'time' in activity_streams:
                df.at[idx, 'time_data_points'] = len(activity_streams['time'])
            
            # Position stream (latlng)
            if 'latlng' in activity_streams:
                df.at[idx, 'position_data_points'] = len(activity_streams['latlng'])
    
    return df

def calculate_quick_stats(df):
    """Calculate quick statistics including stream data analysis."""
    # Data preprocessing
    df['distance_km'] = df['distance'] / 1000
    df['moving_time_hours'] = df['moving_time'] / 3600
    df['speed_kmh'] = df['average_speed'] * 3.6
    df['start_date'] = pd.to_datetime(df['start_date_local'])
    
    # Basic stats
    total_activities = len(df)
    total_distance = df['distance_km'].sum()
    total_time = df['moving_time_hours'].sum()
    avg_speed = df['speed_kmh'].mean()
    
    # Stream data stats
    activities_with_hr_streams = (df['hr_data_points'] > 0).sum()
    activities_with_gps_streams = (df['position_data_points'] > 0).sum()
    avg_hr_from_streams = df['hr_avg_detailed'].mean()
    
    # By activity type
    type_stats = df.groupby('type').agg({
        'distance_km': ['count', 'sum', 'mean'],
        'moving_time_hours': 'sum',
        'speed_kmh': 'mean',
        'hr_data_points': 'sum',
        'hr_avg_detailed': 'mean'
    }).round(2)
    
    # Date range
    date_range = f"{df['start_date'].min().strftime('%Y-%m-%d')} to {df['start_date'].max().strftime('%Y-%m-%d')}"
    
    return {
        'total_activities': total_activities,
        'total_distance_km': round(total_distance, 1),
        'total_time_hours': round(total_time, 1),
        'average_speed_kmh': round(avg_speed, 1),
        'date_range': date_range,
        'activity_types': df['type'].value_counts().to_dict(),
        'by_type': type_stats,
        'stream_stats': {
            'activities_with_hr_streams': activities_with_hr_streams,
            'activities_with_gps_streams': activities_with_gps_streams,
            'avg_hr_from_streams': round(avg_hr_from_streams, 1) if not pd.isna(avg_hr_from_streams) else None,
            'total_hr_data_points': df['hr_data_points'].sum(),
            'total_gps_data_points': df['position_data_points'].sum()
        }
    }

def main():
    """Main function for quick analysis."""
    load_dotenv()
    
    # Get data path from environment or use default
    data_path = os.getenv('STRAVA_DATA_PATH', '../activity_fetcher/data/individual_activities')
    
    print(f"📍 Data path: {data_path}")
    
    # Load data
    df = load_strava_data(data_path)
    if df.empty:
        print("❌ No data found!")
        return
    
    # Calculate stats
    stats = calculate_quick_stats(df)
    
    # Display results
    print(f"""
🏃‍♂️ QUICK STRAVA STATS (with Stream Data)
{'='*40}
📊 Total Activities: {stats['total_activities']}
🎯 Date Range: {stats['date_range']}
📏 Total Distance: {stats['total_distance_km']} km
⏱️  Total Time: {stats['total_time_hours']} hours
🚀 Average Speed: {stats['average_speed_kmh']} km/h

🌊 STREAM DATA COVERAGE:
   💓 Heart Rate Streams: {stats['stream_stats']['activities_with_hr_streams']} activities
   📍 GPS Streams: {stats['stream_stats']['activities_with_gps_streams']} activities
   💗 Avg HR (from streams): {stats['stream_stats']['avg_hr_from_streams']} bpm
   📊 Total HR Data Points: {stats['stream_stats']['total_hr_data_points']:,}
   🗺️  Total GPS Data Points: {stats['stream_stats']['total_gps_data_points']:,}

🏃 Activity Types:""")
    
    for activity_type, count in stats['activity_types'].items():
        percentage = (count / stats['total_activities']) * 100
        print(f"   {activity_type}: {count} ({percentage:.1f}%)")
    
    print(f"""
📈 BREAKDOWN BY TYPE (including stream data):
{stats['by_type']}
    """)

if __name__ == "__main__":
    main()
