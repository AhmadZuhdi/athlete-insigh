#!/usr/bin/env python3
"""
Quick launcher for the Activity Analyzer

This script provides a simple way to launch different components.
"""

import sys
import subprocess
from pathlib import Path

def show_menu():
    """Show the main menu."""
    print("\n🚴‍♂️ Athlete Insight Analytics Platform")
    print("=" * 50)
    print("1. Interactive Activity Analyzer (main app)")
    print("2. Demo Analyzer")
    print("3. Search Demo")
    print("4. Quick Stats")
    print("5. Test Setup")
    print("6. Exit")
    print("=" * 50)

def main():
    """Main launcher function."""
    while True:
        show_menu()
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            subprocess.run([sys.executable, "main.py"])
        elif choice == '2':
            subprocess.run([sys.executable, "examples/demo_analyzer.py"])
        elif choice == '3':
            subprocess.run([sys.executable, "examples/search_demo.py"])
        elif choice == '4':
            subprocess.run([sys.executable, "src/utils/quick_stats.py"])
        elif choice == '5':
            subprocess.run([sys.executable, "src/utils/test_setup.py"])
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-6.")

if __name__ == "__main__":
    main()
