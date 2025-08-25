#!/usr/bin/env python3
"""
Activity Analyzer Script

Analyzes a specific activity based on activity ID, calculating:
- Max HR based on USER_BIRTHYEAR environment variable
- HR Zone distribution and duration
- Relative effort based on HR zones
- Comprehensive activity summary
- Optional contextual analysis (same week/month/year)

Usage: 
  python activity_analyzer.py <activity_id>
  python activity_analyzer.py <activity_id> --context {week,month,year}
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ActivityAnalyzer:
    """Analyzes cycling activity data including heart rate zones and effort calculations."""
    
    # Heart Rate Zone percentages of max HR
    HR_ZONES = {
        'Zone 1 (Active Recovery)': (0.50, 0.60),    # 50-60% of max HR
        'Zone 2 (Aerobic Base)': (0.60, 0.70),       # 60-70% of max HR
        'Zone 3 (Aerobic)': (0.70, 0.80),            # 70-80% of max HR
        'Zone 4 (Lactate Threshold)': (0.80, 0.90),  # 80-90% of max HR
        'Zone 5 (VO2 Max)': (0.90, 1.00),            # 90-100% of max HR
    }
    
    # Relative effort multipliers for each zone
    ZONE_EFFORT_MULTIPLIERS = {
        'Zone 1 (Active Recovery)': 1.0,
        'Zone 2 (Aerobic Base)': 2.0,
        'Zone 3 (Aerobic)': 3.0,
        'Zone 4 (Lactate Threshold)': 4.0,
        'Zone 5 (VO2 Max)': 5.0,
    }

    def __init__(self, data_dir: str = None):
        """Initialize the analyzer with data directory path."""
        if data_dir is None:
            # Check for STRAVA_DATA_PATH environment variable first
            strava_data_path = os.getenv('STRAVA_DATA_PATH')
            if strava_data_path:
                self.data_dir = Path(strava_data_path)
            else:
                # Default to activity_fetcher data directory (one level up from current script)
                self.data_dir = Path(__file__).parent.parent / "activity_fetcher" / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.activities_dir = self.data_dir / "individual_activities"
        self.metadata_dir = self.data_dir / "metadata"
        
        # Load activity index
        self.activity_index = self._load_activity_index()
        
        # Calculate max HR from birth year
        self.max_hr = self._calculate_max_hr()

    def _load_activity_index(self) -> List[Dict]:
        """Load the activity index from metadata."""
        index_file = self.metadata_dir / "activity_index.json"
        if not index_file.exists():
            raise FileNotFoundError(f"Activity index not found: {index_file}")
        
        with open(index_file, 'r') as f:
            return json.load(f)

    def _calculate_max_hr(self) -> int:
        """Calculate maximum heart rate based on birth year from environment."""
        birth_year = os.getenv('USER_BIRTHYEAR')
        if not birth_year:
            raise ValueError("USER_BIRTHYEAR environment variable not set")
        
        try:
            birth_year = int(birth_year)
            current_year = datetime.now().year
            age = current_year - birth_year
            
            # Use the formula: 220 - age (standard formula)
            max_hr = 220 - age
            print(f"Calculated max HR: {max_hr} bpm (age: {age})")
            return max_hr
            
        except ValueError:
            raise ValueError(f"Invalid birth year: {birth_year}")

    def get_activity_detail(self, activity_id: int) -> Dict:
        """Load activity detail from JSON file."""
        # Find activity in index
        activity_info = None
        for activity in self.activity_index:
            if activity['id'] == activity_id:
                activity_info = activity
                break
        
        if not activity_info:
            raise ValueError(f"Activity {activity_id} not found in index")
        
        # Load activity detail file
        detail_file = self.activities_dir / activity_info['filename']
        if not detail_file.exists():
            raise FileNotFoundError(f"Activity detail file not found: {detail_file}")
        
        with open(detail_file, 'r') as f:
            return json.load(f)

    def get_stream_data(self, activity_id: int, stream_type: str) -> Optional[List]:
        """Load stream data for a specific activity and stream type."""
        # Find activity in index to get filename pattern
        activity_info = None
        for activity in self.activity_index:
            if activity['id'] == activity_id:
                activity_info = activity
                break
        
        if not activity_info:
            return None
        
        # Construct stream filename
        base_filename = activity_info['filename'].replace('.json', '')
        stream_filename = f"{base_filename}_streams_{stream_type}.json"
        stream_file = self.activities_dir / stream_filename
        
        if not stream_file.exists():
            return None
        
        with open(stream_file, 'r') as f:
            stream_data = json.load(f)
            return stream_data.get('data', [])

    def calculate_hr_zones(self, heartrate_data: List[int], time_data: List[int]) -> Dict:
        """Calculate time spent in each heart rate zone."""
        if not heartrate_data or not time_data:
            return {}
        
        if len(heartrate_data) != len(time_data):
            raise ValueError("Heart rate and time data lengths don't match")
        
        zone_durations = {zone: 0 for zone in self.HR_ZONES.keys()}
        
        for i in range(len(heartrate_data) - 1):
            hr = heartrate_data[i]
            duration = time_data[i + 1] - time_data[i] if i + 1 < len(time_data) else 1
            
            # Determine which zone this HR falls into
            hr_percentage = hr / self.max_hr
            
            for zone_name, (min_pct, max_pct) in self.HR_ZONES.items():
                if min_pct <= hr_percentage < max_pct:
                    zone_durations[zone_name] += duration
                    break
        
        return zone_durations

    def calculate_relative_effort(self, zone_durations: Dict[str, int]) -> float:
        """Calculate relative effort based on time spent in HR zones."""
        total_effort = 0
        
        for zone_name, duration in zone_durations.items():
            if zone_name in self.ZONE_EFFORT_MULTIPLIERS:
                multiplier = self.ZONE_EFFORT_MULTIPLIERS[zone_name]
                effort = (duration / 60) * multiplier  # Convert to minutes and apply multiplier
                total_effort += effort
        
        return round(total_effort, 1)

    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def analyze_activity(self, activity_id: int) -> Dict:
        """Perform complete analysis of an activity."""
        # print(f"Analyzing activity {activity_id}...")
        
        # Get activity details
        activity_detail = self.get_activity_detail(activity_id)
        
        # Get stream data
        heartrate_data = self.get_stream_data(activity_id, 'heartrate')
        time_data = self.get_stream_data(activity_id, 'time')
        distance_data = self.get_stream_data(activity_id, 'distance')
        
        # Basic activity info
        analysis = {
            'activity_id': activity_id,
            'name': activity_detail.get('name', 'Unknown'),
            'date': activity_detail.get('start_date', 'Unknown'),
            'type': activity_detail.get('type', 'Unknown'),
            'total_time': self.format_duration(activity_detail.get('elapsed_time', 0)),
            'moving_time': self.format_duration(activity_detail.get('moving_time', 0)),
            'total_distance_m': activity_detail.get('distance', 0),
            'total_distance_km': round(activity_detail.get('distance', 0) / 1000, 2),
            'elevation_gain_m': activity_detail.get('total_elevation_gain', 0),
            'average_speed_ms': round(activity_detail.get('average_speed', 0), 2),
            'average_speed_kmh': round(activity_detail.get('average_speed', 0) * 3.6, 2),
            'max_speed_ms': round(activity_detail.get('max_speed', 0), 2),
            'max_speed_kmh': round(activity_detail.get('max_speed', 0) * 3.6, 2),
        }
        
        # Calculate moving time ratio
        moving_time = activity_detail.get('moving_time', 0)
        elapsed_time = activity_detail.get('elapsed_time', 0)
        if elapsed_time > 0:
            analysis['moving_time_ratio'] = round(moving_time / elapsed_time, 3)
        else:
            analysis['moving_time_ratio'] = 0
        
        # Heart rate analysis
        if heartrate_data and time_data:
            analysis['max_hr_calculated'] = self.max_hr
            analysis['average_hr'] = round(sum(heartrate_data) / len(heartrate_data), 1)
            analysis['max_hr_recorded'] = max(heartrate_data)
            analysis['min_hr_recorded'] = min(heartrate_data)
            
            # HR zone analysis
            zone_durations = self.calculate_hr_zones(heartrate_data, time_data)
            analysis['hr_zone_durations'] = {}
            analysis['hr_zone_percentages'] = {}
            
            total_time_with_hr = sum(zone_durations.values())
            
            for zone, duration in zone_durations.items():
                analysis['hr_zone_durations'][zone] = {
                    'seconds': duration,
                    'formatted': self.format_duration(duration)
                }
                
                if total_time_with_hr > 0:
                    percentage = (duration / total_time_with_hr) * 100
                    analysis['hr_zone_percentages'][zone] = round(percentage, 1)
                else:
                    analysis['hr_zone_percentages'][zone] = 0
            
            # Relative effort
            analysis['relative_effort'] = self.calculate_relative_effort(zone_durations)
            
        else:
            analysis['heart_rate_data'] = 'Not available'
            analysis['hr_zone_durations'] = {}
            analysis['hr_zone_percentages'] = {}
            analysis['relative_effort'] = 0
        
        return analysis

    def get_activities_by_timeframe(self, target_date: str, timeframe: str, max_activities: int = None) -> List[Dict]:
        """Get activities from the same timeframe as the target activity."""
        from datetime import datetime, timedelta
        
        # Parse target date
        target_dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
        
        filtered_activities = []
        
        for activity in self.activity_index:
            activity_dt = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            
            if timeframe == 'week':
                # Same week (Monday to Sunday)
                target_week_start = target_dt - timedelta(days=target_dt.weekday())
                target_week_end = target_week_start + timedelta(days=6)
                activity_week_start = activity_dt - timedelta(days=activity_dt.weekday())
                
                if target_week_start.date() == activity_week_start.date():
                    filtered_activities.append(activity)
                    
            elif timeframe == 'month':
                # Same month and year
                if (target_dt.year == activity_dt.year and 
                    target_dt.month == activity_dt.month):
                    filtered_activities.append(activity)
                    
            elif timeframe == 'year':
                # Same year
                if target_dt.year == activity_dt.year:
                    filtered_activities.append(activity)
        
        # Sort by date (most recent first)
        filtered_activities.sort(key=lambda x: x['start_date'], reverse=True)
        
        # Apply max_activities limit for year context
        if timeframe == 'year' and max_activities and len(filtered_activities) > max_activities:
            filtered_activities = filtered_activities[:max_activities]
            
        return filtered_activities

    def summarize_timeframe_activities(self, target_activity: Dict, timeframe: str, max_activities: int = None) -> Dict:
        """Summarize activities from the same timeframe."""
        activities = self.get_activities_by_timeframe(target_activity['date'], timeframe, max_activities)
        
        if not activities:
            return {'summary': f'No activities found in the same {timeframe}'}
        
        # Calculate totals
        total_distance = sum(act.get('distance', 0) for act in activities) / 1000  # Convert to km
        total_moving_time = sum(act.get('moving_time', 0) for act in activities)
        total_activities = len(activities)
        
        # Group by activity type
        activity_types = {}
        for activity in activities:
            act_type = activity.get('type', 'Unknown')
            if act_type not in activity_types:
                activity_types[act_type] = {'count': 0, 'distance': 0, 'time': 0}
            activity_types[act_type]['count'] += 1
            activity_types[act_type]['distance'] += activity.get('distance', 0) / 1000
            activity_types[act_type]['time'] += activity.get('moving_time', 0)
        
        # Format activity types summary
        type_summaries = []
        for act_type, stats in activity_types.items():
            type_summaries.append(f"{act_type}:{stats['count']}activities/{stats['distance']:.1f}km")
        
        summary = {
            'timeframe': timeframe,
            'total_activities': total_activities,
            'total_distance_km': round(total_distance, 1),
            'total_moving_time': self.format_duration(total_moving_time),
            'activity_types': activity_types,
            'activities_list': activities  # Include all activities, no limit
        }
        
        # Create summary string
        avg_distance = total_distance / total_activities if total_activities > 0 else 0
        summary_string = (f"{timeframe.capitalize()}_summary: {total_activities}activities, "
                         f"{total_distance:.1f}km_total, {avg_distance:.1f}km_avg, "
                         f"{self.format_duration(total_moving_time)}_total_time, "
                         f"types:[{','.join(type_summaries)}]")
        
        summary['summary_string'] = summary_string
        return summary

    def print_timeframe_summary(self, target_activity: Dict, timeframe: str, max_activities: int = None):
        """Print summary of activities from the same timeframe."""
        summary = self.summarize_timeframe_activities(target_activity, timeframe, max_activities)
        
        print(f"\n{timeframe.capitalize()} Context Summary:")
        print("-" * 80)
        print(summary['summary_string'])
        print("-" * 80)

    def get_summary_string(self, analysis: Dict) -> str:
        """Get a single-line summary string suitable for LLM analysis."""
        # Build HR zone summary
        hr_zones_summary = ""
        if 'average_hr' in analysis and analysis['hr_zone_durations']:
            zone_parts = []
            for zone, duration_info in analysis['hr_zone_durations'].items():
                percentage = analysis['hr_zone_percentages'][zone]
                if percentage > 0:  # Only include zones with time spent
                    zone_short = zone.split('(')[1].replace(')', '').replace(' ', '_') if '(' in zone else zone.replace(' ', '_')
                    zone_parts.append(f"{zone_short}:{percentage}%")
            hr_zones_summary = f", HR_zones:[{','.join(zone_parts)}], avg_HR:{analysis['average_hr']}bpm, relative_effort:{analysis['relative_effort']}pts"
        
        # Create single line summary
        summary = (f"Activity: {analysis['name']} ({analysis['type']}) on {analysis['date'][:10]} - "
                  f"Distance: {analysis['total_distance_km']}km, "
                  f"Time: {analysis['moving_time']} (moving) / {analysis['total_time']} (total), "
                  f"Avg_speed: {analysis['average_speed_kmh']}km/h, "
                  f"Elevation: {analysis['elevation_gain_m']}m"
                  f"{hr_zones_summary}")
        
        return summary

    def print_summary(self, analysis: Dict):
        """Print a single-line summary suitable for LLM analysis."""
        summary = self.get_summary_string(analysis)

        print("\nActivity Summary:")
        print("```")
        print(summary)
        print("```")
        
        # Add context summary if available
        context_found = False
        for timeframe in ['week', 'month', 'year']:
            context_key = f'{timeframe}_context'
            if context_key in analysis and 'summary_string' in analysis[context_key]:
                if not context_found:
                    print()  # Add blank line before context summaries
                    context_found = True
                print(analysis[context_key]['summary_string'])


def main():
    """Main function to run the activity analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze cycling activity data')
    parser.add_argument('activity_id', type=int, help='Activity ID to analyze')
    parser.add_argument('--context', choices=['week', 'month', 'year'], 
                       help='Include summary of activities from same week/month/year')
    parser.add_argument('--max-activities', type=int, default=50,
                       help='Maximum number of activities to load for year context (default: 50)')
    
    # Handle both old format (just activity_id) and new format (with arguments)
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        # Old format: python activity_analyzer.py <activity_id>
        activity_id = int(sys.argv[1])
        context_timeframe = None
        max_activities = 50
    else:
        # New format with argparse
        args = parser.parse_args()
        activity_id = args.activity_id
        context_timeframe = args.context
        max_activities = args.max_activities
    
    try:
        analyzer = ActivityAnalyzer()
        analysis = analyzer.analyze_activity(activity_id)
        
        # Add summary string to analysis
        analysis['summary_string'] = analyzer.get_summary_string(analysis)
        
        analyzer.print_summary(analysis)
        
        # Add timeframe context if requested
        if context_timeframe:
    
            # Add timeframe summary to analysis
            timeframe_summary = analyzer.summarize_timeframe_activities(analysis, context_timeframe, max_activities)
            analysis[f'{context_timeframe}_context'] = timeframe_summary
            
            # Analyze and print summaries for other activities in the same timeframe
            context_activities = timeframe_summary.get('activities_list', [])
            if context_activities:
                print("\nPrevious Activities Analysis:")
                print("```")
                
                for context_activity in context_activities:  # No limit, analyze all
                    if context_activity['id'] != activity_id:  # Skip the main activity
                        try:
                            context_analysis = analyzer.analyze_activity(context_activity['id'])
                            context_analysis['summary_string'] = analyzer.get_summary_string(context_analysis)
                            print(context_analysis['summary_string'])
                            
                        except Exception as e:
                            print(f"Could not analyze activity {context_activity['id']}: {e}")
                
                print("```")
        
        # Also save to JSON file
        output_file = f"activity_analysis_{activity_id}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\nDetailed analysis saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
