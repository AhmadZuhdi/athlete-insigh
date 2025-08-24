#!/usr/bin/env python3
"""
Strava Activity Semantic Search Demo
=====================================
Demonstrates semantic search capabilities with ChromaDB
"""

import chromadb
import json
from datetime import datetime

def connect_to_chromadb():
    """Connect to ChromaDB"""
    try:
        client = chromadb.HttpClient(host="chromadb", port=8000)
        collection = client.get_collection(name="strava_activity_stories")
        print(f"🔗 Connected to ChromaDB. Collection has {collection.count()} stories.\n")
        return collection
    except Exception as e:
        print(f"❌ Error connecting to ChromaDB: {e}")
        return None

def search_stories(collection, query, n_results=5):
    """Search stories using semantic similarity"""
    print(f"🔍 Searching for: '{query}'")
    print("=" * 50)
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            print("❌ No stories found.")
            return
        
        for i, (story, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"{i+1}. {story}")
            
            # Parse metadata for display
            activity_date = metadata.get('activity_date', 'Unknown')
            activity_type = metadata.get('activity_type', 'Unknown')
            distance_km = metadata.get('distance_km', 0)
            
            print(f"   📅 {activity_date} | {activity_type} | {distance_km}km")
            
            # Show additional stats if available
            if 'avg_speed_kmh' in metadata:
                avg_speed = metadata['avg_speed_kmh']
                print(f"   ⚡ {avg_speed}km/h", end="")
                
                if 'avg_hr_bpm' in metadata and metadata['avg_hr_bpm']:
                    avg_hr = metadata['avg_hr_bpm']
                    print(f" | 💓 {avg_hr}bpm", end="")
                
                if 'total_elevation_gain_m' in metadata:
                    elevation = metadata['total_elevation_gain_m']
                    print(f" | 🏔️ {elevation}m", end="")
                
                print()  # New line
            
            print()  # Blank line between results
            
    except Exception as e:
        print(f"❌ Error searching stories: {e}")

def demo_searches(collection):
    """Run a series of demo searches"""
    
    search_queries = [
        "long distance cycling endurance ride",
        "morning workout easy pace recovery",
        "challenging climb hill mountain",
        "high heart rate intense training",
        "short quick ride commute",
        "evening ride sunset beautiful weather",
        "winter cycling cold weather",
        "fast speed racing competitive",
        "relaxed leisurely ride fun",
        "training preparation fitness"
    ]
    
    for query in search_queries:
        search_stories(collection, query, n_results=3)
        print("\n" + "="*60 + "\n")

def interactive_search(collection):
    """Interactive search mode"""
    print("🎯 INTERACTIVE SEARCH MODE")
    print("Type your search queries (or 'quit' to exit):")
    print("-" * 40)
    
    while True:
        query = input("\n🔍 Search: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not query:
            continue
            
        search_stories(collection, query, n_results=5)

def collection_stats(collection):
    """Show collection statistics"""
    print("📊 COLLECTION STATISTICS")
    print("=" * 30)
    
    # Get all metadata
    all_data = collection.get()
    metadatas = all_data['metadatas']
    
    total_count = len(metadatas)
    print(f"Total Activities: {total_count}")
    
    # Activity types
    activity_types = {}
    effort_levels = {}
    years = {}
    
    for metadata in metadatas:
        # Activity types
        activity_type = metadata.get('activity_type', 'Unknown')
        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        # Effort levels
        effort_level = metadata.get('effort_level', 'Unknown')
        effort_levels[effort_level] = effort_levels.get(effort_level, 0) + 1
        
        # Years
        date_str = metadata.get('activity_date', '')
        if date_str:
            try:
                year = date_str.split('-')[0]
                years[year] = years.get(year, 0) + 1
            except (ValueError, IndexError):
                pass
    
    print("\nActivity Types:")
    for activity_type, count in sorted(activity_types.items()):
        print(f"  {activity_type}: {count}")
    
    print("\nEffort Levels:")
    for effort, count in sorted(effort_levels.items()):
        print(f"  {effort}: {count}")
    
    print("\nActivities by Year:")
    for year, count in sorted(years.items()):
        print(f"  {year}: {count}")
    
    print()

def main():
    """Main demo function"""
    print("🚴‍♂️ STRAVA ACTIVITY SEMANTIC SEARCH DEMO")
    print("=" * 45)
    
    # Connect to ChromaDB
    collection = connect_to_chromadb()
    if not collection:
        return
    
    # Show collection stats
    collection_stats(collection)
    
    # Menu
    while True:
        print("\n🎯 SEARCH DEMO OPTIONS:")
        print("1. Run demo searches")
        print("2. Interactive search")
        print("3. Show collection stats")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            print("\n🚀 Running demo searches...\n")
            demo_searches(collection)
        elif choice == '2':
            interactive_search(collection)
        elif choice == '3':
            collection_stats(collection)
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-4.")

if __name__ == "__main__":
    main()
