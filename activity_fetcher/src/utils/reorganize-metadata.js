const fs = require('fs').promises;
const path = require('path');

async function reorganizeToMetadata() {
    console.log('🔄 Reorganizing utility files to metadata folder...\n');
    
    const individualDir = './data/individual_activities';
    const metadataDir = './data/metadata';
    
    // Files to move from individual_activities to metadata
    const filesToMove = [
        { from: '_activity_index.json', to: 'activity_index.json' },
        { from: '_fetcher_summary.json', to: 'fetcher_summary.json' },
        { from: '_split_summary.json', to: 'split_summary.json' },
        { from: '_migration_summary.json', to: 'migration_summary.json' }
    ];
    
    try {
        // Create metadata directory
        await fs.mkdir(metadataDir, { recursive: true });
        console.log('📁 Created metadata directory');
        
        let movedCount = 0;
        let notFoundCount = 0;
        
        for (const file of filesToMove) {
            const sourcePath = path.join(individualDir, file.from);
            const targetPath = path.join(metadataDir, file.to);
            
            try {
                // Check if source file exists
                await fs.access(sourcePath);
                
                // Move file to metadata folder
                const data = await fs.readFile(sourcePath, 'utf8');
                await fs.writeFile(targetPath, data);
                
                // Remove old file
                await fs.unlink(sourcePath);
                
                console.log(`✅ Moved ${file.from} → metadata/${file.to}`);
                movedCount++;
                
            } catch (error) {
                console.log(`⚠️  File ${file.from} not found (skipping)`);
                notFoundCount++;
            }
        }
        
        console.log(`\n📊 Reorganization Summary:`);
        console.log(`  • Files moved: ${movedCount}`);
        console.log(`  • Files not found: ${notFoundCount}`);
        console.log(`  • Metadata directory: ${metadataDir}`);
        
        // List current metadata files
        try {
            const metadataFiles = await fs.readdir(metadataDir);
            console.log(`\n📋 Current metadata files:`);
            metadataFiles.forEach(file => {
                console.log(`  • ${file}`);
            });
        } catch (error) {
            console.log('⚠️  Could not list metadata files');
        }
        
        console.log('\n✅ Reorganization completed!');
        console.log('🎯 All utility files are now in the metadata folder');
        
    } catch (error) {
        console.error('❌ Reorganization failed:', error.message);
    }
}

if (require.main === module) {
    reorganizeToMetadata();
}

module.exports = { reorganizeToMetadata };
