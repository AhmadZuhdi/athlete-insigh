const fs = require('fs').promises;
const path = require('path');

async function analyzeActivities() {
    const metadataIndexFile = './data/metadata/activity_index.json';
    const legacyActivitiesFile = './data/activities.json';
    
    let activities = [];
    
    try {
        // Try to load from new metadata location first
        const data = await fs.readFile(metadataIndexFile, 'utf8');
        const activityIndex = JSON.parse(data);
        
        if (activityIndex.length === 0) {
            console.log('No activities found. Run the fetcher first: npm start');
            return;
        }

        // Load individual activity files to get full data for analysis
        console.log('📖 Loading individual activity files for analysis...');
        const individualActivitiesDir = './data/individual_activities';
        
        for (const indexEntry of activityIndex) {
            try {
                const activityPath = path.join(individualActivitiesDir, indexEntry.filename);
                const activityData = await fs.readFile(activityPath, 'utf8');
                const activity = JSON.parse(activityData);
                activities.push(activity);
            } catch (error) {
                console.warn(`⚠️  Could not load activity file: ${indexEntry.filename}`);
            }
        }
        
        console.log(`✅ Loaded ${activities.length} activities from individual files`);
        
    } catch (error) {
        // Fallback to legacy activities.json file
        try {
            console.log('📖 Falling back to legacy activities.json file...');
            const data = await fs.readFile(legacyActivitiesFile, 'utf8');
            activities = JSON.parse(data);
        } catch (legacyError) {
            console.error('❌ Error analyzing activities:', error.message);
            console.log('Make sure to run the fetcher first: npm start');
            return;
        }
    }
        
    if (activities.length === 0) {
        console.log('No activities found. Run the fetcher first: npm start');
        return;
    }

    console.log('📊 Activity Analysis\n');
    console.log(`Total activities: ${activities.length}`);
    
    // Activity types
    const activityTypes = {};
    activities.forEach(activity => {
        activityTypes[activity.type] = (activityTypes[activity.type] || 0) + 1;
    });
    
    console.log('\n🏃 Activity Types:');
    Object.entries(activityTypes)
        .sort(([,a], [,b]) => b - a)
        .forEach(([type, count]) => {
            console.log(`  ${type}: ${count}`);
        });

    // Distance analysis
    const totalDistance = activities.reduce((sum, activity) => sum + (activity.distance || 0), 0);
    const avgDistance = totalDistance / activities.length;
    
    console.log('\n📏 Distance:');
    console.log(`  Total: ${(totalDistance / 1000).toFixed(2)} km`);
    console.log(`  Average: ${(avgDistance / 1000).toFixed(2)} km per activity`);

    // Time analysis
    const totalTime = activities.reduce((sum, activity) => sum + (activity.moving_time || 0), 0);
    const avgTime = totalTime / activities.length;
    
    console.log('\n⏱️  Time:');
    console.log(`  Total moving time: ${Math.round(totalTime / 3600)} hours`);
    console.log(`  Average per activity: ${Math.round(avgTime / 60)} minutes`);

    // Recent activities
    const recentActivities = activities
        .sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
        .slice(0, 5);
    
    console.log('\n🕒 Recent Activities:');
    recentActivities.forEach((activity, index) => {
        const date = new Date(activity.start_date).toLocaleDateString();
        const distance = (activity.distance / 1000).toFixed(2);
        console.log(`  ${index + 1}. ${activity.name} - ${activity.type} - ${distance}km (${date})`);
    });

    // Date range
    const dates = activities.map(a => new Date(a.start_date)).sort();
    const firstActivity = dates[0];
    const lastActivity = dates[dates.length - 1];
    
    console.log('\n📅 Date Range:');
    console.log(`  First activity: ${firstActivity.toLocaleDateString()}`);
    console.log(`  Last activity: ${lastActivity.toLocaleDateString()}`);
}

if (require.main === module) {
    analyzeActivities();
}
