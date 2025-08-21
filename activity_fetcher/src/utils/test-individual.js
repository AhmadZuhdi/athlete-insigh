require('dotenv').config();
const StravaActivityFetcher = require('./index.js');

class TestFetcher extends StravaActivityFetcher {
    async fetchActivities(page = 1, perPage = 5) { // Limit to 5 activities for testing
        if (page > 2) return []; // Only fetch 2 pages max for testing
        return super.fetchActivities(page, perPage);
    }
}

async function testRun() {
    console.log('🧪 Running test fetch with updated individual file saving...\n');
    
    try {
        const fetcher = new TestFetcher();
        await fetcher.initialize();
        await fetcher.fetchAllActivities();
        
        console.log('\n✅ Test completed successfully!');
        console.log('Check the data/individual_activities/ directory for new files');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

if (require.main === module) {
    testRun();
}
