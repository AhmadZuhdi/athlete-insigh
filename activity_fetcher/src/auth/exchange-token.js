require('dotenv').config();
const axios = require('axios');

async function exchangeToken(authCode) {
    const clientId = process.env.STRAVA_CLIENT_ID;
    const clientSecret = process.env.STRAVA_CLIENT_SECRET;
    
    if (!clientId || !clientSecret) {
        console.log('❌ Missing STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET in .env file');
        return;
    }
    
    if (!authCode) {
        console.log('❌ Please provide the authorization code');
        console.log('Usage: node exchange-token.js YOUR_CODE_HERE');
        return;
    }
    
    console.log('🔄 Exchanging authorization code for access token...');
    
    try {
        const response = await axios.post('https://www.strava.com/oauth/token', {
            client_id: clientId,
            client_secret: clientSecret,
            code: authCode,
            grant_type: 'authorization_code'
        });
        
        const tokenData = response.data;
        
        console.log('\n✅ Successfully obtained access token!');
        console.log('\n📝 Add this to your .env file:');
        console.log(`STRAVA_ACCESS_TOKEN=${tokenData.access_token}`);
        console.log('\n📊 Token details:');
        console.log(`- Athlete: ${tokenData.athlete.firstname} ${tokenData.athlete.lastname}`);
        console.log(`- Token Type: ${tokenData.token_type}`);
        console.log(`- Expires: ${new Date(tokenData.expires_at * 1000).toLocaleString()}`);
        console.log(`- Refresh Token: ${tokenData.refresh_token ? tokenData.refresh_token.substring(0, 10) + '...' : 'Not provided'}`);
        
        // Test the token
        console.log('\n🔍 Testing new token...');
        await testToken(tokenData.access_token);
        
        console.log('\n🎉 Token is ready! You can now run: npm start');
        
    } catch (error) {
        console.log('❌ Token exchange failed:');
        if (error.response?.data) {
            console.log('Error details:', error.response.data);
        } else {
            console.log('Error:', error.message);
        }
        
        console.log('\n💡 Common issues:');
        console.log('- Make sure the authorization code is correct');
        console.log('- Code can only be used once');
        console.log('- Code expires quickly (usually within 10 minutes)');
        console.log('- Check your Client ID and Secret in .env file');
    }
}

async function testToken(accessToken) {
    try {
        // Test athlete endpoint
        const athleteResponse = await axios.get('https://www.strava.com/api/v3/athlete', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Accept': 'application/json'
            }
        });
        console.log('✅ Athlete data access: SUCCESS');
        
        // Test activities endpoint
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
        console.log('✅ Activities access: SUCCESS');
        
        if (activitiesResponse.data.length > 0) {
            const activity = activitiesResponse.data[0];
            console.log(`✅ Sample activity: "${activity.name}" (${activity.type})`);
        } else {
            console.log('✅ No activities found, but permission granted');
        }
        
    } catch (error) {
        console.log('❌ Token test failed:');
        if (error.response?.status === 401) {
            console.log('  Invalid or expired token');
        } else if (error.response?.status === 403) {
            console.log('  Missing required scopes');
        } else {
            console.log('  ' + (error.response?.data?.message || error.message));
        }
    }
}

if (require.main === module) {
    const authCode = process.argv[2];
    exchangeToken(authCode);
}

module.exports = { exchangeToken };
