# 📁 Project Structure

This document describes the reorganized folder structure of the Athlete Insight Analytics Platform.

## 🗂️ Directory Structure

```
activity_builder/
├── 📁 src/                          # Source code
│   ├── 📁 core/                     # Core application modules
│   │   ├── interactive_analyzer.py  # Main interactive analyzer
│   │   ├── story_generator.py       # Activity story generation
│   │   └── __init__.py              # Package initialization
│   ├── 📁 utils/                    # Utility modules
│   │   ├── quick_stats.py           # Quick statistics utilities
│   │   ├── web_search.py            # Web search functionality
│   │   ├── test_setup.py            # Test setup utilities
│   │   └── __init__.py              # Package initialization
│   └── __init__.py                  # Main package initialization
├── 📁 examples/                     # Example scripts and demos
│   ├── demo_analyzer.py             # Demo usage of the analyzer
│   └── search_demo.py               # Search functionality demo
├── 📁 legacy/                       # Legacy/deprecated code
│   ├── activity_analyzer.py         # Original activity analyzer
│   └── enhanced_analyzer.py         # Enhanced analyzer (superseded)
├── 📁 docker/                       # Docker configuration
│   ├── Dockerfile                   # Container definition
│   └── compose.yml                  # Docker Compose configuration
├── 📁 data/                         # Data files and outputs
│   ├── activity_analysis.csv        # Basic analysis results
│   └── enhanced_activity_analysis.csv # Enhanced analysis results
├── 📁 scripts/                      # Shell scripts and utilities
│   └── test_ollama_connectivity.sh  # Ollama connectivity test
├── 📁 reports/                      # Generated analysis reports
│   └── *.md                         # Individual activity reports
├── main.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── README.md                        # Main documentation
└── README_structure.md              # This file
```

## 🚀 How to Run

### Quick Start
```bash
# Run the interactive analyzer
python main.py

# Or run directly from source
python -m src.core.interactive_analyzer
```

### Using Docker
```bash
# Start with Docker Compose
cd docker
docker-compose up -d

# Run the analyzer in container
docker exec -it python-app python main.py
```

## 📦 Package Structure

### Core Modules (`src/core/`)
- **`interactive_analyzer.py`**: Main application with CLI interface
- **`story_generator.py`**: Converts activity data to natural language stories

### Utilities (`src/utils/`)
- **`quick_stats.py`**: Statistical analysis tools
- **`web_search.py`**: Web search integration
- **`test_setup.py`**: Testing and setup utilities

### Examples (`examples/`)
- **`demo_analyzer.py`**: Shows how to use the analyzer programmatically
- **`search_demo.py`**: Demonstrates search functionality

### Legacy (`legacy/`)
- Contains older versions of analyzers that have been superseded
- Kept for reference and backward compatibility

## 🔧 Development

### Adding New Features
1. Core functionality goes in `src/core/`
2. Utilities and helpers go in `src/utils/`
3. Examples and demos go in `examples/`

### Import Structure
```python
# Import from core modules
from src.core.interactive_analyzer import InteractiveActivityAnalyzer
from src.core.story_generator import StravaStoryGenerator

# Import utilities
from src.utils.quick_stats import generate_stats
```

### Running Examples
```bash
# From the root directory
python examples/demo_analyzer.py
python examples/search_demo.py
```

## 🐳 Docker Configuration

The Docker setup has been updated to work with the new structure:
- Build context is now from the parent directory
- Source code is properly copied into the container
- Environment variables are preserved

## 📊 Data Organization

- **Raw analysis data**: `data/` directory
- **Generated reports**: `reports/` directory  
- **External data**: Linked from `../activity_fetcher/data/`

## 🔄 Migration Notes

If you have existing scripts that import the old modules directly:

**Old way:**
```python
from interactive_analyzer import InteractiveActivityAnalyzer
```

**New way:**
```python
from src.core.interactive_analyzer import InteractiveActivityAnalyzer
# or use the main entry point
python main.py
```

## 🎯 Benefits of New Structure

1. **Better Organization**: Clear separation of concerns
2. **Easier Maintenance**: Related code is grouped together
3. **Cleaner Root Directory**: Less clutter in the main folder
4. **Package Structure**: Proper Python package with imports
5. **Docker Integration**: Optimized container builds
6. **Legacy Support**: Old code preserved but separated
