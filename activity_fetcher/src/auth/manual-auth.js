require('dotenv').config();

function generateAuthUrl() {
    const clientId = process.env.STRAVA_CLIENT_ID;
    
    if (!clientId) {
        console.log('❌ Missing STRAVA_CLIENT_ID in .env file');
        return;
    }

    const scopes = 'read,activity:read,activity:read_all';
    const redirectUri = 'http://localhost';
    
    const authUrl = `https://www.strava.com/oauth/authorize?` +
        `client_id=${clientId}&` +
        `response_type=code&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `approval_prompt=force&` +
        `scope=${encodeURIComponent(scopes)}`;
    
    console.log('🔑 Manual Token Generation Guide\n');
    console.log('📋 Step 1: Open this URL in your browser:');
    console.log('\n' + authUrl + '\n');
    
    console.log('📋 Step 2: After clicking "Authorize":');
    console.log('- You\'ll be redirected to localhost with an error page (this is normal)');
    console.log('- Copy the FULL URL from your browser address bar');
    console.log('- It will look like: http://localhost/?state=&code=XXXXX&scope=read,activity:read');
    console.log('- Copy the code=XXXXX part');
    
    console.log('\n📋 Step 3: Exchange the code for a token:');
    console.log('Run: node exchange-token.js YOUR_CODE_HERE');
    
    console.log('\n🔐 Required Permissions:');
    console.log('Make sure to authorize these scopes:');
    console.log('✅ View data about your activities');
    console.log('✅ View your activity data including private activities');
}

if (require.main === module) {
    generateAuthUrl();
}

module.exports = { generateAuthUrl };
