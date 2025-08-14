# Repository Guide - kemurphy3 GitHub Portfolio

This guide provides a comprehensive overview of all repositories and their purposes. Use this to quickly identify which repo to clone for specific tasks.

## 📊 Public Repositories (Portfolio)

### 1. **athlete-performance-predictor** (THIS REPO - Main Hub)
**Purpose**: Multi-tenant SaaS platform for fitness data analysis
**Status**: 42% complete, working toward beta launch
**Key Features**:
- FastAPI backend with OAuth (Strava, Garmin)
- Multi-source data integration
- Demo calorie calculator
- PostgreSQL database schemas
**When to use**: Main development, API work, authentication, data ingestion
**Clone**: Already here - this is your working directory

### 2. **calorie_predictor**
**Purpose**: Standalone ML project demonstrating calorie prediction
**Status**: Complete, excellent portfolio piece
**Key Features**:
- Multiple ML models (Linear, RF, XGBoost, LightGBM)
- Research-based approach (15+ papers)
- Clean, professional documentation
**When to use**: ML demonstrations, algorithm reference, portfolio showcase
**Clone**: `gh repo clone kemurphy3/calorie_predictor`

### 3. **fitness-projects**
**Purpose**: Collection of fitness-related applications
**Status**: Active development
**Key Features**:
- Women's soccer readiness app
- Decision-free planner concept
- Multiple sub-projects
**When to use**: NCAA pilot work, B2B features, team-specific tools
**Clone**: `gh repo clone kemurphy3/fitness-projects`

### 4. **ml-injury-prediction-demo**
**Purpose**: Injury risk prediction using ML
**Status**: README complete, implementation pending
**Key Features**:
- 14-day injury prediction
- ACWR calculations
- Biomechanical analysis
**When to use**: Injury prevention features, ML model examples
**Clone**: `gh repo clone kemurphy3/ml-injury-prediction-demo`

### 5. **react-dashboard-components**
**Purpose**: Reusable React components for sports dashboards
**Status**: README complete, implementation pending
**Key Features**:
- Real-time data visualization
- Performance-optimized components
- Mobile-responsive design
**When to use**: Frontend development, dashboard creation, UI components
**Clone**: `gh repo clone kemurphy3/react-dashboard-components`

### 6. **sports-analytics-toolkit**
**Purpose**: Python library for sports performance analysis
**Status**: README complete, implementation pending
**Key Features**:
- Load management calculations
- GPS data processing
- Research-validated algorithms
**When to use**: Backend calculations, data processing, algorithm reference
**Clone**: `gh repo clone kemurphy3/sports-analytics-toolkit`

## 🔒 Private Repositories (Business Logic)

### 7. **vector-core-private**
**Purpose**: Proprietary algorithms and ML models
**Status**: Active, contains production code
**Key Features**:
- EnhancedCalorieCalculator (proprietary)
- MultiAthleteCalorieCalculator
- Advanced ML models
- Enhanced connectors (Garmin, Strava)
**When to use**: Production deployments, proprietary algorithm work
**Clone**: `gh repo clone kemurphy3/vector-core-private`

### 8. **soccer-readiness-private**
**Purpose**: Business-critical soccer readiness features
**Status**: Active, B2B features
**Key Features**:
- VeSync data collector
- Multi-athlete support
- Proprietary readiness algorithms
**When to use**: VeSync integration, B2B features, NCAA pilot
**Clone**: `gh repo clone kemurphy3/soccer-readiness-private`

### 9. **claudeyboy**
**Purpose**: NEON ecosystem data processing
**Status**: Private, work-related code
**Key Features**:
- R/Python scripts for ecological data
- NEON API integration
- Scientific data processing
**When to use**: Ecological data analysis, NEON projects
**Clone**: `gh repo clone kemurphy3/claudeyboy`

### 10. **FitnessPlayhouse**
**Purpose**: Business planning and strategy documents
**Status**: Private, contains sensitive business info
**Key Features**:
- Financial projections
- Market analysis
- Development timelines
- Learning curriculum
**When to use**: Business planning, strategy reference
**Clone**: `gh repo clone kemurphy3/FitnessPlayhouse`

## 🗂️ Quick Reference - What's Where?

### For API Development:
- **athlete-performance-predictor** - Main API implementation
- **vector-core-private** - Proprietary endpoints

### For ML/Data Science:
- **calorie_predictor** - Best ML example
- **ml-injury-prediction-demo** - Injury-specific models
- **sports-analytics-toolkit** - Algorithm implementations
- **vector-core-private** - Production ML models

### For Frontend:
- **react-dashboard-components** - Reusable UI components
- **athlete-performance-predictor** - Integration examples

### For Business Logic:
- **vector-core-private** - Core algorithms
- **soccer-readiness-private** - B2B features
- **FitnessPlayhouse** - Business strategy

### For Data Integration:
- **athlete-performance-predictor** - Strava, Garmin connectors
- **soccer-readiness-private** - VeSync integration
- **claudeyboy** - NEON data processing

## 🚀 Development Workflow

1. **Always start here**: athlete-performance-predictor
2. **Clone private repos** only when needed for proprietary code
3. **Use public repos** for portfolio demonstrations
4. **Delete cloned repos** after each session for security

## 📝 Repository Relationships

```
athlete-performance-predictor (Main Platform)
    ├── Uses: vector-core-private (algorithms)
    ├── Uses: soccer-readiness-private (VeSync)
    ├── Demonstrates: calorie_predictor (simplified)
    ├── Implements: sports-analytics-toolkit (concepts)
    └── Displays with: react-dashboard-components

fitness-projects (Secondary Apps)
    └── Contains: womens-soccer-readiness
        └── Enhanced by: soccer-readiness-private
```

## 🔑 Key Files to Remember

- **Status Updates**: `athlete-performance-predictor/STATUS_UPDATE_2025_01.md`
- **Development Plan**: `athlete-performance-predictor/docs/planning/DEVELOPMENT_PLAN_2025_2028.md`
- **API Docs**: `athlete-performance-predictor/src/api/`
- **Proprietary Algos**: `vector-core-private/src/core/`
- **Business Plans**: `FitnessPlayhouse/FINANCIAL_PROJECTIONS.md`

## 🛡️ Security Reminders

- Public repos contain NO proprietary algorithms
- Private repos contain NO hardcoded credentials
- Use `.env` files for all secrets
- Clone private repos only when needed
- Delete local copies after use

Last Updated: 2025-08-14