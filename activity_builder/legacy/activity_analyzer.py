#!/usr/bin/env python3
"""
Strava Activity Data Analyzer

This script reads Strava activity data from JSON files and performs comprehensive analysis
using pandas and numpy for statistical insights.
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

class StravaActivityAnalyzer:
    def __init__(self):
        """Initialize the analyzer with base path from environment variables."""
        self.base_path = os.getenv('STRAVA_DATA_PATH', '../activity_fetcher/data/individual_activities')
        self.activities_df = None
        self.stats = {}
        
    def load_activities(self) -> pd.DataFrame:
        """Load all activity JSON files into a pandas DataFrame."""
        print(f"🔍 Loading activities from: {self.base_path}")
        
        activities_path = Path(self.base_path)
        if not activities_path.exists():
            raise FileNotFoundError(f"Activities directory not found: {self.base_path}")
        
        activities = []
        json_files = list(activities_path.glob("*.json"))
        
        # Filter out stream data files
        activity_files = [f for f in json_files if "stream" not in f.name.lower()]
        stream_files_count = len(json_files) - len(activity_files)
        
        print(f"📁 Found {len(json_files)} total JSON files")
        print(f"📊 Activity files: {len(activity_files)}")
        print(f"🌊 Stream files (excluded): {stream_files_count}")
        
        for file_path in activity_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
                    activities.append(activity_data)
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")
        
        if not activities:
            raise ValueError("No valid activity files found")
        
        # Convert to DataFrame
        self.activities_df = pd.DataFrame(activities)
        
        # Data preprocessing
        self._preprocess_data()
        
        print(f"✅ Loaded {len(self.activities_df)} activities successfully")
        return self.activities_df
    
    def _preprocess_data(self):
        """Preprocess the activity data for analysis."""
        df = self.activities_df
        
        # Convert dates
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['start_date_local'] = pd.to_datetime(df['start_date_local'])
        
        # Extract date components
        df['year'] = df['start_date_local'].dt.year
        df['month'] = df['start_date_local'].dt.month
        df['day_of_week'] = df['start_date_local'].dt.day_name()
        df['hour'] = df['start_date_local'].dt.hour
        
        # Convert distance from meters to kilometers
        df['distance_km'] = df['distance'] / 1000
        
        # Convert time from seconds to minutes and hours
        df['moving_time_minutes'] = df['moving_time'] / 60
        df['moving_time_hours'] = df['moving_time'] / 3600
        df['elapsed_time_minutes'] = df['elapsed_time'] / 60
        
        # Calculate pace (minutes per km) for activities with distance > 0
        df['pace_min_per_km'] = np.where(
            df['distance_km'] > 0,
            df['moving_time_minutes'] / df['distance_km'],
            np.nan
        )
        
        # Convert average speed from m/s to km/h
        df['average_speed_kmh'] = df['average_speed'] * 3.6
        df['max_speed_kmh'] = df['max_speed'] * 3.6
        
        # Calculate calories estimate (rough approximation)
        df['estimated_calories'] = np.where(
            df['type'] == 'Run',
            df['distance_km'] * 70,  # ~70 calories per km for running
            df['distance_km'] * 40   # ~40 calories per km for cycling
        )
        
        # Fill missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
    def calculate_basic_stats(self) -> Dict[str, Any]:
        """Calculate basic statistics for all activities."""
        df = self.activities_df
        
        self.stats = {
            'total_activities': len(df),
            'activity_types': df['type'].value_counts().to_dict(),
            'date_range': {
                'start': df['start_date_local'].min().strftime('%Y-%m-%d'),
                'end': df['start_date_local'].max().strftime('%Y-%m-%d')
            },
            'total_distance_km': df['distance_km'].sum(),
            'total_moving_time_hours': df['moving_time_hours'].sum(),
            'total_elevation_gain_m': df['total_elevation_gain'].sum(),
            'average_distance_km': df['distance_km'].mean(),
            'average_moving_time_minutes': df['moving_time_minutes'].mean(),
            'average_speed_kmh': df['average_speed_kmh'].mean(),
            'activities_per_year': df['year'].value_counts().sort_index().to_dict(),
            'activities_per_month': df.groupby(['year', 'month']).size().to_dict(),
            'preferred_days': df['day_of_week'].value_counts().to_dict(),
            'preferred_hours': df['hour'].value_counts().sort_index().to_dict()
        }
        
        return self.stats
    
    def analyze_by_activity_type(self) -> Dict[str, pd.DataFrame]:
        """Analyze statistics grouped by activity type."""
        df = self.activities_df
        
        analysis = {}
        for activity_type in df['type'].unique():
            type_df = df[df['type'] == activity_type]
            
            analysis[activity_type] = {
                'count': len(type_df),
                'total_distance_km': type_df['distance_km'].sum(),
                'avg_distance_km': type_df['distance_km'].mean(),
                'total_time_hours': type_df['moving_time_hours'].sum(),
                'avg_time_minutes': type_df['moving_time_minutes'].mean(),
                'avg_speed_kmh': type_df['average_speed_kmh'].mean(),
                'avg_elevation_gain': type_df['total_elevation_gain'].mean(),
                'avg_pace_min_per_km': type_df['pace_min_per_km'].mean() if 'pace_min_per_km' in type_df.columns else None
            }
            
            # Heart rate analysis if available
            if 'average_heartrate' in type_df.columns and type_df['average_heartrate'].notna().any():
                hr_data = type_df[type_df['average_heartrate'] > 0]
                if not hr_data.empty:
                    analysis[activity_type].update({
                        'avg_heartrate': hr_data['average_heartrate'].mean(),
                        'max_heartrate_recorded': hr_data['max_heartrate'].max(),
                        'activities_with_hr': len(hr_data)
                    })
        
        return analysis
    
    def find_personal_records(self) -> Dict[str, Dict]:
        """Find personal records across different metrics."""
        df = self.activities_df
        
        records = {}
        for activity_type in df['type'].unique():
            type_df = df[df['type'] == activity_type]
            if type_df.empty:
                continue
                
            records[activity_type] = {}
            
            # Distance records
            if type_df['distance_km'].max() > 0:
                longest_idx = type_df['distance_km'].idxmax()
                records[activity_type]['longest_distance'] = {
                    'distance_km': type_df.loc[longest_idx, 'distance_km'],
                    'name': type_df.loc[longest_idx, 'name'],
                    'date': type_df.loc[longest_idx, 'start_date_local'].strftime('%Y-%m-%d'),
                    'id': type_df.loc[longest_idx, 'id']
                }
            
            # Speed records
            if type_df['average_speed_kmh'].max() > 0:
                fastest_avg_idx = type_df['average_speed_kmh'].idxmax()
                records[activity_type]['fastest_average_speed'] = {
                    'speed_kmh': type_df.loc[fastest_avg_idx, 'average_speed_kmh'],
                    'name': type_df.loc[fastest_avg_idx, 'name'],
                    'date': type_df.loc[fastest_avg_idx, 'start_date_local'].strftime('%Y-%m-%d'),
                    'distance_km': type_df.loc[fastest_avg_idx, 'distance_km']
                }
            
            # Time records
            if type_df['moving_time_hours'].max() > 0:
                longest_time_idx = type_df['moving_time_hours'].idxmax()
                records[activity_type]['longest_duration'] = {
                    'duration_hours': type_df.loc[longest_time_idx, 'moving_time_hours'],
                    'name': type_df.loc[longest_time_idx, 'name'],
                    'date': type_df.loc[longest_time_idx, 'start_date_local'].strftime('%Y-%m-%d'),
                    'distance_km': type_df.loc[longest_time_idx, 'distance_km']
                }
            
            # Elevation records
            if type_df['total_elevation_gain'].max() > 0:
                highest_elevation_idx = type_df['total_elevation_gain'].idxmax()
                records[activity_type]['highest_elevation_gain'] = {
                    'elevation_m': type_df.loc[highest_elevation_idx, 'total_elevation_gain'],
                    'name': type_df.loc[highest_elevation_idx, 'name'],
                    'date': type_df.loc[highest_elevation_idx, 'start_date_local'].strftime('%Y-%m-%d'),
                    'distance_km': type_df.loc[highest_elevation_idx, 'distance_km']
                }
        
        return records
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends over time."""
        df = self.activities_df
        
        # Monthly trends
        monthly_stats = df.groupby([df['start_date_local'].dt.to_period('M')]).agg({
            'distance_km': ['sum', 'mean', 'count'],
            'moving_time_hours': 'sum',
            'total_elevation_gain': 'sum'
        }).round(2)
        
        # Yearly trends
        yearly_stats = df.groupby('year').agg({
            'distance_km': ['sum', 'mean', 'count'],
            'moving_time_hours': 'sum',
            'total_elevation_gain': 'sum'
        }).round(2)
        
        return {
            'monthly_trends': monthly_stats.to_dict(),
            'yearly_trends': yearly_stats.to_dict()
        }
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        if self.activities_df is None:
            self.load_activities()
        
        basic_stats = self.calculate_basic_stats()
        type_analysis = self.analyze_by_activity_type()
        records = self.find_personal_records()
        
        report = f"""
🏃‍♂️ STRAVA ACTIVITY ANALYSIS REPORT
{'='*50}

📊 OVERVIEW
- Total Activities: {basic_stats['total_activities']}
- Date Range: {basic_stats['date_range']['start']} to {basic_stats['date_range']['end']}
- Total Distance: {basic_stats['total_distance_km']:.1f} km
- Total Moving Time: {basic_stats['total_moving_time_hours']:.1f} hours
- Total Elevation Gain: {basic_stats['total_elevation_gain_m']:.0f} m

🎯 ACTIVITY TYPES
"""
        
        for activity_type, count in basic_stats['activity_types'].items():
            percentage = (count / basic_stats['total_activities']) * 100
            report += f"- {activity_type}: {count} activities ({percentage:.1f}%)\n"
        
        report += f"""
📈 AVERAGES
- Average Distance: {basic_stats['average_distance_km']:.1f} km
- Average Duration: {basic_stats['average_moving_time_minutes']:.1f} minutes
- Average Speed: {basic_stats['average_speed_kmh']:.1f} km/h

🏆 PERSONAL RECORDS
"""
        
        for activity_type, type_records in records.items():
            report += f"\n{activity_type.upper()}:\n"
            for record_type, record_data in type_records.items():
                if record_type == 'longest_distance':
                    report += f"  • Longest: {record_data['distance_km']:.1f} km - {record_data['name']} ({record_data['date']})\n"
                elif record_type == 'fastest_average_speed':
                    report += f"  • Fastest Avg: {record_data['speed_kmh']:.1f} km/h - {record_data['name']} ({record_data['date']})\n"
        
        report += f"""
📅 ACTIVITY PATTERNS
- Most Active Year: {max(basic_stats['activities_per_year'], key=basic_stats['activities_per_year'].get)}
- Preferred Day: {max(basic_stats['preferred_days'], key=basic_stats['preferred_days'].get)}
- Most Common Hour: {max(basic_stats['preferred_hours'], key=basic_stats['preferred_hours'].get)}:00

💡 INSIGHTS
"""
        
        # Add some insights
        total_days = (pd.to_datetime(basic_stats['date_range']['end']) - 
                     pd.to_datetime(basic_stats['date_range']['start'])).days
        activities_per_week = (basic_stats['total_activities'] / total_days) * 7
        
        report += f"- Activity Frequency: {activities_per_week:.1f} activities per week\n"
        
        if 'Ride' in basic_stats['activity_types'] and 'Run' in basic_stats['activity_types']:
            ride_ratio = basic_stats['activity_types']['Ride'] / basic_stats['activity_types']['Run']
            report += f"- Cycling to Running Ratio: {ride_ratio:.1f}:1\n"
        
        return report
    
    def save_analysis_to_csv(self, output_path: str = "activity_analysis.csv"):
        """Save the processed data to CSV for further analysis."""
        if self.activities_df is None:
            self.load_activities()
        
        # Select key columns for export
        export_columns = [
            'id', 'name', 'type', 'start_date_local', 'distance_km', 
            'moving_time_minutes', 'average_speed_kmh', 'max_speed_kmh',
            'total_elevation_gain', 'average_heartrate', 'max_heartrate',
            'kudos_count', 'year', 'month', 'day_of_week', 'hour'
        ]
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in export_columns if col in self.activities_df.columns]
        
        self.activities_df[available_columns].to_csv(output_path, index=False)
        print(f"📁 Analysis saved to: {output_path}")

def main():
    """Main execution function."""
    print("🚴‍♂️ Strava Activity Analyzer Starting...")
    
    try:
        analyzer = StravaActivityAnalyzer()
        
        # Load and analyze data
        analyzer.load_activities()
        
        # Generate and display report
        report = analyzer.generate_summary_report()
        print(report)
        
        # Save processed data
        analyzer.save_analysis_to_csv()
        
        # Additional detailed analysis
        print("\n🔍 DETAILED ANALYSIS BY ACTIVITY TYPE")
        print("="*50)
        type_analysis = analyzer.analyze_by_activity_type()
        
        for activity_type, stats in type_analysis.items():
            print(f"\n{activity_type.upper()}:")
            print(f"  Count: {stats['count']}")
            print(f"  Total Distance: {stats['total_distance_km']:.1f} km")
            print(f"  Avg Distance: {stats['avg_distance_km']:.1f} km")
            print(f"  Total Time: {stats['total_time_hours']:.1f} hours")
            print(f"  Avg Speed: {stats['avg_speed_kmh']:.1f} km/h")
            if stats.get('avg_heartrate'):
                print(f"  Avg Heart Rate: {stats['avg_heartrate']:.0f} bpm")
        
        print("\n✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
