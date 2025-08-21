require('dotenv').config();
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

class StravaActivityFetcher {
    constructor() {
        this.accessToken = process.env.STRAVA_ACCESS_TOKEN;
        this.maxRequestsPer15Min = parseInt(process.env.MAX_REQUESTS_PER_15MIN) || 100;
        this.dataDir = process.env.DATA_DIR || './data';
        this.individualActivitiesDir = path.join(this.dataDir, 'individual_activities');
        this.metadataDir = path.join(this.dataDir, 'metadata');
        this.rateLimitFile = path.join(this.dataDir, 'rate_limit.json');
        this.activitiesFile = path.join(this.dataDir, 'activities.json'); // Keep for backward compatibility
        this.indexFile = path.join(this.metadataDir, 'activity_index.json');
        this.summaryFile = path.join(this.metadataDir, 'fetcher_summary.json');
        this.requestCount = 0;
        this.windowStart = Date.now();
        
        if (!this.accessToken) {
            throw new Error('STRAVA_ACCESS_TOKEN is required. Please set it in your .env file');
        }
    }

    async initialize() {
        // Create data directories if they don't exist
        try {
            await fs.mkdir(this.dataDir, { recursive: true });
            await fs.mkdir(this.individualActivitiesDir, { recursive: true });
            await fs.mkdir(this.metadataDir, { recursive: true });
        } catch (error) {
            console.error('Error creating data directories:', error.message);
        }

        // Load existing rate limit data
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

    async loadExistingActivities() {
        try {
            // Try to load from new metadata location first
            const data = await fs.readFile(this.indexFile, 'utf8');
            const index = JSON.parse(data);
            console.log(`📖 Loaded ${index.length} existing activities from metadata index`);
            return index;
        } catch (error) {
            // Fallback: try old location
            try {
                const oldIndexFile = path.join(this.individualActivitiesDir, '_activity_index.json');
                const data = await fs.readFile(oldIndexFile, 'utf8');
                const index = JSON.parse(data);
                console.log(`📖 Loaded ${index.length} existing activities from legacy index (will migrate)`);
                
                // Migrate to new location
                await this.saveActivitiesIndex(index);
                console.log(`📋 Migrated index to metadata folder`);
                
                return index;
            } catch (legacyError) {
                // Final fallback: try to load from old activities.json file
                try {
                    const data = await fs.readFile(this.activitiesFile, 'utf8');
                    const activities = JSON.parse(data);
                    console.log(`📖 Loaded ${activities.length} existing activities from legacy activities.json`);
                    // Convert to index format for consistency
                    return activities.map((activity, index) => ({
                        id: activity.id,
                        name: activity.name,
                        type: activity.type,
                        sport_type: activity.sport_type,
                        start_date: activity.start_date,
                        distance: activity.distance,
                        moving_time: activity.moving_time,
                        file_index: index,
                        filename: this.generateFilename(activity)
                    }));
                } catch (finalError) {
                    console.log('📝 No existing activities found, starting fresh');
                    return [];
                }
            }
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

    async saveIndividualActivity(activity, fileIndex) {
        const filename = this.generateFilename(activity);
        const filepath = path.join(this.individualActivitiesDir, filename);
        
        // Add metadata to the activity
        const activityWithMeta = {
            ...activity,
            _metadata: {
                fetched_date: new Date().toISOString(),
                file_index: fileIndex,
                file_name: filename,
                fetcher_version: "2.0"
            }
        };
        
        try {
            await fs.writeFile(filepath, JSON.stringify(activityWithMeta, null, 2));
            return { filename, success: true };
        } catch (error) {
            console.error(`❌ Failed to save activity ${activity.id}:`, error.message);
            return { filename, success: false, error: error.message };
        }
    }

    async saveActivitiesIndex(activities) {
        try {
            await fs.writeFile(this.indexFile, JSON.stringify(activities, null, 2));
            console.log(`� Saved activity index with ${activities.length} activities`);
        } catch (error) {
            console.error('Error saving activity index:', error.message);
        }
    }

    async saveFetcherSummary(summary) {
        try {
            await fs.writeFile(this.summaryFile, JSON.stringify(summary, null, 2));
        } catch (error) {
            console.error('Error saving fetcher summary:', error.message);
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

    async fetchActivities(page = 1, perPage = 30) {
        const url = `https://www.strava.com/api/v3/athlete/activities`;
        const params = {
            page,
            per_page: perPage
        };

        const activities = await this.makeRequest(url, { params });
        return activities;
    }

    async fetchAllActivities() {
        console.log('🚀 Starting Strava activity fetch...');
        
        let allActivitiesIndex = await this.loadExistingActivities();
        let page = 1;
        const perPage = 30;
        let hasMore = true;
        
        // Get existing activity IDs to avoid duplicates
        const existingIds = new Set(allActivitiesIndex.map(activity => activity.id));
        let newActivitiesCount = 0;
        let saveErrors = 0;
        const fetchStats = {
            start_time: new Date().toISOString(),
            total_fetched: 0,
            new_activities: 0,
            existing_activities: allActivitiesIndex.length,
            pages_processed: 0,
            save_errors: 0,
            activity_types: {}
        };

        while (hasMore && this.checkRateLimit()) {
            try {
                console.log(`📄 Fetching page ${page}...`);
                const activities = await this.fetchActivities(page, perPage);
                
                if (activities.length === 0) {
                    console.log('✅ No more activities found');
                    hasMore = false;
                    break;
                }

                fetchStats.pages_processed++;
                fetchStats.total_fetched += activities.length;

                // Process each activity
                for (const activity of activities) {
                    // Skip if already exists
                    if (existingIds.has(activity.id)) {
                        continue;
                    }

                    // Save individual activity file
                    const saveResult = await this.saveIndividualActivity(activity, allActivitiesIndex.length);
                    
                    if (saveResult.success) {
                        // Add to index
                        const indexEntry = {
                            id: activity.id,
                            name: activity.name,
                            type: activity.type,
                            sport_type: activity.sport_type,
                            start_date: activity.start_date,
                            distance: activity.distance,
                            moving_time: activity.moving_time,
                            file_index: allActivitiesIndex.length,
                            filename: saveResult.filename
                        };
                        
                        allActivitiesIndex.push(indexEntry);
                        existingIds.add(activity.id);
                        newActivitiesCount++;
                        
                        // Track activity types
                        fetchStats.activity_types[activity.type] = (fetchStats.activity_types[activity.type] || 0) + 1;
                        
                    } else {
                        saveErrors++;
                        fetchStats.save_errors++;
                    }
                }
                
                if (newActivitiesCount > 0) {
                    console.log(`✅ Saved ${activities.filter(a => !existingIds.has(a.id) || existingIds.size === allActivitiesIndex.length).length} new activities from page ${page}`);
                } else {
                    console.log(`⏭️  No new activities on page ${page}`);
                }

                page++;
                
                // Save index periodically (every 5 pages)
                if (page % 5 === 0) {
                    await this.saveActivitiesIndex(allActivitiesIndex);
                    console.log(`💾 Saved progress: ${allActivitiesIndex.length} activities indexed`);
                }
                
                // Small delay to be respectful to the API
                await new Promise(resolve => setTimeout(resolve, 100));
                
            } catch (error) {
                console.error(`❌ Error fetching page ${page}:`, error.message);
                break;
            }
        }

        // Final save
        fetchStats.end_time = new Date().toISOString();
        fetchStats.new_activities = newActivitiesCount;
        
        await this.saveActivitiesIndex(allActivitiesIndex);
        await this.saveFetcherSummary(fetchStats);
        await this.saveRateLimitData();

        console.log(`\n📊 Summary:`);
        console.log(`Total activities: ${allActivitiesIndex.length}`);
        console.log(`New activities fetched: ${newActivitiesCount}`);
        console.log(`Individual files created: ${newActivitiesCount}`);
        if (saveErrors > 0) {
            console.log(`Save errors: ${saveErrors}`);
        }
        console.log(`Requests made: ${this.requestCount}/${this.maxRequestsPer15Min}`);
        console.log(`📁 Files saved to: ${this.individualActivitiesDir}`);
        
        if (this.requestCount >= this.maxRequestsPer15Min) {
            const nextAllowedTime = this.windowStart + (15 * 60 * 1000);
            console.log(`⏰ Next execution allowed at: ${new Date(nextAllowedTime).toLocaleTimeString()}`);
        }

        return allActivitiesIndex;
    }
}

async function main() {
    try {
        const fetcher = new StravaActivityFetcher();
        await fetcher.initialize();
        await fetcher.fetchAllActivities();
    } catch (error) {
        console.error('❌ Application error:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = StravaActivityFetcher;
