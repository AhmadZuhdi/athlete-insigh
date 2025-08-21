# Strava Activity Fetcher

A Node.js application that downloads Strava activities to local JSON files with intelligent rate limiting.

## Features

- ✅ Downloads all athlete activities from Strava API
- ✅ Respects Strava's rate limits (100 requests per 15 minutes)
- ✅ Automatically stops and saves state when rate limit is reached
- ✅ Resumes from where it left off after the rate limit window
- ✅ Avoids duplicate activities by checking existing data
- ✅ **Saves activities as individual JSON files** (one per activity)
- ✅ **Creates searchable activity index** for fast lookups
- ✅ Persistent rate limit tracking
- ✅ **Legacy migration support** from single JSON file

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure Strava API access:**
   
   **Option A: Quick OAuth (Recommended)**
   ```bash
   npm run oauth
   ```
   This will:
   - Open your browser to Strava's authorization page
   - Guide you through granting the correct permissions
   - Automatically get a token with proper scopes
   - Show you the token to add to your .env file

   **Option B: Manual Setup**
   - Copy `.env.example` to `.env`
   - Get your Strava API credentials:
     - Go to https://www.strava.com/settings/api
     - Create an application
     - Generate an access token with `read` and `activity:read` scopes

3. **Update `.env` file:**
   ```env
   STRAVA_ACCESS_TOKEN=your_actual_access_token_here
   STRAVA_CLIENT_ID=your_client_id_here
   STRAVA_CLIENT_SECRET=your_client_secret_here
   ```

## Usage

### Run the fetcher:
```bash
npm start
```

### Validate your token:
```bash
npm run validate
```

### Get a new token with proper permissions:
```bash
npm run oauth
```

### Development mode (with auto-restart):
```bash
npm run dev
```

### Analyze your data:
```bash
npm run analyze
```

### Split activities into individual files:
```bash
npm run split
```

### Manage individual activity files:
```bash
# Show statistics
npm run manage stats

# List all files
npm run manage list

# Find activities
npm run manage find "Morning"
npm run manage find "2025"

# Get specific activity
npm run manage get 15511022783

# Get activities by type
npm run manage type Ride
```

### Migrate from legacy single JSON file:
```bash
npm run migrate
```

## How it works

1. **Rate Limiting**: Tracks requests and stops at 100 requests per 15-minute window
2. **State Persistence**: Saves rate limit state to `data/rate_limit.json`
3. **Individual Activity Storage**: Each activity saved as separate JSON file in `data/individual_activities/`
4. **Metadata Management**: All utility files organized in `data/metadata/` folder
5. **Activity Index**: Maintains searchable index for fast searching and browsing
6. **Smart Resumption**: Automatically resumes after rate limit window expires
7. **Duplicate Prevention**: Checks existing activities to avoid re-downloading

## Output

**Activity Files:**
- `data/individual_activities/*.json` - Individual activity files (one per activity)

**Metadata Files:**
- `data/metadata/activity_index.json` - Searchable activity index
- `data/metadata/fetcher_summary.json` - Fetch operation statistics
- `data/metadata/split_summary.json` - Split operation summary (if using split command)

**System Files:**
- `data/rate_limit.json` - Rate limit tracking data

## File Structure

```
data/
├── individual_activities/           # Activity files (one per activity)
│   ├── 15511022783_2025-08-19_Afternoon_Ride.json
│   ├── 15476920956_2025-08-16_Afternoon_Ride.json
│   └── ... (more activity files)
├── metadata/                       # Utility and index files
│   ├── activity_index.json        # Fast search index
│   ├── fetcher_summary.json       # Fetch statistics
│   └── split_summary.json         # Split operation summary
└── rate_limit.json               # Rate limiting data
```

## Project Structure

```
activity_fetcher/
├── index.js                    # Main entry point
├── package.json               # Dependencies and scripts
├── .env                       # Environment variables (create from .env.example)
├── src/
│   ├── core/
│   │   └── strava-fetcher.js  # Main fetcher application logic
│   ├── auth/                  # Authentication utilities
│   │   ├── oauth.js           # OAuth flow implementation
│   │   ├── manual-auth.js     # Manual token authorization
│   │   ├── exchange-token.js  # Token exchange utility
│   │   └── validate-token.js  # Token validation
│   ├── utils/                 # Analysis and management utilities
│   │   ├── activity-manager.js # Activity file management
│   │   └── analyze.js         # Activity data analysis
│   └── commands/              # Data processing commands
│       ├── split-activities.js # Legacy JSON splitter
│       └── migrate.js         # Data migration utility
├── data/
│   ├── individual_activities/ # One JSON file per activity
│   ├── metadata/             # Index and summary files
│   │   ├── activity_index.json
│   │   └── fetcher_summary.json
│   └── rate_limit.json       # Rate limiting state
└── scripts/                  # Additional utility scripts
```

## Rate Limit Behavior

When the app hits the 100 request limit:
- ✋ Stops execution immediately
- 💾 Saves current progress
- ⏰ Calculates and displays next allowed execution time
- 🔄 Run the app again after 15 minutes to continue

## Example Output

```
🚀 Starting Strava activity fetch...
📄 Fetching page 1...
📡 Request 1/100: https://www.strava.com/api/v3/athlete/activities
✅ Added 30 new activities from page 1
📄 Fetching page 2...
...
⚠️  Approaching rate limit: 96/100
🛑 Rate limit reached (100/100)
⏰ Next execution allowed at: 2:45:00 PM
⏳ Wait time: 15 minutes

📊 Summary:
Total activities: 2,850
New activities fetched: 150
Requests made: 100/100
⏰ Next execution allowed at: 2:45:00 PM
```

## API Scopes Required

Your Strava access token needs these scopes:
- `read` - Read public segments, public routes, public profile data
- `activity:read` - Read private activities

## Troubleshooting

1. **Invalid access token**: Make sure your token is valid and not expired
2. **Rate limit file issues**: Delete `data/rate_limit.json` to reset rate limiting
3. **No activities found**: Check if your access token has the right scopes
