require('dotenv').config();
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

class StravaStreamFetcher {
    constructor() {
        this.accessToken = process.env.STRAVA_ACCESS_TOKEN;
        this.dataDir = process.env.DATA_DIR || './data';
        this.individualActivitiesDir = path.join(this.dataDir, 'individual_activities');
        this.requestCount = 0;
        
        if (!this.accessToken) {
            throw new Error('STRAVA_ACCESS_TOKEN is required. Please set it in your .env file');
        }
    }

    generateFilename(activity) {
        const date = new Date(activity.start_date).toISOString().split('T')[0];
        const sanitizedName = activity.name
            .replace(/[^a-zA-Z0-9\s-]/g, '') // Remove special characters
            .replace(/\s+/g, '_') // Replace spaces with underscores
            .substring(0, 50); // Limit length
        return `${activity.id}_${date}_${sanitizedName}.json`;
    }

    async makeRequest(url, options = {}) {
        this.requestCount++;
        
        try {
            const response = await axios({
                url,
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Accept': 'application/json',
                    ...options.headers
                },
                ...options
            });

            console.log(`📡 Request ${this.requestCount}: ${url}`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 429) {
                console.log('🛑 Rate limit exceeded by API response');
                throw new Error('Rate limit exceeded');
            }
            throw error;
        }
    }

    async fetchActivityStreams(activityId, streamTypes = ['time', 'latlng', 'heartrate']) {
        console.log(`🚀 Fetching streams for activity ${activityId}...`);
        console.log(`📊 Stream types: ${streamTypes.join(', ')}`);
        
        const url = `https://www.strava.com/api/v3/activities/${activityId}/streams`;
        const params = {
            keys: streamTypes.join(','),
            key_by_type: true
        };

        try {
            const streams = await this.makeRequest(url, { params });
            
            if (!streams || Object.keys(streams).length === 0) {
                console.log(`⚠️  No streams found for activity ${activityId}`);
                return null;
            }

            console.log(`✅ Found streams: ${Object.keys(streams).join(', ')}`);
            return streams;
        } catch (error) {
            console.error(`❌ Error fetching streams for activity ${activityId}:`, error.message);
            throw error;
        }
    }

    async fetchActivityDetails(activityId) {
        const url = `https://www.strava.com/api/v3/activities/${activityId}`;
        
        try {
            const activity = await this.makeRequest(url);
            console.log(`📋 Fetched activity details: ${activity.name}`);
            return activity;
        } catch (error) {
            console.error(`❌ Error fetching activity details for ${activityId}:`, error.message);
            throw error;
        }
    }

    async saveStreamData(activityId, streamType, streamData, activity) {
        // Generate filename using the same method as the main fetcher
        const baseFilename = this.generateFilename(activity);
        const streamFilename = baseFilename.replace('.json', `_streams_${streamType}.json`);
        const filepath = path.join(this.individualActivitiesDir, streamFilename);
        
        // Add metadata to the stream data
        const streamWithMeta = {
            activity_id: activityId,
            activity_name: activity.name,
            activity_date: activity.start_date,
            stream_type: streamType,
            data: streamData.data,
            series_type: streamData.series_type,
            original_size: streamData.original_size,
            resolution: streamData.resolution,
            _metadata: {
                fetched_date: new Date().toISOString(),
                file_name: streamFilename,
                fetcher_version: "1.0"
            }
        };
        
        try {
            await fs.writeFile(filepath, JSON.stringify(streamWithMeta, null, 2));
            console.log(`💾 Saved ${streamType} stream to ${streamFilename}`);
            return { filename: streamFilename, success: true };
        } catch (error) {
            console.error(`❌ Failed to save ${streamType} stream:`, error.message);
            return { filename: streamFilename, success: false, error: error.message };
        }
    }

    async fetchAndSaveStreams(activityId, streamTypes = ['time', 'latlng', 'heartrate']) {
        try {
            // Ensure data directory exists
            await fs.mkdir(this.individualActivitiesDir, { recursive: true });
            
            // First fetch activity details to get name and date for filename generation
            const activity = await this.fetchActivityDetails(activityId);
            
            // Fetch all streams for the activity
            const streams = await this.fetchActivityStreams(activityId, streamTypes);
            
            if (!streams) {
                return { success: false, message: 'No streams found' };
            }

            const results = {
                activity_id: activityId,
                activity_name: activity.name,
                streams_fetched: [],
                streams_saved: [],
                errors: []
            };

            // Save each stream type separately
            for (const [streamType, streamData] of Object.entries(streams)) {
                results.streams_fetched.push(streamType);
                
                const saveResult = await this.saveStreamData(activityId, streamType, streamData, activity);
                
                if (saveResult.success) {
                    results.streams_saved.push(streamType);
                } else {
                    results.errors.push({
                        stream_type: streamType,
                        error: saveResult.error
                    });
                }
            }

            console.log(`\n📊 Summary for activity ${activityId} (${activity.name}):`);
            console.log(`Streams fetched: ${results.streams_fetched.join(', ')}`);
            console.log(`Streams saved: ${results.streams_saved.join(', ')}`);
            if (results.errors.length > 0) {
                console.log(`Errors: ${results.errors.length}`);
            }
            console.log(`Total requests made: ${this.requestCount}`);

            return { success: true, results };
            
        } catch (error) {
            console.error(`❌ Error processing streams for activity ${activityId}:`, error.message);
            return { success: false, error: error.message };
        }
    }
}

async function main() {
    // Get activity ID from command line arguments
    const activityId = process.argv[2];
    
    if (!activityId) {
        console.log(`
🔧 Strava Stream Fetcher

Usage:
  node src/commands/fetch-streams.js <activity_id> [stream_types]

Examples:
  node src/commands/fetch-streams.js 15511022783
  node src/commands/fetch-streams.js 15511022783 time,latlng,heartrate
  node src/commands/fetch-streams.js 15511022783 time,latlng,heartrate,altitude,watts

Available stream types:
  - time: Time elapsed (seconds)
  - latlng: GPS coordinates [latitude, longitude]
  - heartrate: Heart rate (BPM)
  - altitude: Elevation (meters)
  - velocity_smooth: Smoothed velocity (m/s)
  - cadence: Pedaling/running cadence
  - watts: Power output (watts)
  - temp: Temperature
  - moving: Boolean indicating if moving
  - grade_smooth: Smoothed grade percentage

Files will be saved to: data/individual_activities/{activity_id}_{date}_{activity_name}_streams_{stream_type}.json
        `);
        process.exit(1);
    }

    // Parse stream types from command line (default: time, latlng, heartrate)
    let streamTypes = ['time', 'latlng', 'heartrate'];
    if (process.argv[3]) {
        streamTypes = process.argv[3].split(',').map(type => type.trim());
    }

    try {
        const fetcher = new StravaStreamFetcher();
        const result = await fetcher.fetchAndSaveStreams(activityId, streamTypes);
        
        if (result.success) {
            console.log(`\n✅ Successfully processed streams for activity ${activityId}`);
        } else {
            console.log(`\n❌ Failed to process streams: ${result.error || result.message}`);
            process.exit(1);
        }
    } catch (error) {
        console.error('❌ Application error:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = StravaStreamFetcher;
