require('dotenv').config();
const http = require('http');
const url = require('url');
const querystring = require('querystring');
const axios = require('axios');

class StravaOAuth {
    constructor() {
        this.clientId = process.env.STRAVA_CLIENT_ID;
        this.clientSecret = process.env.STRAVA_CLIENT_SECRET;
        this.redirectUri = 'http://localhost:3000/callback';
        this.port = 3000;
    }

    getAuthUrl() {
        const scopes = 'read,activity:read,activity:read_all';
        const authUrl = `https://www.strava.com/oauth/authorize?` +
            `client_id=${this.clientId}&` +
            `response_type=code&` +
            `redirect_uri=${encodeURIComponent(this.redirectUri)}&` +
            `approval_prompt=force&` +
            `scope=${encodeURIComponent(scopes)}`;
        
        return authUrl;
    }

    async exchangeCodeForToken(code) {
        try {
            const response = await axios.post('https://www.strava.com/oauth/token', {
                client_id: this.clientId,
                client_secret: this.clientSecret,
                code: code,
                grant_type: 'authorization_code'
            });

            return response.data;
        } catch (error) {
            throw new Error(`Token exchange failed: ${error.response?.data?.message || error.message}`);
        }
    }

    async startOAuthFlow() {
        return new Promise((resolve, reject) => {
            const server = http.createServer(async (req, res) => {
                const parsedUrl = url.parse(req.url, true);
                
                if (parsedUrl.pathname === '/callback') {
                    const { code, error } = parsedUrl.query;
                    
                    if (error) {
                        res.writeHead(400, { 'Content-Type': 'text/html' });
                        res.end(`<h1>Authorization Failed</h1><p>Error: ${error}</p>`);
                        server.close();
                        reject(new Error(`Authorization failed: ${error}`));
                        return;
                    }

                    if (code) {
                        try {
                            console.log('🔄 Exchanging authorization code for access token...');
                            const tokenData = await this.exchangeCodeForToken(code);
                            
                            res.writeHead(200, { 'Content-Type': 'text/html' });
                            res.end(`
                                <h1>✅ Authorization Successful!</h1>
                                <p>You can close this window and return to your terminal.</p>
                                <h3>Token Details:</h3>
                                <ul>
                                    <li>Access Token: ${tokenData.access_token.substring(0, 10)}...${tokenData.access_token.substring(tokenData.access_token.length - 5)}</li>
                                    <li>Athlete: ${tokenData.athlete.firstname} ${tokenData.athlete.lastname}</li>
                                    <li>Expires: ${new Date(tokenData.expires_at * 1000).toLocaleString()}</li>
                                </ul>
                            `);
                            
                            server.close();
                            resolve(tokenData);
                        } catch (error) {
                            res.writeHead(500, { 'Content-Type': 'text/html' });
                            res.end(`<h1>❌ Token Exchange Failed</h1><p>${error.message}</p>`);
                            server.close();
                            reject(error);
                        }
                    }
                } else {
                    res.writeHead(404, { 'Content-Type': 'text/html' });
                    res.end('<h1>404 Not Found</h1>');
                }
            });

            server.listen(this.port, () => {
                const authUrl = this.getAuthUrl();
                console.log('🚀 OAuth server started on port', this.port);
                console.log('🔗 Open this URL in your browser to authorize:');
                console.log('\n' + authUrl + '\n');
                console.log('📋 Steps:');
                console.log('1. Click the URL above (or copy/paste to browser)');
                console.log('2. Log in to Strava if needed');
                console.log('3. Click "Authorize" to grant permissions');
                console.log('4. You\'ll be redirected back here automatically');
                console.log('\nWaiting for authorization...');
            });

            // Timeout after 5 minutes
            setTimeout(() => {
                server.close();
                reject(new Error('Authorization timeout - please try again'));
            }, 5 * 60 * 1000);
        });
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
        console.log(`✅ Found ${activitiesResponse.data.length > 0 ? 'activities available' : 'no activities (but permission granted)'}`);
        
    } catch (error) {
        console.log('❌ Token test failed:', error.response?.data?.message || error.message);
        if (error.response?.status === 403) {
            console.log('⚠️  Token may be missing required scopes');
        }
    }
}

async function main() {
    console.log('🔑 Strava OAuth Token Generator\n');
    
    const clientId = process.env.STRAVA_CLIENT_ID;
    const clientSecret = process.env.STRAVA_CLIENT_SECRET;
    
    if (!clientId || !clientSecret) {
        console.log('❌ Missing Strava app credentials');
        console.log('Please set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in your .env file');
        console.log('\nTo get these:');
        console.log('1. Go to https://www.strava.com/settings/api');
        console.log('2. Create an application if you haven\'t');
        console.log('3. Use your Client ID and Client Secret');
        return;
    }

    try {
        const oauth = new StravaOAuth();
        const tokenData = await oauth.startOAuthFlow();
        
        console.log('\n✅ Successfully obtained access token!');
        console.log('\n📝 Update your .env file with this new token:');
        console.log(`STRAVA_ACCESS_TOKEN=${tokenData.access_token}`);
        console.log('\n📊 Token details:');
        console.log(`- Athlete: ${tokenData.athlete.firstname} ${tokenData.athlete.lastname}`);
        console.log(`- Scopes: ${tokenData.scope || 'read,activity:read,activity:read_all'}`);
        console.log(`- Expires: ${new Date(tokenData.expires_at * 1000).toLocaleString()}`);
        console.log(`- Refresh Token: ${tokenData.refresh_token ? tokenData.refresh_token.substring(0, 10) + '...' + tokenData.refresh_token.substring(tokenData.refresh_token.length - 5) : 'Not provided'}`);
        
        // Test the new token immediately
        console.log('\n🔍 Testing new token...');
        await testToken(tokenData.access_token);
        
        console.log('\n🎉 You can now run: npm start');
        
    } catch (error) {
        console.error('❌ OAuth flow failed:', error.message);
    }
}

if (require.main === module) {
    main();
}

module.exports = StravaOAuth;
