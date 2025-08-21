const fs = require('fs').promises;
const path = require('path');

async function splitActivities() {
    console.log('🔄 Starting to split activities into individual files...\n');
    
    const activitiesFile = './data/activities.json';
    const outputDir = './data/individual_activities';
    const metadataDir = './data/metadata';
    
    try {
        // Read the activities file
        console.log('📖 Reading activities.json...');
        const data = await fs.readFile(activitiesFile, 'utf8');
        const activities = JSON.parse(data);
        
        console.log(`✅ Found ${activities.length} activities`);
        
        // Create output directories
        console.log('📁 Creating output directories...');
        await fs.mkdir(outputDir, { recursive: true });
        await fs.mkdir(metadataDir, { recursive: true });
        
        // Process each activity
        console.log('✂️  Splitting activities into individual files...\n');
        
        const results = {
            total: activities.length,
            successful: 0,
            failed: 0,
            errors: []
        };
        
        for (let i = 0; i < activities.length; i++) {
            const activity = activities[i];
            
            try {
                // Create filename with activity ID, date, and sanitized name
                const date = new Date(activity.start_date).toISOString().split('T')[0];
                const sanitizedName = activity.name
                    .replace(/[^a-zA-Z0-9\s-]/g, '') // Remove special characters
                    .replace(/\s+/g, '_') // Replace spaces with underscores
                    .substring(0, 50); // Limit length
                
                const filename = `${activity.id}_${date}_${sanitizedName}.json`;
                const filepath = path.join(outputDir, filename);
                
                // Add metadata to the activity
                const activityWithMeta = {
                    ...activity,
                    _metadata: {
                        split_date: new Date().toISOString(),
                        original_index: i,
                        file_name: filename
                    }
                };
                
                // Write individual activity file
                await fs.writeFile(filepath, JSON.stringify(activityWithMeta, null, 2));
                
                results.successful++;
                
                // Progress indicator
                if ((i + 1) % 10 === 0 || i === activities.length - 1) {
                    console.log(`📝 Progress: ${i + 1}/${activities.length} files created`);
                }
                
            } catch (error) {
                results.failed++;
                results.errors.push({
                    activity_id: activity.id,
                    activity_name: activity.name,
                    error: error.message
                });
                console.log(`❌ Failed to process activity ${activity.id}: ${error.message}`);
            }
        }
        
        // Create summary file
        const summary = {
            split_date: new Date().toISOString(),
            source_file: activitiesFile,
            output_directory: outputDir,
            metadata_directory: metadataDir,
            results: results,
            activity_types: getActivityTypesSummary(activities),
            date_range: getDateRange(activities)
        };
        
        await fs.writeFile(path.join(metadataDir, 'split_summary.json'), JSON.stringify(summary, null, 2));
        
        // Create index file with activity list
        const index = activities.map((activity, index) => ({
            id: activity.id,
            name: activity.name,
            type: activity.type,
            sport_type: activity.sport_type,
            start_date: activity.start_date,
            distance: activity.distance,
            moving_time: activity.moving_time,
            file_index: index,
            filename: `${activity.id}_${new Date(activity.start_date).toISOString().split('T')[0]}_${activity.name.replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '_').substring(0, 50)}.json`
        }));
        
        await fs.writeFile(path.join(metadataDir, 'activity_index.json'), JSON.stringify(index, null, 2));
        
        // Display results
        console.log('\n' + '='.repeat(60));
        console.log('📊 SPLIT RESULTS');
        console.log('='.repeat(60));
        console.log(`✅ Total activities: ${results.total}`);
        console.log(`✅ Successfully split: ${results.successful}`);
        console.log(`❌ Failed: ${results.failed}`);
        console.log(`📁 Output directory: ${outputDir}`);
        
        if (results.failed > 0) {
            console.log('\n❌ Errors:');
            results.errors.forEach(error => {
                console.log(`  - Activity ${error.activity_id} (${error.activity_name}): ${error.error}`);
            });
        }
        
        console.log('📋 Additional files created:');
        console.log(`  • ${metadataDir}/split_summary.json - Complete summary with statistics`);
        console.log(`  • ${metadataDir}/activity_index.json - Index of all activities with filenames`);
        
        console.log('\n🎉 Split complete!');
        
    } catch (error) {
        console.error('❌ Error splitting activities:', error.message);
    }
}

function getActivityTypesSummary(activities) {
    const types = {};
    activities.forEach(activity => {
        types[activity.type] = (types[activity.type] || 0) + 1;
    });
    return types;
}

function getDateRange(activities) {
    const dates = activities.map(a => new Date(a.start_date)).sort();
    return {
        earliest: dates[0].toISOString(),
        latest: dates[dates.length - 1].toISOString(),
        span_days: Math.ceil((dates[dates.length - 1] - dates[0]) / (1000 * 60 * 60 * 24))
    };
}

if (require.main === module) {
    splitActivities();
}

module.exports = { splitActivities };
