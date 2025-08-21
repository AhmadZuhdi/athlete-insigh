const fs = require('fs').promises;
const path = require('path');

class ActivityFileManager {
    constructor() {
        this.baseDir = './data/individual_activities';
        this.metadataDir = './data/metadata';
        this.indexFile = path.join(this.metadataDir, 'activity_index.json');
        this.summaryFile = path.join(this.metadataDir, 'fetcher_summary.json');
        // Legacy file locations for backward compatibility
        this.legacyIndexFile = path.join(this.baseDir, '_activity_index.json');
        this.legacySummaryFile = path.join(this.baseDir, '_split_summary.json');
    }

    async loadIndex() {
        try {
            // Try new metadata location first
            const data = await fs.readFile(this.indexFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            // Fallback to legacy location
            try {
                const data = await fs.readFile(this.legacyIndexFile, 'utf8');
                console.log('📝 Using legacy index file. Consider running migration.');
                return JSON.parse(data);
            } catch (legacyError) {
                throw new Error('Activity index not found. Run "npm start" first to fetch activities.');
            }
        }
    }

    async loadSummary() {
        try {
            // Try new metadata location first
            const data = await fs.readFile(this.summaryFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            // Fallback to legacy location
            try {
                const data = await fs.readFile(this.legacySummaryFile, 'utf8');
                return JSON.parse(data);
            } catch (legacyError) {
                throw new Error('Summary not found.');
            }
        }
    }

    async findActivity(searchTerm) {
        const index = await this.loadIndex();
        
        const results = index.filter(activity => 
            activity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            activity.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
            activity.id.toString().includes(searchTerm) ||
            activity.start_date.includes(searchTerm)
        );

        return results;
    }

    async getActivity(activityId) {
        const index = await this.loadIndex();
        const activityInfo = index.find(a => a.id.toString() === activityId.toString());
        
        if (!activityInfo) {
            throw new Error(`Activity ${activityId} not found`);
        }

        const filepath = path.join(this.baseDir, activityInfo.filename);
        const data = await fs.readFile(filepath, 'utf8');
        return JSON.parse(data);
    }

    async getActivitiesByType(type) {
        const index = await this.loadIndex();
        return index.filter(activity => 
            activity.type.toLowerCase() === type.toLowerCase()
        );
    }

    async getActivitiesByDateRange(startDate, endDate) {
        const index = await this.loadIndex();
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        return index.filter(activity => {
            const activityDate = new Date(activity.start_date);
            return activityDate >= start && activityDate <= end;
        });
    }

    async listFiles() {
        const files = await fs.readdir(this.baseDir);
        return files.filter(file => 
            file.endsWith('.json') && 
            !file.startsWith('_')
        );
    }

    async getStats() {
        try {
            const summary = await this.loadSummary();
            const index = await this.loadIndex();
            
            const stats = {
                total_activities: index.length,
                activity_types: this.getActivityTypesFromIndex(index),
                date_range: this.getDateRangeFromIndex(index),
                total_distance: index.reduce((sum, a) => sum + (a.distance || 0), 0),
                total_time: index.reduce((sum, a) => sum + (a.moving_time || 0), 0),
                file_count: await this.listFiles().then(files => files.length)
            };

            return stats;
        } catch (error) {
            // Fallback: calculate stats from index only
            const index = await this.loadIndex();
            
            const stats = {
                total_activities: index.length,
                activity_types: this.getActivityTypesFromIndex(index),
                date_range: this.getDateRangeFromIndex(index),
                total_distance: index.reduce((sum, a) => sum + (a.distance || 0), 0),
                total_time: index.reduce((sum, a) => sum + (a.moving_time || 0), 0),
                file_count: await this.listFiles().then(files => files.length)
            };

            return stats;
        }
    }

    getActivityTypesFromIndex(index) {
        const types = {};
        index.forEach(activity => {
            types[activity.type] = (types[activity.type] || 0) + 1;
        });
        return types;
    }

    getDateRangeFromIndex(index) {
        if (index.length === 0) return { earliest: null, latest: null, span_days: 0 };
        
        const dates = index.map(a => new Date(a.start_date)).sort();
        return {
            earliest: dates[0].toISOString(),
            latest: dates[dates.length - 1].toISOString(),
            span_days: Math.ceil((dates[dates.length - 1] - dates[0]) / (1000 * 60 * 60 * 24))
        };
    }
}

async function main() {
    const command = process.argv[2];
    const param = process.argv[3];
    
    const manager = new ActivityFileManager();

    try {
        switch (command) {
            case 'list':
                const files = await manager.listFiles();
                console.log(`📁 Found ${files.length} activity files:`);
                files.slice(0, 10).forEach(file => console.log(`  • ${file}`));
                if (files.length > 10) {
                    console.log(`  ... and ${files.length - 10} more`);
                }
                break;

            case 'stats':
                const stats = await manager.getStats();
                console.log('📊 Activity Statistics:');
                console.log(`  Total activities: ${stats.total_activities}`);
                console.log(`  Total distance: ${(stats.total_distance / 1000).toFixed(2)} km`);
                console.log(`  Total time: ${Math.round(stats.total_time / 3600)} hours`);
                console.log('  Activity types:');
                Object.entries(stats.activity_types).forEach(([type, count]) => {
                    console.log(`    ${type}: ${count}`);
                });
                break;

            case 'find':
                if (!param) {
                    console.log('Usage: node activity-manager.js find <search_term>');
                    return;
                }
                const results = await manager.findActivity(param);
                console.log(`🔍 Found ${results.length} activities matching "${param}":`);
                results.forEach(activity => {
                    const date = new Date(activity.start_date).toLocaleDateString();
                    const distance = (activity.distance / 1000).toFixed(2);
                    console.log(`  • ${activity.name} (${activity.type}) - ${distance}km - ${date}`);
                });
                break;

            case 'get':
                if (!param) {
                    console.log('Usage: node activity-manager.js get <activity_id>');
                    return;
                }
                const activity = await manager.getActivity(param);
                console.log('📄 Activity Details:');
                console.log(`  Name: ${activity.name}`);
                console.log(`  Type: ${activity.type}`);
                console.log(`  Date: ${new Date(activity.start_date).toLocaleString()}`);
                console.log(`  Distance: ${(activity.distance / 1000).toFixed(2)} km`);
                console.log(`  Moving Time: ${Math.round(activity.moving_time / 60)} minutes`);
                console.log(`  Elevation Gain: ${activity.total_elevation_gain} m`);
                console.log(`  File: ${activity._metadata.file_name}`);
                break;

            case 'type':
                if (!param) {
                    console.log('Usage: node activity-manager.js type <activity_type>');
                    return;
                }
                const byType = await manager.getActivitiesByType(param);
                console.log(`🚴 Found ${byType.length} ${param} activities:`);
                byType.slice(0, 10).forEach(activity => {
                    const date = new Date(activity.start_date).toLocaleDateString();
                    const distance = (activity.distance / 1000).toFixed(2);
                    console.log(`  • ${activity.name} - ${distance}km - ${date}`);
                });
                if (byType.length > 10) {
                    console.log(`  ... and ${byType.length - 10} more`);
                }
                break;

            default:
                console.log('🔧 Activity File Manager');
                console.log('\nUsage:');
                console.log('  node activity-manager.js list           - List all activity files');
                console.log('  node activity-manager.js stats          - Show activity statistics');
                console.log('  node activity-manager.js find <term>    - Search activities');
                console.log('  node activity-manager.js get <id>       - Get specific activity');
                console.log('  node activity-manager.js type <type>    - Get activities by type');
                console.log('\nExamples:');
                console.log('  node activity-manager.js find "Morning"');
                console.log('  node activity-manager.js get 15511022783');
                console.log('  node activity-manager.js type Ride');
        }

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

if (require.main === module) {
    main();
}

module.exports = ActivityFileManager;
