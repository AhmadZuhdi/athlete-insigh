# Interactive Activity Analyzer

An intelligent cycling activity analyzer that combines Strava data with AI-powered coaching insights using ChromaDB for semantic search and Ollama with Llama3 for expert analysis.

## Features

- 🚴‍♂️ **Interactive Activity Selection**: Browse and select activities by ID
- 📖 **Story Generation**: Convert raw activity data into natural language stories
- 🔍 **Semantic Search**: Find similar activities using ChromaDB vector database
- 🤖 **AI Coaching Analysis**: Get expert cycling coach insights using Ollama with Llama3
- 📊 **Comprehensive Reports**: Generate detailed analysis reports in Markdown format

## Prerequisites

1. **Python Environment**: Python 3.8+
2. **ChromaDB**: Running ChromaDB instance
3. **Ollama**: Local Ollama installation with Llama3 model
4. **Strava Data**: Activity data from the activity_fetcher

## Installation

1. Install Python dependencies:
```bash
pip install pandas numpy chromadb requests python-dotenv
```

2. Install and start Ollama:
```bash
# Install Ollama (visit https://ollama.ai)
ollama pull llama3
```

3. Start ChromaDB (if using Docker):
```bash
docker run -p 8000:8000 chromadb/chroma
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Required
USER_BIRTHYEAR=1990                    # Your birth year for HR zone calculations
STRAVA_DATA_PATH=../activity_fetcher/data/individual_activities

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3

# Analysis Configuration
MAX_SIMILAR_ACTIVITIES=30
```

## Usage

### Interactive Mode (Default)
```bash
python interactive_analyzer.py
```

This will start an interactive session where you can:
1. List available activities
2. Select an activity by ID for analysis
3. Get AI-powered coaching insights

### Direct Analysis Mode
```bash
# Analyze a specific activity by ID
python interactive_analyzer.py --activity-id 12345678

# Specify number of similar activities to find
python interactive_analyzer.py --activity-id 12345678 --similar-count 50
```

### Command Line Options
- `--activity-id, -a`: Activity ID to analyze directly
- `--similar-count, -s`: Number of similar activities to find (default: 30)
- `--interactive, -i`: Force interactive mode

## How It Works

1. **Data Loading**: Loads Strava activity data and stream analytics
2. **Story Generation**: Converts activity metrics into natural language using the story generator
3. **Semantic Search**: Uses ChromaDB to find similar activities based on story content
4. **AI Analysis**: Sends the current activity and similar activities to Ollama for expert coaching analysis
5. **Report Generation**: Creates a comprehensive analysis report in Markdown format

## Example Analysis Flow

```
🔍 Analyzing activity ID: 12345678
📊 Activity: Morning Ride
🏃 Type: Ride
📅 Date: 2024-01-15 08:30:00
📏 Distance: 45.2km
⚡ Avg Speed: 28.5km/h

📖 Generated Story:
A 45.2km cycling ride with 650m of climbing at an average speed of 28.5 km/h 
and an average heart rate of 165 bpm. Took place on a sunny morning in winter. 
Felt challenging on the climbs. Heart rate data shows consistent effort.

🔍 Found 25 similar activities

🤖 Getting expert coaching analysis...
✅ Analysis completed!

🏆 CYCLING COACH ANALYSIS:
Based on your activity data, I can see this was a solid endurance ride...
[Detailed AI analysis follows]

💾 Analysis report saved to: reports/activity_analysis_12345678_2024-01-15.md
```

## Output

The analyzer generates:
- **Console Output**: Real-time analysis progress and results
- **Markdown Reports**: Saved in `reports/` directory with detailed analysis
- **Similar Activities**: List of comparable activities with metadata

## Expert Coaching Analysis

The AI coach analyzes:
- **Performance Assessment**: Effort level, pace, and heart rate evaluation
- **Comparison Analysis**: How the activity compares to similar rides
- **Training Insights**: Fitness level indicators and patterns
- **Recommendations**: Specific advice for future training
- **Technical Analysis**: Pacing strategy and heart rate zones

## Troubleshooting

### ChromaDB Connection Issues
- Ensure ChromaDB is running on the specified host/port
- Check firewall settings
- Verify ChromaDB container health

### Ollama Connection Issues
- Ensure Ollama is installed and running
- Verify the Llama3 model is downloaded: `ollama pull llama3`
- Check Ollama service status

### Activity Data Issues
- Ensure activity data exists in the specified path
- Check that the story generator has been run to populate ChromaDB
- Verify activity ID format (should be numeric)

## Dependencies

- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `chromadb`: Vector database for semantic search
- `requests`: HTTP client for Ollama API calls
- `python-dotenv`: Environment variable management

## Related Components

- `story_generator.py`: Generates natural language stories from activity data
- `activity_analyzer.py`: Statistical analysis of activity data
- ChromaDB: Vector database for storing and searching activity stories
- Ollama: Local LLM inference server for AI coaching analysis
