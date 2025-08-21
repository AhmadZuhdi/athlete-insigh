require('dotenv').config();
const axios = require('axios');

async function validateToken() {
    const accessToken = process.env.STRAVA_ACCESS_TOKEN;
    
    if (!accessToken) {
        console.log('❌ No access token found in .env file');
        console.log('Please set STRAVA_ACCESS_TOKEN in your .env file');
        return;
    }

    console.log('🔍 Validating Strava access token...');
    console.log(`Token: ${accessToken.substring(0, 10)}...${accessToken.substring(accessToken.length - 5)}`);

    try {
        // Test with athlete endpoint first
        const response = await axios.get('https://www.strava.com/api/v3/athlete', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Accept': 'application/json'
            }
        });

        console.log('✅ Token is valid!');
        console.log(`👤 Authenticated as: ${response.data.firstname} ${response.data.lastname}`);
        console.log(`🆔 Athlete ID: ${response.data.id}`);
        console.log(`🔗 Profile: ${response.data.profile}`);
        
        // Check token scopes by trying to access activities
        try {
            const activitiesResponse = await axios.get('https://www.strava.com/api/v3/athlete/activities', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Accept': 'application/json'
                },
                params: {
                    page: 1,
                    per_page: 1
                }
            });
            
            console.log('✅ Token has activity read permissions');
            console.log(`📊 Found ${activitiesResponse.data.length > 0 ? 'activities' : 'no activities'}`);
            
        } catch (error) {
            if (error.response?.status === 403) {
                console.log('❌ Token lacks activity read permissions');
                console.log('🔧 Your token needs "activity:read" scope');
            } else {
                console.log('❌ Error checking activities:', error.response?.data || error.message);
            }
        }

    } catch (error) {
        console.log('❌ Token validation failed');
        
        if (error.response?.status === 401) {
            console.log('🚫 Token is invalid or expired');
            console.log('\n📋 To fix this:');
            console.log('1. Go to https://www.strava.com/settings/api');
            console.log('2. Find your application');
            console.log('3. Generate a new access token with these scopes:');
            console.log('   - read');
            console.log('   - activity:read');
            console.log('4. Update your .env file with the new token');
        } else if (error.response?.status === 429) {
            console.log('🚫 Rate limit exceeded');
            console.log('Wait 15 minutes and try again');
        } else {
            console.log('❌ Unexpected error:', error.response?.data || error.message);
        }
    }
}

async function getNewToken() {
    console.log('\n🔑 How to get a new Strava access token:\n');
    console.log('1. Go to: https://www.strava.com/settings/api');
    console.log('2. If you don\'t have an app, click "Create App"');
    console.log('3. Fill in the application details:');
    console.log('   - Application Name: "Activity Fetcher"');
    console.log('   - Category: "Other"');
    console.log('   - Club: Leave empty');
    console.log('   - Website: "http://localhost"');
    console.log('   - Authorization Callback Domain: "localhost"');
    console.log('4. After creating, you\'ll see your app details');
    console.log('5. Note your Client ID and Client Secret');
    console.log('6. For quick testing, you can use the "Your Access Token" shown on the page');
    console.log('7. For production, implement OAuth flow for long-term tokens\n');
    
    console.log('🔐 Required Scopes:');
    console.log('   - read: Read public segments, public routes, public profile data');
    console.log('   - activity:read: Read private activities');
    console.log('   - activity:read_all: Read all activities (optional, for more data)');
}

if (require.main === module) {
    validateToken().then(() => {
        console.log('\n' + '='.repeat(60));
        getNewToken();
    });
}

module.exports = { validateToken };
