#!/usr/bin/env python3
"""
Repository Cleanup Script
Archives legacy files and standardizes naming conventions
"""

import os
import shutil
from pathlib import Path

def cleanup_repository():
    """Clean up repository by archiving legacy files"""
    print("🧹 Starting repository cleanup...")
    
    # Files to archive
    files_to_archive = {
        'old_docs': [
            'SENIOR_DS_ROADMAP.md',
            'PORTFOLIO_READY_PLAN.md', 
            'PROJECT_CONTEXT.md',
            'PORTFOLIO_GRADE_REPORT.md',
            'PERSONAL_FITNESS_INSIGHTS.md',
            'ML_DEEP_LEARNING_ROADMAP.md'
        ],
        'duplicate_scripts': [
            'fitness_metrics_analyzer.py'  # Functionality now in analyze_my_fitness.py
        ]
    }
    
    # Archive files
    for archive_dir, files in files_to_archive.items():
        archive_path = Path(f"archive/{archive_dir}")
        archive_path.mkdir(exist_ok=True)
        
        for file in files:
            if Path(file).exists():
                try:
                    shutil.move(file, archive_path / file)
                    print(f"✅ Archived {file} to {archive_path}")
                except Exception as e:
                    print(f"⚠️ Failed to archive {file}: {e}")
            else:
                print(f"ℹ️ File not found: {file}")
    
    # Create standardized directory structure
    directories = [
        'src/core',
        'src/ml',
        'src/analysis',
        'src/visualization',
        'data/raw',
        'data/processed',
        'data/reports',
        'tests/unit',
        'tests/integration',
        'docs/user',
        'docs/technical'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Move core files to appropriate locations
    core_files = {
        'analyze_my_fitness.py': 'src/core/',
        'ml_models.py': 'src/ml/',
        'streamlit_app.py': 'src/visualization/',
        'vesync_data_collector.py': 'src/analysis/'
    }
    
    for file, dest_dir in core_files.items():
        if Path(file).exists():
            try:
                shutil.move(file, dest_dir + file)
                print(f"✅ Moved {file} to {dest_dir}")
            except Exception as e:
                print(f"⚠️ Failed to move {file}: {e}")
    
    print("\n🎯 Repository cleanup complete!")
    print("📁 Core files organized in src/ directory")
    print("📚 Legacy files archived in archive/ directory")
    print("🧪 Test structure created in tests/ directory")

if __name__ == "__main__":
    cleanup_repository()
