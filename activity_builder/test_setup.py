#!/usr/bin/env python3
"""
Test script to verify Strava data can be loaded and basic analysis works.
"""

import os
import sys
import json
from pathlib import Path

def test_data_loading():
    """Test if we can load the Strava data files."""
    # Try to get data path from environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        data_path = os.getenv('STRAVA_DATA_PATH', '../activity_fetcher/data/individual_activities')
    except ImportError:
        print("⚠️  dotenv not installed, using default path")
        data_path = '../activity_fetcher/data/individual_activities'
    
    print(f"🔍 Checking data path: {data_path}")
    
    activities_path = Path(data_path)
    if not activities_path.exists():
        print(f"❌ Path does not exist: {data_path}")
        return False
    
    json_files = list(activities_path.glob("*.json"))
    
    # Filter out stream data files
    activity_files = [f for f in json_files if "stream" not in f.name.lower()]
    stream_files_count = len(json_files) - len(activity_files)
    
    print(f"📁 Found {len(json_files)} total JSON files")
    print(f"📊 Activity files: {len(activity_files)}")
    print(f"🌊 Stream files (excluded): {stream_files_count}")
    
    if not activity_files:
        print("❌ No activity JSON files found!")
        return False
    
    # Test loading a few files
    loaded_count = 0
    sample_activity = None
    
    for file_path in activity_files[:5]:  # Test first 5 files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                activity_data = json.load(f)
                loaded_count += 1
                if sample_activity is None:
                    sample_activity = activity_data
        except Exception as e:
            print(f"⚠️  Error loading {file_path.name}: {e}")
    
    print(f"✅ Successfully loaded {loaded_count} sample files")
    
    if sample_activity:
        print("📋 Sample activity:")
        print(f"   Name: {sample_activity.get('name', 'N/A')}")
        print(f"   Type: {sample_activity.get('type', 'N/A')}")
        print(f"   Distance: {sample_activity.get('distance', 0)/1000:.1f} km")
        print(f"   Date: {sample_activity.get('start_date_local', 'N/A')}")
    
    return True

def test_basic_calculation():
    """Test basic calculations without pandas/numpy."""
    data_path = os.getenv('STRAVA_DATA_PATH', '../activity_fetcher/data/individual_activities')
    activities_path = Path(data_path)
    
    if not activities_path.exists():
        return False
    
    json_files = list(activities_path.glob("*.json"))
    
    # Filter out stream data files
    activity_files = [f for f in json_files if "stream" not in f.name.lower()]
    
    total_distance = 0
    total_time = 0
    activity_types = {}
    
    for file_path in activity_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                activity = json.load(f)
                
                # Sum distance (convert from meters to km)
                distance_km = activity.get('distance', 0) / 1000
                total_distance += distance_km
                
                # Sum moving time (convert from seconds to hours)
                moving_time_hours = activity.get('moving_time', 0) / 3600
                total_time += moving_time_hours
                
                # Count activity types
                activity_type = activity.get('type', 'Unknown')
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
                
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
    
    print("\n📊 BASIC CALCULATIONS:")
    print(f"   Total Activities: {len(activity_files)}")
    print(f"   Total Distance: {total_distance:.1f} km")
    print(f"   Total Time: {total_time:.1f} hours")
    print(f"   Average Distance: {total_distance/len(activity_files):.1f} km")
    print(f"   Activity Types: {activity_types}")
    
    return True

def main():
    """Main test function."""
    print("🧪 Testing Strava Activity Analysis Setup")
    print("="*45)
    
    # Test 1: Data loading
    print("\n1️⃣  Testing data loading...")
    if not test_data_loading():
        print("❌ Data loading test failed!")
        return 1
    
    # Test 2: Basic calculations
    print("\n2️⃣  Testing basic calculations...")
    if not test_basic_calculation():
        print("❌ Basic calculation test failed!")
        return 1
    
    print("\n✅ All tests passed!")
    print("\n🚀 Ready to run analysis:")
    print("   • For full analysis: python activity_analyzer.py")
    print("   • For quick stats: python quick_stats.py")
    print("   • Make sure to install requirements: pip install -r requirements.txt")
    
    return 0

if __name__ == "__main__":
    exit(main())
