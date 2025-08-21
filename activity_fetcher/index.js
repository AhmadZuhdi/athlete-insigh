// Entry point for the Strava Activity Fetcher
// This file serves as the main entry point and delegates to the core fetcher

const StravaActivityFetcher = require('./src/core/strava-fetcher');

// Create and run the fetcher
const fetcher = new StravaActivityFetcher();
fetcher.initialize().then(() => {
    return fetcher.fetchAllActivities();
}).catch(error => {
    console.error('❌ Application error:', error.message);
    process.exit(1);
});
