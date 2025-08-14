# Public/Private Repository Separation Guide

## Overview
This document outlines the separation between public portfolio/demo code and private business-critical code.

## Public Repository (athlete-performance-predictor)
**Purpose**: Portfolio demonstration, open-source framework, API documentation

### Contains:
- Basic framework and architecture
- Demo calorie calculator (MET-based)
- API endpoint definitions (without proprietary logic)
- Basic data models
- Authentication framework
- Documentation and guides
- Test structure

### Does NOT contain:
- Enhanced calorie calculation algorithms
- Multi-athlete support logic
- VeSync integration
- Business-critical ML models
- Proprietary data processing

## Private Repositories

### vector-core-private
**Contains**:
- EnhancedCalorieCalculator with proprietary algorithms
- MultiAthleteCalorieCalculator for B2B features
- Advanced ML models
- Proprietary connectors (Garmin, Strava enhanced features)

### soccer-readiness-private
**Contains**:
- VeSync data collector and integration
- Proprietary readiness algorithms
- B2B-specific features

## Integration Strategy

### For Development:
1. Public repo serves as the base framework
2. Private repos are added as dependencies
3. Environment variables determine which features are available

### Example Structure:
```python
# In public repo
try:
    from vector_core_private import EnhancedCalorieCalculator
    calculator = EnhancedCalorieCalculator()
except ImportError:
    from .demo_calorie_calculator import DemoCalorieCalculator
    calculator = DemoCalorieCalculator()
```

## Security Checklist
- [ ] No API keys or secrets in public repos
- [ ] No proprietary algorithms in public repos
- [ ] No business logic that provides competitive advantage
- [ ] Clear separation of demo vs production features
- [ ] Regular audits of public repositories

## Deployment
- Production deployments use private repositories
- Demo/portfolio deployments use public repository only
- CI/CD configured to handle both scenarios