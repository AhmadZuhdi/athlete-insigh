#!/usr/bin/env python3
"""
Simple Web Interface for Strava Activity Search
"""

from flask import Flask, render_template, request, jsonify
import chromadb
import json
from datetime import datetime

app = Flask(__name__)

def get_chromadb_collection():
    """Get ChromaDB collection"""
    try:
        client = chromadb.HttpClient(host="chromadb", port=8000)
        collection = client.get_collection(name="strava_activity_stories")
        return collection
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        return None

@app.route('/')
def index():
    """Home page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Strava Activity Search</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 { 
                color: #333; 
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5rem;
            }
            .search-box {
                display: flex;
                gap: 10px;
                margin-bottom: 30px;
            }
            input[type="text"] { 
                flex: 1;
                padding: 15px; 
                border: 2px solid #ddd; 
                border-radius: 8px;
                font-size: 16px;
                outline: none;
                transition: border-color 0.3s;
            }
            input[type="text"]:focus {
                border-color: #667eea;
            }
            button { 
                padding: 15px 25px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                border: none; 
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            .result {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .result-story {
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 15px;
                color: #333;
            }
            .result-meta {
                font-size: 14px;
                color: #666;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }
            .loading {
                text-align: center;
                color: #666;
                font-style: italic;
            }
            .suggestions {
                margin-top: 20px;
            }
            .suggestion-chips {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }
            .chip {
                background: #e9ecef;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
                border: 1px solid transparent;
            }
            .chip:hover {
                background: #667eea;
                color: white;
                transform: translateY(-1px);
            }
            .stats {
                background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }
            .emoji { font-size: 1.2em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚴‍♂️ Strava Activity Search</h1>
            
            <div class="stats" id="stats">
                <div class="loading">Loading collection stats...</div>
            </div>
            
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search your activities... (e.g., 'challenging climb', 'morning ride', 'high heart rate')" />
                <button onclick="search()">🔍 Search</button>
            </div>
            
            <div class="suggestions">
                <strong>Try these searches:</strong>
                <div class="suggestion-chips">
                    <span class="chip" onclick="searchFor('long distance endurance ride')">🚴‍♂️ Long distance</span>
                    <span class="chip" onclick="searchFor('challenging climb mountain')">🏔️ Challenging climbs</span>
                    <span class="chip" onclick="searchFor('high heart rate intense')">💓 High intensity</span>
                    <span class="chip" onclick="searchFor('morning workout easy pace')">🌅 Morning rides</span>
                    <span class="chip" onclick="searchFor('fast speed racing')">⚡ Fast rides</span>
                    <span class="chip" onclick="searchFor('winter cold weather')">❄️ Winter cycling</span>
                </div>
            </div>
            
            <div id="results"></div>
        </div>

        <script>
            // Load stats on page load
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = `
                        <strong>📊 Collection: ${data.total_activities} activities</strong><br>
                        <span class="emoji">🚴‍♂️</span> ${data.activity_types.Ride || 0} rides | 
                        <span class="emoji">🏃‍♂️</span> ${data.activity_types.Run || 0} runs | 
                        <span class="emoji">🚶‍♂️</span> ${data.activity_types.Walk || 0} walks
                    `;
                })
                .catch(err => {
                    document.getElementById('stats').innerHTML = '<div class="error">Could not load stats</div>';
                });

            function searchFor(query) {
                document.getElementById('searchInput').value = query;
                search();
            }

            function search() {
                const query = document.getElementById('searchInput').value.trim();
                if (!query) return;

                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading">🔍 Searching...</div>';

                fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({query: query})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        resultsDiv.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                        return;
                    }

                    if (data.results.length === 0) {
                        resultsDiv.innerHTML = '<div class="loading">No results found. Try a different search term.</div>';
                        return;
                    }

                    let html = `<h3>🎯 Found ${data.results.length} matching activities:</h3>`;
                    data.results.forEach((result, i) => {
                        const meta = result.metadata;
                        let metaText = `📅 ${meta.activity_date || 'Unknown date'} | ${meta.activity_type || 'Unknown'} | ${(meta.distance_km || 0).toFixed(1)}km`;
                        
                        if (meta.avg_speed_kmh) {
                            metaText += ` | ⚡ ${meta.avg_speed_kmh.toFixed(1)}km/h`;
                        }
                        if (meta.avg_hr_bpm) {
                            metaText += ` | 💓 ${Math.round(meta.avg_hr_bpm)}bpm`;
                        }
                        if (meta.total_elevation_gain_m) {
                            metaText += ` | 🏔️ ${Math.round(meta.total_elevation_gain_m)}m`;
                        }

                        html += `
                            <div class="result">
                                <div class="result-story">${result.story}</div>
                                <div class="result-meta">${metaText}</div>
                            </div>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                })
                .catch(err => {
                    resultsDiv.innerHTML = '<div class="error">❌ Search failed. Please try again.</div>';
                });
            }

            // Enable Enter key search
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    search();
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/search', methods=['POST'])
def search():
    """Search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'})
        
        collection = get_chromadb_collection()
        if not collection:
            return jsonify({'error': 'Could not connect to database'})
        
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if not results['documents'] or not results['documents'][0]:
            return jsonify({'results': []})
        
        formatted_results = []
        for story, metadata in zip(results['documents'][0], results['metadatas'][0]):
            formatted_results.append({
                'story': story,
                'metadata': metadata
            })
        
        return jsonify({'results': formatted_results})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/stats')
def stats():
    """Get collection statistics"""
    try:
        collection = get_chromadb_collection()
        if not collection:
            return jsonify({'error': 'Could not connect to database'})
        
        all_data = collection.get()
        metadatas = all_data['metadatas']
        
        activity_types = {}
        for metadata in metadatas:
            activity_type = metadata.get('activity_type', 'Unknown')
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        return jsonify({
            'total_activities': len(metadatas),
            'activity_types': activity_types
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
