#!/usr/bin/env python3
"""
Athlete Insight Analytics Platform - Main Entry Point

This is the main entry point for the interactive activity analyzer.
Run this script to start the analysis tool.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point for the application."""
    try:
        from core.interactive_analyzer import InteractiveActivityAnalyzer
        
        # Create and run the analyzer
        analyzer = InteractiveActivityAnalyzer()
        analyzer.interactive_mode()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed all dependencies:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
