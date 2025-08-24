#!/usr/bin/env python3
"""
Interactive Activity Analyzer with ChromaDB and Ollama Integration

This script allows you to:
1. Pick an activity by ID
2. Generate its story
3. Search for similar activities in ChromaDB
4. Use Ollama with Llama3 to analyze the activity as a cycling coach expert
"""

import os
import json
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from .story_generator import StravaStoryGenerator

# Load environment variables
load_dotenv()

class InteractiveActivityAnalyzer:
    def __init__(self):
        """Initialize the activity analyzer."""
        self.story_generator = StravaStoryGenerator()
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
        self.ollama_port = os.getenv('OLLAMA_PORT', '11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3')
        self.max_similar_activities = int(os.getenv('MAX_SIMILAR_ACTIVITIES', '30'))
        
        print("🤖 Ollama configuration:")
        print(f"   Host: {self.ollama_host}")
        print(f"   Port: {self.ollama_port}")
        print(f"   Model: {self.ollama_model}")
        print(f"   Max similar activities: {self.max_similar_activities}")
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test if Ollama is available and warn if not."""
        # Try multiple host options for container environments
        host_options = [
            self.ollama_host,  # User-configured host
            'host.containers.internal',
            'host.docker.internal',
        ]
        
        successful_host = None
        
        for host in host_options:
            try:
                url = f"http://{host}:{self.ollama_port}/api/tags"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [model.get('name', '') for model in models]
                    
                    # Update the host to the working one
                    self.ollama_host = host
                    successful_host = host
                    
                    if any(self.ollama_model in name for name in model_names):
                        print(f"✅ Ollama is running with {self.ollama_model} model at {host}")
                    else:
                        print(f"⚠️  Ollama is running at {host} but {self.ollama_model} model not found")
                        print(f"   Available models: {', '.join(model_names) if model_names else 'None'}")
                        print(f"   Run: ollama pull {self.ollama_model}")
                    break
            except Exception:
                continue
        
        if not successful_host:
            print("⚠️  Ollama is not accessible - AI analysis will be skipped")
            print("   Tried hosts:", ', '.join(host_options))
            print("\n💡 To fix this issue:")
            print("   1. On Windows: Run 'start_ollama_for_containers.bat'")
            print("   2. Or manually: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve")
            print("   3. Make sure Windows Firewall allows port 11434")
            print("   4. Restart your containers after fixing Ollama")
    
    def load_activities(self):
        """Load activities data."""
        print("📊 Loading activity data...")
        self.story_generator.load_activities_and_streams()
        
        if not self.story_generator.connect_to_chromadb():
            print("❌ Failed to connect to ChromaDB. Some features may not work.")
            return False
        
        return True
    
    def list_available_activities(self, limit: int = 20):
        """List available activities for selection."""
        if self.story_generator.activities_df is None:
            print("❌ No activities loaded.")
            return
        
        df = self.story_generator.activities_df
        print(f"\n📋 Available Activities (showing first {limit}):")
        print("=" * 80)
        
        for idx, row in df.head(limit).iterrows():
            activity_id = row['id']
            name = row.get('name', 'Unnamed Activity')
            activity_type = row['type']
            date = row['start_date_local'].strftime('%Y-%m-%d %H:%M')
            distance = row['distance_km']
            
            print(f"{idx + 1:2d}. ID: {activity_id} | {name}")
            print(f"    {activity_type} | {date} | {distance:.1f}km")
            print("-" * 80)
    
    def get_activity_by_id(self, activity_id: str) -> Optional[Dict]:
        """Get activity data by ID."""
        if self.story_generator.activities_df is None:
            return None
        
        df = self.story_generator.activities_df
        activity_row = df[df['id'].astype(str) == str(activity_id)]
        
        if activity_row.empty:
            return None
        
        return activity_row.iloc[0].to_dict()
    
    def generate_activity_story(self, activity_data: Dict) -> str:
        """Generate story for the selected activity."""
        print(f"📝 Generating story for activity {activity_data['id']}...")
        
        # Convert dict back to Series for compatibility with story generator
        import pandas as pd
        activity_series = pd.Series(activity_data)
        
        story = self.story_generator.generate_activity_story(activity_series)
        return story
    
    def search_similar_activities(self, story: str, n_results: int = None) -> Dict:
        """Search for similar activities in ChromaDB."""
        if n_results is None:
            n_results = self.max_similar_activities
        
        print(f"🔍 Searching for up to {n_results} similar activities...")
        
        if not self.story_generator.collection:
            print("❌ ChromaDB collection not available.")
            return {}
        
        try:
            results = self.story_generator.collection.query(
                query_texts=[story],
                n_results=min(n_results, self.story_generator.collection.count())
            )
            
            print(f"✅ Found {len(results['documents'][0])} similar activities")
            return results
            
        except Exception as e:
            print(f"❌ Error searching for similar activities: {e}")
            return {}
    
    def call_ollama_analysis(self, current_story: str, similar_activities: Dict) -> str:
        """Call Ollama with Llama3 to analyze the activity."""
        print(f"🤖 Calling Ollama ({self.ollama_model}) for coaching analysis...")
        
        # Prepare the prompt for the cycling coach
        prompt = self._build_coaching_prompt(current_story, similar_activities)
        
        try:
            # Call Ollama API
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/generate"
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            analysis = result.get('response', 'No response received')
            
            print("✅ Analysis completed!")
            return analysis
            
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Error calling Ollama API: {e}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Unexpected error during analysis: {e}"
            print(error_msg)
            return error_msg
    
    def _build_coaching_prompt(self, current_story: str, similar_activities: Dict) -> str:
        """Build the prompt for the cycling coach analysis."""
        prompt = f"""You are an expert cycling coach with years of experience in training analysis and performance optimization. 

CURRENT ACTIVITY TO ANALYZE:
{current_story}

SIMILAR ACTIVITIES FOR COMPARISON:
"""
        
        # Add similar activities to the prompt
        if similar_activities and 'documents' in similar_activities and similar_activities['documents'][0]:
            for i, (doc, metadata) in enumerate(zip(
                similar_activities['documents'][0][:10],  # Limit to top 10 for prompt size
                similar_activities['metadatas'][0][:10]
            )):
                prompt += f"\n{i + 1}. {doc}"
                prompt += f"   (Date: {metadata.get('date', 'N/A')}, Distance: {metadata.get('distance_km', 0):.1f}km, "
                prompt += f"Speed: {metadata.get('avg_speed_kmh', 0):.1f}km/h, HR: {metadata.get('avg_hr_bpm', 0):.0f}bpm, "
                prompt += f"Effort: {metadata.get('effort_level', 'N/A')}, Terrain: {metadata.get('terrain_type', 'N/A')})"
        else:
            prompt += "\nNo similar activities found for comparison."
        
        prompt += f"""

COACHING ANALYSIS REQUEST:
As an expert cycling coach, please provide a comprehensive analysis of the current activity including:

1. **Performance Assessment**: 
   - Evaluate the effort level, pace, and heart rate data
   - Assess if the intensity was appropriate for the activity type and terrain

2. **Comparison with Similar Activities**:
   - How does this activity compare to similar rides in terms of performance?
   - Are there any trends or patterns you notice?
   - What improvements or concerns do you see?

3. **Training Insights**:
   - What does this activity tell us about the athlete's current fitness level?
   - Are there any red flags or positive indicators?

4. **Recommendations**:
   - What should the athlete focus on for future training?
   - Any specific advice for similar routes or conditions?
   - Recovery recommendations if needed

5. **Technical Analysis**:
   - Comment on pacing strategy
   - Heart rate zone distribution (if applicable)
   - Power/speed relationship for the terrain

Please provide specific, actionable advice based on the data. Be encouraging but honest about areas for improvement.
"""
        
        return prompt
    
    def _generate_basic_analysis(self, activity_data: Dict, similar_activities: Dict) -> str:
        """Generate basic analysis without AI when Ollama is not available."""
        analysis = []
        
        # Basic activity metrics
        distance = activity_data['distance_km']
        speed = activity_data['average_speed_kmh']
        activity_type = activity_data['type']
        elevation = activity_data.get('total_elevation_gain', 0)
        hr_avg = activity_data.get('hr_stream_avg', activity_data.get('average_heartrate', 0))
        
        analysis.append("## Performance Summary")
        analysis.append(f"- Activity Type: {activity_type}")
        analysis.append(f"- Distance: {distance:.1f}km")
        analysis.append(f"- Average Speed: {speed:.1f}km/h")
        if elevation > 0:
            analysis.append(f"- Elevation Gain: {elevation:.0f}m ({elevation/distance:.0f}m/km)")
        if hr_avg and hr_avg > 0:
            analysis.append(f"- Average Heart Rate: {hr_avg:.0f}bpm")
        
        # Speed analysis
        analysis.append("\n## Speed Analysis")
        if activity_type == 'Ride':
            if speed < 15:
                analysis.append("- Pace: Leisurely/Recovery ride")
            elif speed < 25:
                analysis.append("- Pace: Moderate endurance pace")
            elif speed < 35:
                analysis.append("- Pace: Strong/Tempo pace")
            else:
                analysis.append("- Pace: High intensity/Racing pace")
        elif activity_type == 'Run':
            if speed < 8:
                analysis.append("- Pace: Easy/Recovery run")
            elif speed < 12:
                analysis.append("- Pace: Moderate training pace")
            elif speed < 16:
                analysis.append("- Pace: Tempo/Threshold pace")
            else:
                analysis.append("- Pace: High intensity/Racing pace")
        
        # Terrain analysis
        if elevation > 0:
            analysis.append("\n## Terrain Analysis")
            elevation_per_km = elevation / distance
            if elevation_per_km < 5:
                analysis.append("- Terrain: Mostly flat with minimal climbing")
            elif elevation_per_km < 15:
                analysis.append("- Terrain: Rolling hills with moderate climbing")
            elif elevation_per_km < 30:
                analysis.append("- Terrain: Hilly with significant climbing")
            else:
                analysis.append("- Terrain: Mountainous with major climbing")
        
        # Comparison with similar activities
        if similar_activities and 'metadatas' in similar_activities:
            analysis.append("\n## Comparison with Similar Activities")
            metadatas = similar_activities['metadatas'][0][:5]  # Top 5 similar
            
            if metadatas:
                speeds = [m.get('avg_speed_kmh', 0) for m in metadatas if m.get('avg_speed_kmh', 0) > 0]
                hrs = [m.get('avg_hr_bpm', 0) for m in metadatas if m.get('avg_hr_bpm', 0) > 0]
                
                if speeds:
                    avg_similar_speed = sum(speeds) / len(speeds)
                    speed_diff = speed - avg_similar_speed
                    if abs(speed_diff) < 1:
                        analysis.append(f"- Speed: Consistent with similar activities ({avg_similar_speed:.1f}km/h average)")
                    elif speed_diff > 0:
                        analysis.append(f"- Speed: {speed_diff:.1f}km/h faster than similar activities")
                    else:
                        analysis.append(f"- Speed: {abs(speed_diff):.1f}km/h slower than similar activities")
                
                if hrs and hr_avg and hr_avg > 0:
                    avg_similar_hr = sum(hrs) / len(hrs)
                    hr_diff = hr_avg - avg_similar_hr
                    if abs(hr_diff) < 5:
                        analysis.append(f"- Heart Rate: Consistent with similar activities ({avg_similar_hr:.0f}bpm average)")
                    elif hr_diff > 0:
                        analysis.append(f"- Heart Rate: {hr_diff:.0f}bpm higher than similar activities")
                    else:
                        analysis.append(f"- Heart Rate: {abs(hr_diff):.0f}bpm lower than similar activities")
        
        analysis.append("\n## Recommendations")
        analysis.append("- For detailed AI-powered coaching insights, install and run Ollama with Llama3")
        analysis.append("- Monitor trends over time by comparing with similar activities")
        analysis.append("- Consider the terrain and conditions when evaluating performance")
        
        return "\n".join(analysis)
    
    def interactive_mode(self):
        """Run the interactive mode for activity analysis."""
        print("\n🚴‍♂️ Interactive Activity Analyzer Starting...")
        print("=" * 60)
        
        # Load activities
        if not self.load_activities():
            print("❌ Failed to load activities. Exiting.")
            return
        
        while True:
            print("\n📋 OPTIONS:")
            print("1. List available activities")
            print("2. Analyze activity by ID")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                limit = input("How many activities to show? (default 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                self.list_available_activities(limit)
                
            elif choice == '2':
                activity_id = input("Enter activity ID: ").strip()
                if activity_id:
                    self.analyze_activity(activity_id)
                else:
                    print("❌ Please enter a valid activity ID.")
                    
            elif choice == '3':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid option. Please select 1, 2, or 3.")
    
    def analyze_activity(self, activity_id: str, n_similar: int = None):
        """Analyze a specific activity by ID."""
        print(f"\n🔍 Analyzing activity ID: {activity_id}")
        print("=" * 60)
        
        # Get activity data
        activity_data = self.get_activity_by_id(activity_id)
        if not activity_data:
            print(f"❌ Activity with ID {activity_id} not found.")
            return
        
        # Display basic activity info
        print(f"📊 Activity: {activity_data.get('name', 'Unnamed Activity')}")
        print(f"🏃 Type: {activity_data['type']}")
        print(f"📅 Date: {activity_data['start_date_local']}")
        print(f"📏 Distance: {activity_data['distance_km']:.1f}km")
        print(f"⚡ Avg Speed: {activity_data['average_speed_kmh']:.1f}km/h")
        
        # Add heart rate if available
        hr_avg = activity_data.get('hr_stream_avg', activity_data.get('average_heartrate', 0))
        if hr_avg and hr_avg > 0:
            print(f"💓 Avg HR: {hr_avg:.0f}bpm")
        else:
            print("💓 Avg HR: No data")
        
        # Add elevation if available
        elevation = activity_data.get('total_elevation_gain', 0)
        if elevation > 0:
            print(f"🏔️ Elevation Gain: {elevation:.0f}m")
        
        # Generate story
        story = self.generate_activity_story(activity_data)
        print(f"\n📖 Generated Story:")
        print(f"{story}")
        
        # Search for similar activities
        if n_similar is None:
            n_similar = self.max_similar_activities
        
        similar_activities = self.search_similar_activities(story, n_similar)
        
        if similar_activities and 'documents' in similar_activities:
            print(f"\n🔍 Found {len(similar_activities['documents'][0])} similar activities")
            
            # Show top 5 similar activities
            print("\n🏃‍♂️ Top 5 Most Similar Activities:")
            for i, (doc, metadata) in enumerate(zip(
                similar_activities['documents'][0][:5],
                similar_activities['metadatas'][0][:5]
            )):
                print(f"\n{i + 1}. {doc}")
                print(f"   📅 {metadata.get('date', 'N/A')} | {metadata.get('activity_type', 'N/A')} | {metadata.get('distance_km', 0):.1f}km")
                print(f"   ⚡ {metadata.get('avg_speed_kmh', 0):.1f}km/h | 💓 {metadata.get('avg_hr_bpm', 0):.0f}bpm")
        
        # Get coaching analysis from Ollama
        print("\n🤖 Getting expert coaching analysis...")
        analysis = self.call_ollama_analysis(story, similar_activities)
        
        # Only show analysis if we got a valid response
        if not analysis.startswith("❌"):
            print("\n🏆 CYCLING COACH ANALYSIS:")
            print("=" * 60)
            print(analysis)
        else:
            print("\n⚠️  Ollama analysis unavailable:")
            print(analysis)
            print("\n💡 To enable AI coaching analysis:")
            print("   1. Install Ollama: https://ollama.ai")
            print("   2. Run: ollama pull llama3")
            print("   3. Ensure Ollama is running on localhost:11434")
            
            # Provide basic analysis without AI
            print("\n📊 BASIC ANALYSIS (without AI):")
            print("=" * 60)
            analysis = self._generate_basic_analysis(activity_data, similar_activities)
            print(analysis)
        
        # Save analysis to file
        self.save_analysis_report(activity_id, activity_data, story, similar_activities, analysis)
    
    def save_analysis_report(self, activity_id: str, activity_data: Dict, story: str, 
                           similar_activities: Dict, analysis: str):
        """Save the complete analysis report to a file."""
        # Extract timestamp safely
        try:
            if isinstance(activity_data['start_date_local'], str):
                timestamp = activity_data['start_date_local'][:10]  # YYYY-MM-DD
            else:
                # If it's a pandas Timestamp, convert to string
                timestamp = str(activity_data['start_date_local'])[:10]
        except (KeyError, TypeError, IndexError):
            timestamp = "unknown_date"
        
        filename = f"activity_analysis_{activity_id}_{timestamp}.md"
        filepath = Path("reports") / filename
        
        # Create reports directory if it doesn't exist
        filepath.parent.mkdir(exist_ok=True)
        
        # Build the report
        report = f"""# Activity Analysis Report

## Activity Details
- **ID**: {activity_id}
- **Name**: {activity_data.get('name', 'Unnamed Activity')}
- **Type**: {activity_data['type']}
- **Date**: {activity_data['start_date_local']}
- **Distance**: {activity_data['distance_km']:.1f}km
- **Average Speed**: {activity_data['average_speed_kmh']:.1f}km/h
- **Elevation Gain**: {activity_data.get('total_elevation_gain', 0):.0f}m

## Generated Story
{story}

## Similar Activities Found
"""
        
        if similar_activities and 'documents' in similar_activities:
            report += f"Found {len(similar_activities['documents'][0])} similar activities.\n\n"
            
            for i, (doc, metadata) in enumerate(zip(
                similar_activities['documents'][0][:10],
                similar_activities['metadatas'][0][:10]
            )):
                report += f"### {i + 1}. Similar Activity\n"
                report += f"- **Date**: {metadata.get('date', 'N/A')}\n"
                report += f"- **Type**: {metadata.get('activity_type', 'N/A')}\n"
                report += f"- **Distance**: {metadata.get('distance_km', 0):.1f}km\n"
                report += f"- **Speed**: {metadata.get('avg_speed_kmh', 0):.1f}km/h\n"
                report += f"- **HR**: {metadata.get('avg_hr_bpm', 0):.0f}bpm\n"
                report += f"- **Effort**: {metadata.get('effort_level', 'N/A')}\n"
                report += f"- **Story**: {doc}\n\n"
        else:
            report += "No similar activities found.\n\n"
        
        report += f"""## Expert Coaching Analysis
{analysis}

---
*Report generated by Interactive Activity Analyzer on {activity_data['start_date_local']}*
"""
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n💾 Analysis report saved to: {filepath}")
        except Exception as e:
            print(f"⚠️  Could not save report: {e}")

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description='Analyze Strava activities with AI coaching insights')
    parser.add_argument('--activity-id', '-a', type=str, help='Activity ID to analyze directly')
    parser.add_argument('--similar-count', '-s', type=int, default=30, 
                       help='Number of similar activities to find (default: 30)')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode')
    
    args = parser.parse_args()
    
    analyzer = InteractiveActivityAnalyzer()
    
    if args.activity_id:
        # Direct analysis mode
        if not analyzer.load_activities():
            print("❌ Failed to load activities. Exiting.")
            return 1
        
        analyzer.analyze_activity(args.activity_id, args.similar_count)
        
    elif args.interactive:
        # Interactive mode
        analyzer.interactive_mode()
        
    else:
        # Default: interactive mode
        analyzer.interactive_mode()
    
    return 0

if __name__ == "__main__":
    exit(main())
