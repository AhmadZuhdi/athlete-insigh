require('dotenv').config();
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

class BulkStreamFetcher {
    constructor() {
        this.accessToken = process.env.STRAVA_ACCESS_TOKEN;
        this.maxRequestsPer15Min = parseInt(process.env.MAX_REQUESTS_PER_15MIN) || 100;
        this.dataDir = process.env.DATA_DIR || './data';
        this.individualActivitiesDir = path.join(this.dataDir, 'individual_activities');
        this.metadataDir = path.join(this.dataDir, 'metadata');
        this.indexFile = path.join(this.metadataDir, 'activity_index.json');
        this.rateLimitFile = path.join(this.dataDir, 'rate_limit.json');
        this.requestCount = 0;
        this.windowStart = Date.now();
        this.defaultStreamTypes = ['time', 'latlng', 'heartrate'];
        
        if (!this.accessToken) {
            throw new Error('STRAVA_ACCESS_TOKEN is required. Please set it in your .env file');
        }
    }

    async initialize() {
        await this.loadRateLimitData();
    }

    async loadRateLimitData() {
        try {
            const data = await fs.readFile(this.rateLimitFile, 'utf8');
            const rateLimitData = JSON.parse(data);
            
            if (rateLimitData.nextAllowedTime && Date.now() < rateLimitData.nextAllowedTime) {
                const waitTime = rateLimitData.nextAllowedTime - Date.now();
                const waitMinutes = Math.ceil(waitTime / 1000 / 60);
                console.log(`🛑 Rate limit active. Need to wait ${waitMinutes} minutes until ${new Date(rateLimitData.nextAllowedTime).toLocaleTimeString()}`);
                process.exit(0);
            }
            
            // Reset if window has passed
            if (Date.now() - rateLimitData.windowStart > 15 * 60 * 1000) {
                this.requestCount = 0;
                this.windowStart = Date.now();
            } else {
                this.requestCount = rateLimitData.requestCount || 0;
                this.windowStart = rateLimitData.windowStart || Date.now();
            }
        } catch (error) {
            // File doesn't exist or is invalid, start fresh
            this.requestCount = 0;
            this.windowStart = Date.now();
        }
    }

    async saveRateLimitData() {
        const rateLimitData = {
            requestCount: this.requestCount,
            windowStart: this.windowStart,
            lastUpdate: Date.now(),
            nextAllowedTime: null
        };

        // If we hit the rate limit, calculate next allowed time
        if (this.requestCount >= this.maxRequestsPer15Min) {
            rateLimitData.nextAllowedTime = this.windowStart + (15 * 60 * 1000);
        }

        try {
            await fs.writeFile(this.rateLimitFile, JSON.stringify(rateLimitData, null, 2));
        } catch (error) {
            console.error('Error saving rate limit data:', error.message);
        }
    }

    checkRateLimit() {
        if (this.requestCount >= this.maxRequestsPer15Min) {
            const nextAllowedTime = this.windowStart + (15 * 60 * 1000);
            const waitTime = nextAllowedTime - Date.now();
            const waitMinutes = Math.ceil(waitTime / 1000 / 60);
            
            console.log(`🛑 Rate limit reached (${this.requestCount}/${this.maxRequestsPer15Min})`);
            console.log(`⏰ Next execution allowed at: ${new Date(nextAllowedTime).toLocaleTimeString()}`);
            console.log(`⏳ Wait time: ${waitMinutes} minutes`);
            
            return false;
        }
        return true;
    }

    async makeRequest(url, options = {}) {
        if (!this.checkRateLimit()) {
            await this.saveRateLimitData();
            process.exit(0);
        }

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

            console.log(`📡 Request ${this.requestCount}/${this.maxRequestsPer15Min}: ${url}`);
            
            // Check if we're approaching the limit
            if (this.requestCount >= this.maxRequestsPer15Min - 5) {
                console.log(`⚠️  Approaching rate limit: ${this.requestCount}/${this.maxRequestsPer15Min}`);
            }

            return response.data;
        } catch (error) {
            if (error.response?.status === 429) {
                console.log('🛑 Rate limit exceeded by API response');
                await this.saveRateLimitData();
                process.exit(0);
            }
            throw error;
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

    async loadActivityIndex() {
        try {
            const data = await fs.readFile(this.indexFile, 'utf8');
            const index = JSON.parse(data);
            console.log(`📖 Loaded ${index.length} activities from metadata index`);
            return index;
        } catch (error) {
            console.error('❌ Error loading activity index:', error.message);
            console.log('Make sure to run the main fetcher first: npm start');
            process.exit(1);
        }
    }

    async getExistingStreamFiles() {
        try {
            const files = await fs.readdir(this.individualActivitiesDir);
            const streamFiles = files.filter(file => file.includes('_streams_'));
            
            // Group by activity ID and stream type
            const streamsByActivity = {};
            
            for (const file of streamFiles) {
                const match = file.match(/^(\d+)_.*_streams_(.+)\.json$/);
                if (match) {
                    const [, activityId, streamType] = match;
                    if (!streamsByActivity[activityId]) {
                        streamsByActivity[activityId] = [];
                    }
                    streamsByActivity[activityId].push(streamType);
                }
            }
            
            console.log(`📁 Found existing stream files for ${Object.keys(streamsByActivity).length} activities`);
            return streamsByActivity;
        } catch (error) {
            console.error('Error reading stream files:', error.message);
            return {};
        }
    }

    async getActivitiesNeedingStreams(streamTypes = this.defaultStreamTypes) {
        const activityIndex = await this.loadActivityIndex();
        const existingStreams = await this.getExistingStreamFiles();
        
        const activitiesNeedingStreams = [];
        
        for (const activity of activityIndex) {
            const activityId = activity.id.toString();
            const existingStreamTypes = existingStreams[activityId] || [];
            
            // Check if any of the requested stream types are missing
            const missingStreams = streamTypes.filter(type => !existingStreamTypes.includes(type));
            
            if (missingStreams.length > 0) {
                activitiesNeedingStreams.push({
                    ...activity,
                    missing_streams: missingStreams,
                    existing_streams: existingStreamTypes
                });
            }
        }
        
        console.log(`🔍 Found ${activitiesNeedingStreams.length} activities missing stream data`);
        return activitiesNeedingStreams;
    }

    async fetchActivityStreams(activityId, streamTypes) {
        const url = `https://www.strava.com/api/v3/activities/${activityId}/streams`;
        const params = {
            keys: streamTypes.join(','),
            key_by_type: true
        };

        try {
            const streams = await this.makeRequest(url, { params });
            return streams;
        } catch (error) {
            console.error(`❌ Error fetching streams for activity ${activityId}:`, error.message);
            return null;
        }
    }

    async saveStreamData(activity, streamType, streamData) {
        // Generate filename using the same method as the main fetcher
        const baseFilename = this.generateFilename(activity);
        const streamFilename = baseFilename.replace('.json', `_streams_${streamType}.json`);
        const filepath = path.join(this.individualActivitiesDir, streamFilename);
        
        // Add metadata to the stream data
        const streamWithMeta = {
            activity_id: activity.id,
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
            return { filename: streamFilename, success: true };
        } catch (error) {
            console.error(`❌ Failed to save ${streamType} stream:`, error.message);
            return { filename: streamFilename, success: false, error: error.message };
        }
    }

    async fetchStreamsForActivity(activity, streamTypes) {
        const activityId = activity.id;
        
        try {
            console.log(`\n🏃 Processing: ${activity.name} (${activityId})`);
            console.log(`📊 Fetching streams: ${streamTypes.join(', ')}`);
            
            const streams = await this.fetchActivityStreams(activityId, streamTypes);
            
            if (!streams || Object.keys(streams).length === 0) {
                console.log(`⚠️  No streams available for activity ${activityId}`);
                return { success: false, reason: 'No streams available' };
            }

            const results = {
                activity_id: activityId,
                streams_fetched: [],
                streams_saved: [],
                errors: []
            };

            // Save each stream type separately
            for (const [streamType, streamData] of Object.entries(streams)) {
                results.streams_fetched.push(streamType);
                
                const saveResult = await this.saveStreamData(activity, streamType, streamData);
                
                if (saveResult.success) {
                    results.streams_saved.push(streamType);
                    console.log(`💾 Saved ${streamType} stream`);
                } else {
                    results.errors.push({
                        stream_type: streamType,
                        error: saveResult.error
                    });
                }
            }

            return { success: true, results };
            
        } catch (error) {
            console.error(`❌ Error processing streams for activity ${activityId}:`, error.message);
            return { success: false, error: error.message };
        }
    }

    async fetchAllMissingStreams(streamTypes = this.defaultStreamTypes) {
        console.log('🚀 Starting bulk stream fetching...');
        console.log(`📊 Target stream types: ${streamTypes.join(', ')}`);
        
        const activitiesNeedingStreams = await this.getActivitiesNeedingStreams(streamTypes);
        
        if (activitiesNeedingStreams.length === 0) {
            console.log('✅ All activities already have the requested stream data!');
            return;
        }

        const stats = {
            total_activities: activitiesNeedingStreams.length,
            processed: 0,
            successful: 0,
            failed: 0,
            streams_saved: 0,
            start_time: new Date().toISOString()
        };

        console.log(`\n🎯 Processing ${stats.total_activities} activities...`);

        for (let i = 0; i < activitiesNeedingStreams.length; i++) {
            const activity = activitiesNeedingStreams[i];
            
            if (!this.checkRateLimit()) {
                console.log(`🛑 Rate limit reached. Processed ${stats.processed}/${stats.total_activities} activities`);
                break;
            }

            const result = await this.fetchStreamsForActivity(activity, activity.missing_streams);
            stats.processed++;
            
            if (result.success) {
                stats.successful++;
                stats.streams_saved += result.results.streams_saved.length;
            } else {
                stats.failed++;
                console.log(`❌ Failed to process ${activity.name}: ${result.error || result.reason}`);
            }

            // Progress update every 10 activities
            if (stats.processed % 10 === 0) {
                console.log(`📈 Progress: ${stats.processed}/${stats.total_activities} activities processed`);
                console.log(`   ✅ Successful: ${stats.successful}, ❌ Failed: ${stats.failed}`);
                console.log(`   💾 Streams saved: ${stats.streams_saved}`);
            }

            // Small delay to be respectful to the API
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        // Final summary
        stats.end_time = new Date().toISOString();
        await this.saveRateLimitData();

        console.log(`\n📊 Bulk Stream Fetching Summary:`);
        console.log(`Total activities processed: ${stats.processed}/${stats.total_activities}`);
        console.log(`Successful: ${stats.successful}`);
        console.log(`Failed: ${stats.failed}`);
        console.log(`Streams saved: ${stats.streams_saved}`);
        console.log(`API requests made: ${this.requestCount}/${this.maxRequestsPer15Min}`);
        
        if (this.requestCount >= this.maxRequestsPer15Min) {
            const nextAllowedTime = this.windowStart + (15 * 60 * 1000);
            console.log(`⏰ Next execution allowed at: ${new Date(nextAllowedTime).toLocaleTimeString()}`);
        }
    }
}

async function main() {
    // Parse stream types from command line (default: time, latlng, heartrate)
    let streamTypes = ['time', 'latlng', 'heartrate'];
    if (process.argv[2]) {
        if (process.argv[2] === '--help' || process.argv[2] === '-h') {
            console.log(`
🔧 Bulk Strava Stream Fetcher

Usage:
  node src/commands/fetch-all-streams.js [stream_types]

Examples:
  node src/commands/fetch-all-streams.js
  node src/commands/fetch-all-streams.js time,latlng,heartrate
  node src/commands/fetch-all-streams.js time,latlng,heartrate,altitude,watts

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

This script will:
1. Check all activities in your index
2. Identify which activities are missing the specified stream types
3. Fetch and save missing streams only
4. Respect rate limits and save progress
            `);
            process.exit(0);
        }
        streamTypes = process.argv[2].split(',').map(type => type.trim());
    }

    try {
        const fetcher = new BulkStreamFetcher();
        await fetcher.initialize();
        await fetcher.fetchAllMissingStreams(streamTypes);
    } catch (error) {
        console.error('❌ Application error:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = BulkStreamFetcher;
