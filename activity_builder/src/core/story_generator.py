#!/usr/bin/env python3
"""
Strava Activity Story Generator with ChromaDB Integration

This script converts Strava activity data and stream analytics into natural language stories
and stores them in ChromaDB for semantic search and analysis.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StravaStoryGenerator:
    def __init__(self):
        """Initialize the story generator with ChromaDB connection."""
        self.base_path = os.getenv('STRAVA_DATA_PATH', '../activity_fetcher/data/individual_activities')
        self.chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
        self.chroma_port = int(os.getenv('CHROMA_PORT', '8000'))
        
        self.activities_df = None
        self.streams = {}
        self.chroma_client = None
        self.collection = None
        
        # Check for USER_BIRTHYEAR environment variable for HR zone calculations
        birth_year = os.getenv('USER_BIRTHYEAR')
        if birth_year:
            try:
                age = datetime.now().year - int(birth_year)
                max_hr = 220 - age
                print(f"🎂 Using USER_BIRTHYEAR ({birth_year}) for HR zones. Estimated max HR: {max_hr} bpm")
            except (ValueError, TypeError):
                print("⚠️  Invalid USER_BIRTHYEAR format. Expected 4-digit year (e.g., 1990)")
        else:
            print("ℹ️  Set USER_BIRTHYEAR environment variable for personalized HR zone calculations")
        
        # Story templates and patterns
        self.weather_descriptors = [
            "sunny morning", "crisp afternoon", "pleasant evening", "foggy morning",
            "windy day", "cool morning", "warm afternoon", "clear day"
        ]
        
        self.effort_descriptors = {
            "easy": ["relaxed", "comfortable", "easy-going", "leisurely"],
            "moderate": ["steady", "consistent", "good rhythm", "solid effort"],
            "hard": ["challenging", "tough", "demanding", "intense"],
            "very_hard": ["grueling", "exhausting", "maximum effort", "all-out"]
        }
        
        self.climb_descriptors = {
            "flat": ["mostly flat terrain", "gentle rolling hills", "flat route"],
            "rolling": ["rolling hills", "undulating terrain", "some climbs"],
            "hilly": ["hilly terrain", "significant climbing", "challenging climbs"],
            "mountainous": ["mountainous terrain", "steep climbs", "major elevation gain"]
        }
    
    def connect_to_chromadb(self):
        """Connect to ChromaDB and create/get collection."""
        try:
            print(f"🔗 Connecting to ChromaDB at {self.chroma_host}:{self.chroma_port}")
            self.chroma_client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(allow_reset=True)
            )
            
            # Create or get collection for activity stories
            self.collection = self.chroma_client.get_or_create_collection(
                name="strava_activity_stories",
                metadata={"description": "Natural language stories of Strava activities with metadata"}
            )
            
            print(f"✅ Connected to ChromaDB. Collection has {self.collection.count()} existing stories.")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            return False
    
    def load_activities_and_streams(self) -> pd.DataFrame:
        """Load all activity JSON files and their stream data."""
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
        print("🌊 Processing stream data...")
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
        
        self.activities_df = pd.DataFrame(activities)
        self.streams = streams
        
        # Preprocess data
        self._preprocess_data()
        
        print(f"✅ Loaded {len(self.activities_df)} activities with stream data")
        return self.activities_df
    
    def _preprocess_data(self):
        """Preprocess the activity data and add stream analytics."""
        df = self.activities_df
        
        # Basic preprocessing
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['start_date_local'] = pd.to_datetime(df['start_date_local'])
        df['distance_km'] = df['distance'] / 1000
        df['moving_time_hours'] = df['moving_time'] / 3600
        df['moving_time_minutes'] = df['moving_time'] / 60
        df['average_speed_kmh'] = df['average_speed'] * 3.6
        df['max_speed_kmh'] = df['max_speed'] * 3.6
        
        # Add stream analytics
        self._add_stream_analytics()
        
        # Add story elements
        self._add_story_elements()
    
    def _add_stream_analytics(self):
        """Add detailed analytics from stream data."""
        df = self.activities_df
        
        # Initialize stream columns
        df['hr_stream_avg'] = np.nan
        df['hr_stream_max'] = np.nan
        df['hr_stream_min'] = np.nan
        df['hr_data_points'] = 0
        df['elevation_gain_detailed'] = np.nan
        df['speed_variability'] = np.nan
        df['position_data_points'] = 0
        
        for idx, row in df.iterrows():
            activity_id = row['id']
            if activity_id in self.streams:
                streams = self.streams[activity_id]
                
                # Heart rate analysis
                if 'heartrate' in streams:
                    hr_data = [hr for hr in streams['heartrate'] if hr > 0]
                    if hr_data:
                        df.at[idx, 'hr_stream_avg'] = np.mean(hr_data)
                        df.at[idx, 'hr_stream_max'] = max(hr_data)
                        df.at[idx, 'hr_stream_min'] = min(hr_data)
                        df.at[idx, 'hr_data_points'] = len(hr_data)
                
                # Position data
                if 'latlng' in streams:
                    df.at[idx, 'position_data_points'] = len(streams['latlng'])
                
                # Speed variability
                if 'distance' in streams and 'time' in streams:
                    speed_var = self._calculate_speed_variability(streams['distance'], streams['time'])
                    df.at[idx, 'speed_variability'] = speed_var
    
    def _calculate_speed_variability(self, distance_data, time_data):
        """Calculate speed variability coefficient."""
        if len(distance_data) != len(time_data) or len(distance_data) < 2:
            return None
        
        speeds = []
        for i in range(1, len(distance_data)):
            dist_diff = distance_data[i] - distance_data[i-1]
            time_diff = time_data[i] - time_data[i-1]
            if time_diff > 0:
                speed = (dist_diff / time_diff) * 3.6
                speeds.append(speed)
        
        return np.std(speeds) / np.mean(speeds) if speeds and np.mean(speeds) > 0 else None
    
    def _add_story_elements(self):
        """Add elements needed for story generation."""
        df = self.activities_df
        
        # Effort level based on heart rate and speed
        df['effort_level'] = df.apply(self._determine_effort_level, axis=1)
        
        # Terrain description based on elevation gain
        df['terrain_type'] = df.apply(self._determine_terrain_type, axis=1)
        
        # Time of day
        df['hour'] = df['start_date_local'].dt.hour
        df['time_of_day'] = df['hour'].apply(self._get_time_of_day)
        
        # Day of week
        df['day_of_week'] = df['start_date_local'].dt.day_name()
        
        # Season
        df['month'] = df['start_date_local'].dt.month
        df['season'] = df['month'].apply(self._get_season)
    
    def _determine_effort_level(self, row):
        """Determine effort level based on HR zones calculated from user's max HR."""
        hr_avg = row.get('hr_stream_avg', row.get('average_heartrate', 0))
        speed = row.get('average_speed_kmh', 0)
        activity_type = row.get('type', 'Unknown')
        
        if pd.isna(hr_avg) or hr_avg == 0:
            # Use speed-based estimation when HR data is not available
            if activity_type == 'Ride':
                if speed < 15: return "easy"
                elif speed < 25: return "moderate"
                elif speed < 35: return "hard"
                else: return "very_hard"
            elif activity_type == 'Run':
                if speed < 8: return "easy"
                elif speed < 12: return "moderate"
                elif speed < 16: return "hard"
                else: return "very_hard"
            else:
                return "moderate"
        else:
            # Use HR zone-based estimation
            max_hr = self._calculate_max_hr()
            if max_hr is None:
                # Fallback to generic HR zones if birth year not available
                if hr_avg < 130: return "easy"
                elif hr_avg < 150: return "moderate"
                elif hr_avg < 170: return "hard"
                else: return "very_hard"
            
            # Calculate HR percentage and determine zone
            hr_percentage = (hr_avg / max_hr) * 100
            
            # HR Zone-based effort levels:
            # Zone 1 (50-60%): Active Recovery/Easy
            # Zone 2 (60-70%): Aerobic Base/Easy-Moderate
            # Zone 3 (70-80%): Aerobic Threshold/Moderate
            # Zone 4 (80-90%): Lactate Threshold/Hard
            # Zone 5 (90%+): VO2 Max/Very Hard
            
            if hr_percentage < 60: return "easy"
            elif hr_percentage < 70: return "easy"  # Zone 2 lower
            elif hr_percentage < 80: return "moderate"  # Zone 3
            elif hr_percentage < 90: return "hard"  # Zone 4
            else: return "very_hard"  # Zone 5
    
    def _calculate_max_hr(self):
        """Calculate maximum heart rate based on user's birth year from environment."""
        try:
            birth_year = os.getenv('USER_BIRTHYEAR')
            if not birth_year:
                print("⚠️  USER_BIRTHYEAR environment variable not set. Using fallback HR zones.")
                return None
            
            current_year = datetime.now().year
            age = current_year - int(birth_year)
            
            # Using the most common formula: 220 - age
            # Note: More accurate formulas exist (like 208 - (0.7 * age)) but 220-age is widely used
            max_hr = 220 - age
            
            # Sanity check
            if age < 10 or age > 100:
                print(f"⚠️  Calculated age ({age}) seems unusual. Please check USER_BIRTHYEAR.")
                return None
            
            if max_hr < 120 or max_hr > 220:
                print(f"⚠️  Calculated max HR ({max_hr}) seems unusual for age {age}.")
                return None
            
            return max_hr
            
        except (ValueError, TypeError) as e:
            print(f"⚠️  Error calculating max HR from USER_BIRTHYEAR: {e}")
            return None
    
    def _determine_terrain_type(self, row):
        """Determine terrain type based on elevation gain."""
        elevation_gain = row.get('total_elevation_gain', 0)
        distance_km = row.get('distance_km', 1)
        
        # Elevation gain per km
        elevation_per_km = elevation_gain / distance_km if distance_km > 0 else 0
        
        if elevation_per_km < 5: return "flat"
        elif elevation_per_km < 15: return "rolling"
        elif elevation_per_km < 30: return "hilly"
        else: return "mountainous"
    
    def _get_time_of_day(self, hour):
        """Get time of day description."""
        if 5 <= hour < 12: return "morning"
        elif 12 <= hour < 17: return "afternoon"
        elif 17 <= hour < 21: return "evening"
        else: return "night"
    
    def _get_season(self, month):
        """Get season from month."""
        if month in [12, 1, 2]: return "winter"
        elif month in [3, 4, 5]: return "spring"
        elif month in [6, 7, 8]: return "summer"
        else: return "autumn"
    
    def generate_activity_story(self, row) -> str:
        """Generate a natural language story for an activity."""
        # Extract key metrics
        distance_km = row['distance_km']
        elevation_gain = row.get('total_elevation_gain', 0)
        avg_speed = row['average_speed_kmh']
        avg_hr = row.get('hr_stream_avg', row.get('average_heartrate'))
        activity_type = row['type']
        effort_level = row['effort_level']
        terrain_type = row['terrain_type']
        time_of_day = row['time_of_day']
        season = row['season']
        activity_name = row.get('name', f"{time_of_day.title()} {activity_type}")
        
        # Start building the story
        story_parts = []
        
        # Opening with distance and type
        if activity_type == 'Ride':
            story_parts.append(f"A {distance_km:.1f}km cycling ride")
        elif activity_type == 'Run':
            story_parts.append(f"A {distance_km:.1f}km run")
        else:
            story_parts.append(f"A {distance_km:.1f}km {activity_type.lower()}")
        
        # Add elevation if significant
        if elevation_gain > 50:
            story_parts.append(f"with {elevation_gain:.0f}m of climbing")
        
        # Add speed
        story_parts.append(f"at an average speed of {avg_speed:.1f} km/h")
        
        # Add heart rate if available
        if not pd.isna(avg_hr) and avg_hr > 0:
            story_parts.append(f"and an average heart rate of {avg_hr:.0f} bpm")
        
        # Add terrain description
        terrain_desc = self.climb_descriptors[terrain_type][0]
        effort_desc = self.effort_descriptors[effort_level][0]
        
        # Build the main sentence
        main_sentence = " ".join(story_parts) + "."
        
        # Add context
        context_parts = []
        
        # Time and setting
        weather = np.random.choice(self.weather_descriptors)
        context_parts.append(f"Took place on a {weather} in {season}")
        
        # Effort description
        if terrain_type in ["hilly", "mountainous"]:
            context_parts.append(f"Felt {effort_desc} on the climbs")
        else:
            context_parts.append(f"Maintained a {effort_desc} pace throughout")
        
        # Additional insights from stream data
        if row['hr_data_points'] > 1000:
            context_parts.append("Heart rate data shows consistent effort")
        
        if row['position_data_points'] > 500:
            context_parts.append("GPS tracking captured detailed route information")
        
        # Combine into final story
        full_story = main_sentence + " " + ". ".join(context_parts) + "."
        
        return full_story
    
    def generate_and_store_stories(self):
        """Generate stories for all activities and store in ChromaDB."""
        if self.activities_df is None:
            self.load_activities_and_streams()
        
        if not self.connect_to_chromadb():
            print("❌ Cannot connect to ChromaDB. Stories will not be stored.")
            return
        
        print("📝 Generating activity stories...")
        
        stories = []
        metadatas = []
        ids = []
        
        for idx, row in self.activities_df.iterrows():
            try:
                # Generate story
                story = self.generate_activity_story(row)
                
                # Prepare metadata
                metadata = {
                    "activity_id": str(row['id']),
                    "activity_name": row.get('name', ''),
                    "activity_type": row['type'],
                    "date": row['start_date_local'].strftime('%Y-%m-%d'),
                    "distance_km": float(row['distance_km']),
                    "avg_speed_kmh": float(row['average_speed_kmh']),
                    "elevation_gain_m": float(row.get('total_elevation_gain', 0)),
                    "avg_hr_bpm": float(row.get('hr_stream_avg', row.get('average_heartrate', 0))),
                    "effort_level": row['effort_level'],
                    "terrain_type": row['terrain_type'],
                    "time_of_day": row['time_of_day'],
                    "season": row['season'],
                    "has_hr_data": bool(row['hr_data_points'] > 0),
                    "has_gps_data": bool(row['position_data_points'] > 0)
                }
                
                stories.append(story)
                metadatas.append(metadata)
                ids.append(str(row['id']))
                
                if idx < 5:  # Print first 5 stories as examples
                    print(f"\n📖 Story {idx + 1}: {story}")
                
            except Exception as e:
                print(f"⚠️  Error generating story for activity {row.get('id', 'unknown')}: {e}")
        
        # Store in ChromaDB
        if stories:
            try:
                print(f"\n💾 Storing {len(stories)} stories in ChromaDB...")
                
                # Clear existing data for fresh start (optional)
                # self.collection.delete()
                
                # Add to collection in batches
                batch_size = 50
                for i in range(0, len(stories), batch_size):
                    batch_stories = stories[i:i + batch_size]
                    batch_metadatas = metadatas[i:i + batch_size]
                    batch_ids = ids[i:i + batch_size]
                    
                    self.collection.upsert(
                        documents=batch_stories,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                
                print(f"✅ Successfully stored {len(stories)} activity stories in ChromaDB!")
                print(f"🔍 Collection now has {self.collection.count()} total stories.")
                
            except Exception as e:
                print(f"❌ Error storing stories in ChromaDB: {e}")
        
        return stories, metadatas
    
    def search_stories(self, query: str, n_results: int = 5) -> Dict:
        """Search for similar stories using semantic search."""
        if not self.collection:
            print("❌ No ChromaDB collection available. Connect first.")
            return {}
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            print(f"\n🔍 Search results for: '{query}'")
            print("=" * 50)
            
            if results['documents'][0]:
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    print(f"\n{i + 1}. {doc}")
                    print(f"   📅 {metadata['date']} | {metadata['activity_type']} | {metadata['distance_km']:.1f}km")
                    print(f"   ⚡ {metadata['avg_speed_kmh']:.1f}km/h | 💓 {metadata['avg_hr_bpm']:.0f}bpm | 🏔️ {metadata['elevation_gain_m']:.0f}m")
            else:
                print("No matching stories found.")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching stories: {e}")
            return {}
    
    def get_collection_stats(self):
        """Get statistics about the stored stories."""
        if not self.collection:
            return None
        
        try:
            count = self.collection.count()
            
            # Get a sample to analyze metadata
            sample = self.collection.get(limit=count)
            
            if sample['metadatas']:
                metadatas = sample['metadatas']
                
                # Analyze the data
                activity_types = {}
                effort_levels = {}
                terrain_types = {}
                
                for meta in metadatas:
                    # Count activity types
                    act_type = meta.get('activity_type', 'Unknown')
                    activity_types[act_type] = activity_types.get(act_type, 0) + 1
                    
                    # Count effort levels
                    effort = meta.get('effort_level', 'Unknown')
                    effort_levels[effort] = effort_levels.get(effort, 0) + 1
                    
                    # Count terrain types
                    terrain = meta.get('terrain_type', 'Unknown')
                    terrain_types[terrain] = terrain_types.get(terrain, 0) + 1
                
                stats = {
                    'total_stories': count,
                    'activity_types': activity_types,
                    'effort_levels': effort_levels,
                    'terrain_types': terrain_types
                }
                
                print(f"\n📊 CHROMADB COLLECTION STATISTICS")
                print("=" * 40)
                print(f"Total Stories: {count}")
                print(f"Activity Types: {activity_types}")
                print(f"Effort Levels: {effort_levels}")
                print(f"Terrain Types: {terrain_types}")
                
                return stats
            
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return None

def main():
    """Main execution function."""
    print("🚴‍♂️ Strava Activity Story Generator with ChromaDB Starting...")
    
    try:
        generator = StravaStoryGenerator()
        
        # Generate and store stories
        stories, metadatas = generator.generate_and_store_stories()
        
        # Show collection statistics
        generator.get_collection_stats()
        
        # Demo search functionality
        print("\n🔍 DEMO SEARCHES:")
        generator.search_stories("challenging climb mountain bike ride", 3)
        generator.search_stories("easy morning cycling comfortable pace", 3)
        generator.search_stories("high heart rate intense workout", 3)
        
        print("\n✅ Story generation and ChromaDB integration completed!")
        
    except Exception as e:
        print(f"❌ Error during story generation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
