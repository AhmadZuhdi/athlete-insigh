const fs = require('fs').promises;
const path = require('path');

async function setup() {
    console.log('🚀 Setting up Strava Activity Fetcher...\n');

    // Create .env file if it doesn't exist
    const envPath = '.env';
    const envExamplePath = '.env.example';
    
    try {
        await fs.access(envPath);
        console.log('✅ .env file already exists');
    } catch {
        try {
            await fs.copyFile(envExamplePath, envPath);
            console.log('✅ Created .env file from .env.example');
        } catch (error) {
            console.error('❌ Failed to create .env file:', error.message);
        }
    }

    // Create data directory
    const dataDir = './data';
    try {
        await fs.mkdir(dataDir, { recursive: true });
        console.log('✅ Created data directory');
    } catch (error) {
        console.error('❌ Failed to create data directory:', error.message);
    }

    console.log('\n📋 Next steps:');
    console.log('1. Get your Strava API access token:');
    console.log('   - Go to https://www.strava.com/settings/api');
    console.log('   - Create an application');
    console.log('   - Generate an access token');
    console.log('');
    console.log('2. Update your .env file with your actual token:');
    console.log('   STRAVA_ACCESS_TOKEN=your_actual_token_here');
    console.log('');
    console.log('3. Run the fetcher:');
    console.log('   npm start');
    console.log('');
    console.log('📖 For more information, see README.md');
}

setup().catch(console.error);
