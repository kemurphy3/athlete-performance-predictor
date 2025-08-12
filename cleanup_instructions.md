# Repository Cleanup Instructions

## Files to Remove

### 1. Legacy Calorie Calculator Backup
- **DELETE**: `src/core/calorie_calculator_backup.py`
- **REASON**: Backup of old implementation, new enhanced version already in place

### 2. Duplicate/Outdated Prompts
- **DELETE**: `cursor_calorie_system_prompt.md` (already deleted in repo)
- **DELETE**: `cursor_calorie_system_prompt_updated.md`
- **KEEP**: `cursor_calorie_system_prompt_final.md` (this is the latest version)
- **REASON**: Only need the final version with multi-athlete support

### 3. Temporary Enhancement File
- **DELETE**: `multi_athlete_enhancement.md`
- **REASON**: Content already incorporated into final prompt

### 4. Legacy Scripts (Already Archived)
- **KEEP**: Everything in `archive/` directory
- **REASON**: Already properly organized for historical reference

### 5. Old Analysis Scripts
- **MOVE TO ARCHIVE**: `src/core/analyze_my_fitness.py`
- **REASON**: Appears to be old single-user analysis script, superseded by new architecture

## Files to Keep

### Essential Documentation
- All main directory `.md` files (README, USAGE_GUIDE, etc.)
- `env_template.txt` - needed for setup
- `requirements.txt` - needed for dependencies

### Core Implementation
- All files in `src/connectors/` - active connector implementations
- All files in `src/core/` EXCEPT `analyze_my_fitness.py` and `calorie_calculator_backup.py`
- `src/cli.py` - main CLI interface

### Data Files
- Keep all files in `data/` - these are user's actual workout data

## Cleanup Commands

```bash
# Remove backup and temporary files
rm src/core/calorie_calculator_backup.py
rm cursor_calorie_system_prompt_updated.md
rm multi_athlete_enhancement.md

# Archive old analysis script
mkdir -p archive/legacy_code/analysis
mv src/core/analyze_my_fitness.py archive/legacy_code/analysis/

# Remove this cleanup file after completion
rm cleanup_instructions.md
```

## Post-Cleanup Verification

After cleanup, verify:
1. `cursor_calorie_system_prompt_final.md` exists (main implementation guide)
2. `src/core/calorie_calculator.py` exists (enhanced implementation)
3. No duplicate prompt files remain
4. All legacy code is in `archive/` directory

---

**DELETE THIS FILE AFTER CLEANUP IS COMPLETE**