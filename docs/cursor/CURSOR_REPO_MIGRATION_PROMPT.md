# Cursor Prompt: Repository Migration & Portfolio Setup

## Objective
Reorganize GitHub repositories to protect business IP while building an impressive public portfolio.

## Current State
- `athlete-performance-predictor` repo contains Vector (adaptive fitness intelligence) code
- Building two apps: Women's Soccer Readiness (B2B) and Vector (B2C)
- Some sensitive business logic is currently in public repos

## Required Tasks

### Task 1: Create Private Repositories
1. Create new private repo: `soccer-readiness-private`
2. Create new private repo: `vector-core-private`
3. Move all business logic, algorithms, and revenue code to private repos
4. Remove any API keys, credentials, or client data from history

### Task 2: Create Public Portfolio Repositories

#### 1. `sports-analytics-toolkit`
- Generic sports data analysis functions
- Example visualizations using public datasets
- Clean, well-documented code showing technical skills
- MIT license

#### 2. `react-dashboard-components`
- Reusable dashboard components (charts, cards, tables)
- Storybook documentation
- No business-specific logic
- Modern React patterns showcasing skills

#### 3. `ml-injury-prediction-demo`
- Basic ML model using public sports data
- Jupyter notebook showing process
- Clean implementation without proprietary algorithms

### Task 3: Clean Current Repository
1. Scan `athlete-performance-predictor` for:
   - API keys or secrets in history
   - Business-specific algorithms
   - Client data or references
   - Pricing/revenue logic

2. Either:
   - Remove sensitive files and clean git history, OR
   - Archive current repo and create clean public version

### Task 4: Create Portfolio Structure
Create README.md for GitHub profile showcasing:
- Public repos with clear descriptions
- Technologies used
- Links to live demos (if applicable)
- Professional presentation

## Important Security Considerations
- Use git filter-branch or BFG to completely remove sensitive data from history
- Ensure no business logic that could be copied by competitors remains public
- Keep enough public code to demonstrate skills to recruiters
- Add clear documentation to all public repos

## Specific Files to Migrate

### Keep Public (Generic/Educational):
- Generic data models
- Open source utilities
- Example visualizations
- Documentation
- Test frameworks

### Move to Private (Business Critical):
- `src/core/deduplication.py` - Proprietary dedup algorithm
- `src/analysis/calorie_calculation.py` - 83% accuracy secret sauce
- `src/core/injury_prediction.py` - ML model specifics
- Any OAuth implementation details
- Customer-specific code
- Pricing/billing logic
- API keys and credentials

## Migration Commands

```bash
# Backup everything first
cp -r athlete-performance-predictor athlete-performance-predictor-backup

# Use BFG to clean sensitive data
java -jar bfg.jar --delete-files "*.env" athlete-performance-predictor
java -jar bfg.jar --delete-folders "credentials" athlete-performance-predictor
java -jar bfg.jar --replace-text passwords.txt athlete-performance-predictor

# After cleaning, force push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

## Expected Outcome
- 3-4 impressive public repos for portfolio
- 2 private repos with all business logic
- Clean git history with no sensitive data
- Professional GitHub profile attractive to recruiters
- Protected IP while showcasing skills