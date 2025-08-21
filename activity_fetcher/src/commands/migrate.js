const fs = require('fs').promises;
const path = require('path');

async function migrateLegacyActivities() {
    console.log('🔄 Legacy Activities Migration Tool\n');
    
    const dataDir = './data';
    const legacyFile = path.join(dataDir, 'activities.json');
    const individualDir = path.join(dataDir, 'individual_activities');
    const metadataDir = path.join(dataDir, 'metadata');
    const indexFile = path.join(metadataDir, 'activity_index.json');
    const legacyIndexFile = path.join(individualDir, '_activity_index.json');
    
    try {
        // Check if we need to migrate
        console.log('🔍 Checking migration status...');
        
        // Check if new metadata structure exists
        try {
            await fs.access(indexFile);
            console.log('✅ New metadata structure already exists');
            
            const indexData = JSON.parse(await fs.readFile(indexFile, 'utf8'));
            console.log(`📊 Found ${indexData.length} activities in metadata index`);
            return;
            
        } catch {
            // Check if legacy index exists and migrate it
            try {
                await fs.access(legacyIndexFile);
                console.log('� Found legacy index file, migrating to metadata folder...');
                
                // Create metadata directory
                await fs.mkdir(metadataDir, { recursive: true });
                
                // Copy legacy files to metadata folder
                const legacyIndexData = await fs.readFile(legacyIndexFile, 'utf8');
                await fs.writeFile(indexFile, legacyIndexData);
                
                // Check for other legacy metadata files
                const legacySummaryFile = path.join(individualDir, '_split_summary.json');
                const newSummaryFile = path.join(metadataDir, 'split_summary.json');
                
                try {
                    const legacySummaryData = await fs.readFile(legacySummaryFile, 'utf8');
                    await fs.writeFile(newSummaryFile, legacySummaryData);
                    console.log('✅ Migrated split summary to metadata folder');
                } catch {
                    console.log('⚠️  No legacy split summary found');
                }
                
                console.log('✅ Migration to metadata folder completed');
                
                const indexData = JSON.parse(legacyIndexData);
                console.log(`📊 Migrated ${indexData.length} activities to metadata structure`);
                return;
                
            } catch {
                // No legacy index, check for legacy activities.json
                console.log('� No existing metadata found, checking for legacy activities.json...');
            }
        }
        
        await fs.access(legacyFile);
        
        // Read legacy data
        const legacyData = JSON.parse(await fs.readFile(legacyFile, 'utf8'));
        console.log(`📖 Found ${legacyData.length} activities in legacy file`);
        
        // Create individual and metadata directories
        await fs.mkdir(individualDir, { recursive: true });
        await fs.mkdir(metadataDir, { recursive: true });
        
        // Convert to individual files
        const index = [];
        let successCount = 0;
        let errorCount = 0;
        
        for (let i = 0; i < legacyData.length; i++) {
            const activity = legacyData[i];
            
            try {
                // Generate filename
                const date = new Date(activity.start_date).toISOString().split('T')[0];
                const sanitizedName = activity.name
                    .replace(/[^a-zA-Z0-9\s-]/g, '')
                    .replace(/\s+/g, '_')
                    .substring(0, 50);
                const filename = `${activity.id}_${date}_${sanitizedName}.json`;
                
                // Add metadata
                const activityWithMeta = {
                    ...activity,
                    _metadata: {
                        migrated_date: new Date().toISOString(),
                        original_index: i,
                        file_name: filename,
                        migration_version: "1.0"
                    }
                };
                
                // Save individual file
                const filepath = path.join(individualDir, filename);
                await fs.writeFile(filepath, JSON.stringify(activityWithMeta, null, 2));
                
                // Add to index
                index.push({
                    id: activity.id,
                    name: activity.name,
                    type: activity.type,
                    sport_type: activity.sport_type,
                    start_date: activity.start_date,
                    distance: activity.distance,
                    moving_time: activity.moving_time,
                    file_index: i,
                    filename: filename
                });
                
                successCount++;
                
                if ((i + 1) % 10 === 0) {
                    console.log(`📝 Migrated ${i + 1}/${legacyData.length} activities`);
                }
                
            } catch (error) {
                console.error(`❌ Failed to migrate activity ${activity.id}:`, error.message);
                errorCount++;
            }
        }
        
        // Save index to metadata folder
        await fs.writeFile(indexFile, JSON.stringify(index, null, 2));
        
        // Create migration summary in metadata folder
        const migrationSummary = {
            migration_date: new Date().toISOString(),
            source_file: legacyFile,
            target_directory: individualDir,
            metadata_directory: metadataDir,
            total_activities: legacyData.length,
            successful_migrations: successCount,
            failed_migrations: errorCount,
            index_file: indexFile
        };
        
        const summaryFile = path.join(metadataDir, 'migration_summary.json');
        await fs.writeFile(summaryFile, JSON.stringify(migrationSummary, null, 2));
        
        console.log(`\n✅ Migration completed!`);
        console.log(`📊 Results:`);
        console.log(`  • Total activities: ${legacyData.length}`);
        console.log(`  • Successfully migrated: ${successCount}`);
        console.log(`  • Failed: ${errorCount}`);
        console.log(`  • Individual files created in: ${individualDir}`);
        console.log(`  • Metadata files saved to: ${metadataDir}`);
        console.log(`  • Index file: ${indexFile}`);
        
        // Backup legacy file
        const backupFile = path.join(dataDir, 'activities_legacy_backup.json');
        await fs.copyFile(legacyFile, backupFile);
        console.log(`  • Legacy file backed up to: ${backupFile}`);
        
    } catch (error) {
        if (error.code === 'ENOENT') {
            console.log('📄 No legacy activities.json file found');
            console.log('✅ You\'re already using the new individual file system');
        } else {
            console.error('❌ Migration failed:', error.message);
        }
    }
}

if (require.main === module) {
    migrateLegacyActivities();
}

module.exports = { migrateLegacyActivities };
