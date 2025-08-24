#!/usr/bin/env python3
"""
Setup script for Athlete Insight Analytics Platform

This script helps users set up the environment and verify that everything is working.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_environment():
    """Check if environment is properly configured."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env file not found. Creating from .env.example...")
            try:
                import shutil
                shutil.copy(env_example, env_file)
                print("✅ .env file created. Please edit it with your settings.")
            except Exception as e:
                print(f"❌ Could not create .env file: {e}")
                return False
        else:
            print("⚠️  No .env file found. Creating basic template...")
            with open(env_file, 'w') as f:
                f.write("""# Athlete Insight Analytics Platform Configuration

# Ollama Configuration (for AI analysis)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Personal Configuration
USER_BIRTHYEAR=1990

# Search Configuration
MAX_SIMILAR_ACTIVITIES=30
""")
            print("✅ Basic .env file created. Please edit it with your settings.")
    
    print("✅ Environment configuration checked.")
    return True

def test_imports():
    """Test if critical modules can be imported."""
    print("\n🧪 Testing module imports...")
    
    modules = [
        ("pandas", "Data analysis"),
        ("numpy", "Numerical computing"),
        ("requests", "HTTP client"),
        ("chromadb", "Vector database"),
        ("dotenv", "Environment variables")
    ]
    
    all_good = True
    for module, description in modules:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError:
            print(f"❌ {module} - {description} (not installed)")
            all_good = False
    
    return all_good

def check_data_directory():
    """Check if data directory exists."""
    data_dir = Path("../activity_fetcher/data")
    if data_dir.exists():
        activities = list(data_dir.glob("individual_activities/*.json"))
        print(f"✅ Data directory found with {len(activities)} activity files.")
    else:
        print("⚠️  Data directory not found at ../activity_fetcher/data")
        print("   You may need to run the activity fetcher first.")
    
    return True

def run_basic_test():
    """Run a basic functionality test."""
    print("\n🚀 Running basic functionality test...")
    
    try:
        # Test the core modules
        sys.path.insert(0, "src")
        from core.story_generator import StravaStoryGenerator
        
        # Try to create an instance (this tests most imports)
        generator = StravaStoryGenerator()
        print("✅ Core modules load successfully!")
        
        return True
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚴‍♂️ Athlete Insight Analytics Platform Setup")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Environment", check_environment),
        ("Module Imports", test_imports),
        ("Data Directory", check_data_directory),
        ("Basic Test", run_basic_test)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 Setup completed successfully!")
        print("\n🚀 You can now run:")
        print("   python launcher.py    # Interactive launcher")
        print("   python main.py        # Main analyzer")
        print("   python examples/demo_analyzer.py  # Demo")
    else:
        print("⚠️  Setup completed with some issues.")
        print("   Please review the errors above and fix them.")
        print("   You can run this setup script again after fixing issues.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
