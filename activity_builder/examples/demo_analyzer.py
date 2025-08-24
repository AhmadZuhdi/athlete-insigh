#!/usr/bin/env python3
"""
Demo script for the Interactive Activity Analyzer

This script demonstrates how to use the analyzer programmatically
and shows example usage patterns.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.interactive_analyzer import InteractiveActivityAnalyzer

# Load environment variables
load_dotenv()

def demo_analysis():
    """Demonstrate the analyzer with example usage."""
    print("🚴‍♂️ Interactive Activity Analyzer Demo")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = InteractiveActivityAnalyzer()
    
    # Load activities
    print("\n1. Loading activity data...")
    if not analyzer.load_activities():
        print("❌ Failed to load activities. Make sure your data path is correct.")
        return
    
    # Show available activities
    print("\n2. Available activities (first 10):")
    analyzer.list_available_activities(10)
    
    # Get the first activity for demo
    if analyzer.story_generator.activities_df is not None:
        df = analyzer.story_generator.activities_df
        if not df.empty:
            first_activity_id = str(df.iloc[0]['id'])
            
            print(f"\n3. Demo analysis of activity ID: {first_activity_id}")
            analyzer.analyze_activity(first_activity_id, n_similar=10)
        else:
            print("❌ No activities found in the dataset.")
    else:
        print("❌ No activity data loaded.")

def check_requirements():
    """Check if all required services are available."""
    print("🔍 Checking Requirements...")
    print("=" * 30)
    
    # Check environment variables
    required_vars = ['USER_BIRTHYEAR', 'STRAVA_DATA_PATH']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file.")
    else:
        print("✅ Environment variables configured")
    
    # Check Ollama
    try:
        import requests
        ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
        ollama_port = os.getenv('OLLAMA_PORT', '11434')
        
        response = requests.get(f"http://{ollama_host}:{ollama_port}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            
            # Check if llama3 model is available
            models = response.json().get('models', [])
            llama3_available = any('llama3' in model.get('name', '') for model in models)
            
            if llama3_available:
                print("✅ Llama3 model is available")
            else:
                print("⚠️  Llama3 model not found. Run: ollama pull llama3")
        else:
            print("❌ Ollama is not responding properly")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
    
    # Check ChromaDB
    try:
        import chromadb
        chroma_host = os.getenv('CHROMA_HOST', 'localhost')
        chroma_port = int(os.getenv('CHROMA_PORT', '8000'))
        
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        client.heartbeat()
        print("✅ ChromaDB is running")
    except Exception as e:
        print(f"❌ Cannot connect to ChromaDB: {e}")

def main():
    """Main demo function."""
    print("🎯 Interactive Activity Analyzer - Demo & Requirements Check")
    print("=" * 70)
    
    # Check requirements first
    check_requirements()
    
    # Ask if user wants to continue with demo
    print("\n" + "=" * 70)
    choice = input("Do you want to run the demo analysis? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        demo_analysis()
    else:
        print("👋 Demo skipped. Use 'python interactive_analyzer.py' to start the analyzer.")

if __name__ == "__main__":
    main()
