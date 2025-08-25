#!/usr/bin/env python3
"""
Test script for activity analyzer setup.
Verifies that data paths are accessible and environment is configured correctly.
"""

import os
import sys
from pathlib import Path
from activity_analyzer import ActivityAnalyzer

def test_setup():
    """Test the activity analyzer setup."""
    print("Testing Activity Analyzer Setup...")
    print("=" * 50)
    
    # Check birth year environment variable
    birth_year = os.getenv('USER_BIRTHYEAR')
    if birth_year:
        print(f"✓ USER_BIRTHYEAR set: {birth_year}")
        try:
            age = 2025 - int(birth_year)
            max_hr = 220 - age
            print(f"✓ Calculated age: {age}, Max HR: {max_hr}")
        except ValueError:
            print(f"✗ Invalid birth year format: {birth_year}")
            return False
    else:
        print("✗ USER_BIRTHYEAR environment variable not set")
        print("  Please run: export USER_BIRTHYEAR=<your_birth_year>")
        return False
    
    # Check data directory structure
    try:
        analyzer = ActivityAnalyzer()
        data_dir = analyzer.data_dir
        
        # Check if using custom data path
        strava_data_path = os.getenv('STRAVA_DATA_PATH')
        if strava_data_path:
            print(f"✓ Using STRAVA_DATA_PATH: {strava_data_path}")
        else:
            print("ℹ STRAVA_DATA_PATH not set, using default path")
        
        print(f"✓ Data directory path: {data_dir}")
        
        if data_dir.exists():
            print("✓ Data directory exists")
        else:
            print(f"✗ Data directory not found: {data_dir}")
            return False
        
        # Check for activity index
        if analyzer.metadata_dir.exists():
            print("✓ Metadata directory exists")
            
            index_file = analyzer.metadata_dir / "activity_index.json"
            if index_file.exists():
                print("✓ Activity index file found")
                
                # Try to load activity index
                try:
                    activities = analyzer.activity_index
                    print(f"✓ Activity index loaded: {len(activities)} activities found")
                    
                    if activities:
                        latest_activity = activities[0]
                        print(f"  Latest activity: {latest_activity['name']} (ID: {latest_activity['id']})")
                        return True
                    else:
                        print("✗ No activities found in index")
                        return False
                        
                except Exception as e:
                    print(f"✗ Error loading activity index: {e}")
                    return False
            else:
                print(f"✗ Activity index file not found: {index_file}")
                return False
        else:
            print(f"✗ Metadata directory not found: {analyzer.metadata_dir}")
            return False
            
    except Exception as e:
        print(f"✗ Error initializing analyzer: {e}")
        return False

def list_recent_activities():
    """List the 10 most recent activities for testing."""
    try:
        analyzer = ActivityAnalyzer()
        activities = analyzer.activity_index[:10]  # First 10 (most recent)
        
        print("\nRecent Activities (for testing):")
        print("-" * 50)
        for i, activity in enumerate(activities, 1):
            print(f"{i:2d}. {activity['name']} (ID: {activity['id']})")
            print(f"    Date: {activity['start_date'][:10]}")
            print(f"    Distance: {activity['distance']/1000:.1f} km")
            print()
            
    except Exception as e:
        print(f"Error listing activities: {e}")

def main():
    """Main test function."""
    success = test_setup()
    
    if success:
        print("\n🎉 Setup test PASSED! You can now use the activity analyzer.")
        list_recent_activities()
        print("Usage example:")
        print("  python activity_analyzer.py <activity_id>")
    else:
        print("\n❌ Setup test FAILED! Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
