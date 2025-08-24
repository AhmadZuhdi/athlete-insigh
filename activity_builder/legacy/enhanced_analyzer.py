#!/usr/bin/env python3
"""
Enhanced Strava Activity Data Analyzer with Stream Data

This script reads Strava activity data and stream data from JSON files and performs 
comprehensive analysis using pandas and numpy for statistical insights.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Optional plotting imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("📊 Note: matplotlib/seaborn not available - plotting features disabled")

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnhancedStravaAnalyzer:
    def __init__(self):
        """Initialize the analyzer with base path from environment variables."""
        self.base_path = os.getenv('STRAVA_DATA_PATH', '../activity_fetcher/data/individual_activities')
        self.activities_df = None
        self.streams = {}
        self.stats = {}
        
    def load_activities_and_streams(self) -> pd.DataFrame:
        """Load all activity JSON files and their stream data into pandas DataFrame."""
        print(f"🔍 Loading activities and streams from: {self.base_path}")
        
        activities_path = Path(self.base_path)
        if not activities_path.exists():
            raise FileNotFoundError(f"Activities directory not found: {self.base_path}")
        
        activities = []
        streams = {}
        json_files = list(activities_path.glob("*.json"))
        
        # Separate activity files and stream files
        activity_files = [f for f in json_files if "_streams_" not in f.name]
        stream_files = [f for f in json_files if "_streams_" in f.name]
        
        print(f"📁 Found {len(json_files)} total JSON files")
        print(f"📊 Activity files: {len(activity_files)}")
        print(f"🌊 Stream files: {len(stream_files)}")
        
        # Load activities
        for file_path in activity_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
                    activities.append(activity_data)
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")
        
        # Load stream data
        for file_path in stream_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    stream_data = json.load(f)
                    activity_id = stream_data.get('activity_id')
                    stream_type = stream_data.get('stream_type')
                    
                    if activity_id not in streams:
                        streams[activity_id] = {}
                    streams[activity_id][stream_type] = stream_data['data']
            except Exception as e:
                print(f"⚠️  Error loading stream {file_path.name}: {e}")
        
        if not activities:
            raise ValueError("No valid activity files found")
        
        # Convert to DataFrame
        self.activities_df = pd.DataFrame(activities)
        self.streams = streams
        
        # Data preprocessing
        self._preprocess_data()
        
        print(f"✅ Loaded {len(self.activities_df)} activities with stream data successfully")
        return self.activities_df
    
    def _preprocess_data(self):
        """Preprocess the activity data for analysis including stream data."""
        df = self.activities_df
        
        # Basic preprocessing
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['start_date_local'] = pd.to_datetime(df['start_date_local'])
        df['year'] = df['start_date_local'].dt.year
        df['month'] = df['start_date_local'].dt.month
        df['day_of_week'] = df['start_date_local'].dt.day_name()
        df['hour'] = df['start_date_local'].dt.hour
        df['distance_km'] = df['distance'] / 1000
        df['moving_time_minutes'] = df['moving_time'] / 60
        df['moving_time_hours'] = df['moving_time'] / 3600
        df['elapsed_time_minutes'] = df['elapsed_time'] / 60
        df['average_speed_kmh'] = df['average_speed'] * 3.6
        df['max_speed_kmh'] = df['max_speed'] * 3.6
        
        # Add stream data analysis
        self._add_stream_analysis()
        
        # Fill missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
    
    def _add_stream_analysis(self):
        """Add detailed stream data analysis to the activities dataframe."""
        df = self.activities_df
        
        # Initialize stream columns
        df['hr_stream_points'] = 0
        df['hr_stream_avg'] = np.nan
        df['hr_stream_max'] = np.nan
        df['hr_stream_min'] = np.nan
        df['hr_zones'] = None
        df['distance_stream_points'] = 0
        df['time_stream_points'] = 0
        df['position_stream_points'] = 0
        df['elevation_gain_detailed'] = np.nan
        df['speed_variability'] = np.nan
        
        for idx, row in df.iterrows():
            activity_id = row['id']
            if activity_id in self.streams:
                streams = self.streams[activity_id]
                
                # Heart rate analysis
                if 'heartrate' in streams:
                    hr_data = [hr for hr in streams['heartrate'] if hr > 0]
                    if hr_data:
                        df.at[idx, 'hr_stream_points'] = len(hr_data)
                        df.at[idx, 'hr_stream_avg'] = np.mean(hr_data)
                        df.at[idx, 'hr_stream_max'] = max(hr_data)
                        df.at[idx, 'hr_stream_min'] = min(hr_data)
                        df.at[idx, 'hr_zones'] = self._calculate_hr_zones(hr_data)
                
                # Distance analysis
                if 'distance' in streams:
                    df.at[idx, 'distance_stream_points'] = len(streams['distance'])
                
                # Time analysis
                if 'time' in streams:
                    df.at[idx, 'time_stream_points'] = len(streams['time'])
                
                # Position analysis
                if 'latlng' in streams:
                    df.at[idx, 'position_stream_points'] = len(streams['latlng'])
                
                # Speed variability (if we have distance and time)
                if 'distance' in streams and 'time' in streams:
                    speed_var = self._calculate_speed_variability(streams['distance'], streams['time'])
                    df.at[idx, 'speed_variability'] = speed_var
    
    def _calculate_hr_zones(self, hr_data):
        """Calculate heart rate zones distribution."""
        if not hr_data:
            return None
        
        # Basic HR zones (can be customized)
        zones = {
            'zone1': 0,  # < 130 bpm
            'zone2': 0,  # 130-150 bpm
            'zone3': 0,  # 150-170 bpm
            'zone4': 0,  # 170-190 bpm
            'zone5': 0   # > 190 bpm
        }
        
        for hr in hr_data:
            if hr < 130:
                zones['zone1'] += 1
            elif hr < 150:
                zones['zone2'] += 1
            elif hr < 170:
                zones['zone3'] += 1
            elif hr < 190:
                zones['zone4'] += 1
            else:
                zones['zone5'] += 1
        
        total = sum(zones.values())
        return {k: round(v/total*100, 1) for k, v in zones.items()}
    
    def _calculate_speed_variability(self, distance_data, time_data):
        """Calculate speed variability coefficient."""
        if len(distance_data) != len(time_data) or len(distance_data) < 2:
            return None
        
        speeds = []
        for i in range(1, len(distance_data)):
            dist_diff = distance_data[i] - distance_data[i-1]
            time_diff = time_data[i] - time_data[i-1]
            if time_diff > 0:
                speed = (dist_diff / time_diff) * 3.6  # km/h
                speeds.append(speed)
        
        if speeds:
            return np.std(speeds) / np.mean(speeds) if np.mean(speeds) > 0 else 0
        return None
    
    def analyze_stream_coverage(self):
        """Analyze stream data coverage and quality."""
        df = self.activities_df
        
        coverage = {
            'total_activities': len(df),
            'hr_coverage': (df['hr_stream_points'] > 0).sum(),
            'gps_coverage': (df['position_stream_points'] > 0).sum(),
            'distance_coverage': (df['distance_stream_points'] > 0).sum(),
            'time_coverage': (df['time_stream_points'] > 0).sum(),
            'hr_coverage_pct': (df['hr_stream_points'] > 0).mean() * 100,
            'gps_coverage_pct': (df['position_stream_points'] > 0).mean() * 100,
            'total_hr_points': df['hr_stream_points'].sum(),
            'total_gps_points': df['position_stream_points'].sum(),
            'avg_hr_from_streams': df['hr_stream_avg'].mean(),
            'activities_by_type': df.groupby('type').agg({
                'hr_stream_points': ['count', 'sum', lambda x: (x > 0).sum()],
                'position_stream_points': ['sum', lambda x: (x > 0).sum()],
                'hr_stream_avg': 'mean'
            }).round(2)
        }
        
        return coverage
    
    def generate_enhanced_report(self) -> str:
        """Generate comprehensive report including stream data analysis."""
        if self.activities_df is None:
            self.load_activities_and_streams()
        
        coverage = self.analyze_stream_coverage()
        
        report = f"""
🏃‍♂️ ENHANCED STRAVA ACTIVITY ANALYSIS REPORT
{'='*55}

📊 OVERVIEW
- Total Activities: {coverage['total_activities']}
- Total Distance: {self.activities_df['distance_km'].sum():.1f} km
- Total Moving Time: {self.activities_df['moving_time_hours'].sum():.1f} hours

🌊 STREAM DATA COVERAGE
- Heart Rate Streams: {coverage['hr_coverage']}/{coverage['total_activities']} ({coverage['hr_coverage_pct']:.1f}%)
- GPS Position Streams: {coverage['gps_coverage']}/{coverage['total_activities']} ({coverage['gps_coverage_pct']:.1f}%)
- Total HR Data Points: {coverage['total_hr_points']:,}
- Total GPS Data Points: {coverage['total_gps_points']:,}
- Average HR (from streams): {coverage['avg_hr_from_streams']:.1f} bpm

💓 HEART RATE INSIGHTS
"""
        
        # Add HR zone analysis for activities with HR data
        hr_activities = self.activities_df[self.activities_df['hr_stream_points'] > 0]
        if not hr_activities.empty:
            # Calculate average HR zones across all activities
            all_zones = {'zone1': [], 'zone2': [], 'zone3': [], 'zone4': [], 'zone5': []}
            for zones in hr_activities['hr_zones'].dropna():
                if zones:
                    for zone, pct in zones.items():
                        all_zones[zone].append(pct)
            
            report += "- Average Time in HR Zones:\n"
            for zone, percentages in all_zones.items():
                if percentages:
                    avg_pct = np.mean(percentages)
                    zone_name = {
                        'zone1': 'Zone 1 (<130 bpm)',
                        'zone2': 'Zone 2 (130-150 bpm)', 
                        'zone3': 'Zone 3 (150-170 bpm)',
                        'zone4': 'Zone 4 (170-190 bpm)',
                        'zone5': 'Zone 5 (>190 bpm)'
                    }[zone]
                    report += f"  • {zone_name}: {avg_pct:.1f}%\n"
        
        report += f"""
📈 DETAILED BREAKDOWN BY TYPE:
{coverage['activities_by_type']}

🎯 DATA QUALITY INSIGHTS
- Activities with complete HR data: {coverage['hr_coverage']}
- Activities with GPS tracking: {coverage['gps_coverage']}
- Average data points per activity: {coverage['total_hr_points'] / max(coverage['hr_coverage'], 1):.0f} (HR), {coverage['total_gps_points'] / max(coverage['gps_coverage'], 1):.0f} (GPS)
"""
        
        return report

def main():
    """Main execution function."""
    print("🚴‍♂️ Enhanced Strava Activity Analyzer Starting...")
    
    try:
        analyzer = EnhancedStravaAnalyzer()
        
        # Load and analyze data
        analyzer.load_activities_and_streams()
        
        # Generate and display report
        report = analyzer.generate_enhanced_report()
        print(report)
        
        # Save enhanced data
        if analyzer.activities_df is not None:
            export_columns = [
                'id', 'name', 'type', 'start_date_local', 'distance_km', 
                'moving_time_minutes', 'average_speed_kmh', 'max_speed_kmh',
                'total_elevation_gain', 'average_heartrate', 'max_heartrate',
                'hr_stream_points', 'hr_stream_avg', 'hr_stream_max', 'hr_stream_min',
                'position_stream_points', 'speed_variability',
                'year', 'month', 'day_of_week', 'hour'
            ]
            
            available_columns = [col for col in export_columns if col in analyzer.activities_df.columns]
            analyzer.activities_df[available_columns].to_csv("enhanced_activity_analysis.csv", index=False)
            print("📁 Enhanced analysis saved to: enhanced_activity_analysis.csv")
        
        print("\n✅ Enhanced analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
