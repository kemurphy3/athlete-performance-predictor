# AI-Powered Fitness Dashboard - Implementation Prompt

## Overview
Create an interactive web dashboard using Streamlit that visualizes fitness data, provides AI-driven insights, and allows users to ask questions about their training. The dashboard should be beautiful, intuitive, and provide actionable insights.

## Technology Stack
- **Frontend**: Streamlit (already in requirements.txt)
- **Visualization**: Plotly, Altair
- **AI Integration**: OpenAI API or local LLM
- **Backend**: Existing SQLite + Python infrastructure

## Dashboard Architecture

### 1. Main Layout
```python
# src/dashboard/app.py
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="AI Fitness Coach Dashboard",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for athlete selection and date range
with st.sidebar:
    athlete_id = st.selectbox("Select Athlete", get_athlete_list())
    date_range = st.date_input(
        "Date Range",
        value=(datetime.now() - timedelta(days=90), datetime.now()),
        max_value=datetime.now()
    )
    
# Main content area with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "💪 Performance", 
    "❤️ Health", 
    "🤖 AI Insights", 
    "💬 Ask AI"
])
```

### 2. Overview Tab - Key Metrics Dashboard

```python
with tab1:
    # Metric cards row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Fitness Score (CTL)",
            value=f"{current_fitness:.1f}",
            delta=f"{fitness_change:+.1f} vs last month",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="Fatigue Level",
            value=fatigue_level,
            delta=fatigue_trend,
            delta_color="inverse"  # Red is bad
        )
    
    with col3:
        st.metric(
            label="Injury Risk",
            value=injury_risk['level'],
            delta=f"{injury_risk['change']}% vs last week",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Weekly Volume",
            value=f"{weekly_hours:.1f} hrs",
            delta=f"{volume_change:+.1f} hrs"
        )
    
    # Training Load Chart
    st.subheader("Training Load & Recovery")
    fig_load = create_training_load_chart(athlete_data)
    st.plotly_chart(fig_load, use_container_width=True)
    
    # Activity Calendar Heatmap
    st.subheader("Activity Calendar")
    fig_calendar = create_calendar_heatmap(workouts)
    st.plotly_chart(fig_calendar, use_container_width=True)
```

### 3. Performance Tab - Deep Analytics

```python
with tab2:
    sport_filter = st.selectbox("Select Sport", ["All"] + get_sport_list())
    
    # Performance Trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pace/Speed Progression")
        fig_pace = create_pace_trend_chart(filtered_workouts)
        st.plotly_chart(fig_pace, use_container_width=True)
        
    with col2:
        st.subheader("Heart Rate Zones")
        fig_hr = create_hr_zone_distribution(filtered_workouts)
        st.plotly_chart(fig_hr, use_container_width=True)
    
    # Sport-Specific Analysis
    if sport_filter == "Soccer":
        st.subheader("Soccer Performance Analysis")
        
        # Sprint Analysis
        sprint_data = analyze_soccer_sprints(workouts)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Sprints/Game", f"{sprint_data['avg_sprints']:.0f}")
        with col2:
            st.metric("High Intensity %", f"{sprint_data['high_intensity_pct']:.1f}%")
        with col3:
            st.metric("Recovery Quality", sprint_data['recovery_score'])
        
        # Movement Pattern Visualization
        fig_movement = create_soccer_movement_chart(sprint_data)
        st.plotly_chart(fig_movement, use_container_width=True)
```

### 4. Health Tab - Biometric Tracking

```python
with tab3:
    # Weight Trend from VeSync
    st.subheader("Body Composition Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_weight = create_weight_trend_chart(biometric_data)
        st.plotly_chart(fig_weight, use_container_width=True)
        
    with col2:
        if body_fat_data:
            fig_bf = create_body_fat_chart(biometric_data)
            st.plotly_chart(fig_bf, use_container_width=True)
    
    # Resting Heart Rate Analysis
    st.subheader("Recovery Indicators")
    fig_rhr = create_resting_hr_analysis(hr_data)
    st.plotly_chart(fig_rhr, use_container_width=True)
    
    # Sleep Quality Estimation
    if morning_hr_data:
        st.subheader("Estimated Sleep Quality")
        sleep_score = estimate_sleep_from_morning_hr(morning_hr_data)
        st.progress(sleep_score / 100)
        st.caption(f"Based on morning HR variability")
```

### 5. AI Insights Tab - Automated Analysis

```python
with tab4:
    # Generate insights on tab load
    insights = generate_ai_insights(athlete_id, date_range)
    
    # Injury Risk Alert
    if insights['injury_risk']['level'] == 'HIGH':
        st.error(f"⚠️ **High Injury Risk Detected**")
        st.write(insights['injury_risk']['explanation'])
        st.write("**Recommended Actions:**")
        for action in insights['injury_risk']['actions']:
            st.write(f"• {action}")
    
    # Training Recommendations
    st.subheader("🎯 Personalized Training Recommendations")
    
    for rec in insights['recommendations']:
        with st.expander(rec['title'], expanded=True):
            st.write(rec['explanation'])
            if rec['type'] == 'workout':
                st.code(rec['workout_plan'])
            elif rec['type'] == 'recovery':
                st.info(rec['recovery_protocol'])
    
    # Performance Predictions
    st.subheader("📈 Performance Projections")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Predicted 5K Time (4 weeks)",
            format_time(insights['predictions']['5k']),
            delta=format_time_delta(insights['predictions']['5k_improvement'])
        )
    
    # Fatigue & Recovery Optimization
    st.subheader("😴 Recovery Optimization")
    
    recovery_plan = insights['recovery_optimization']
    st.write(f"**Current Fatigue Level:** {recovery_plan['fatigue_level']}")
    st.write(f"**Optimal Rest Days:** {recovery_plan['rest_days_needed']}")
    
    if recovery_plan['rest_days_needed'] > 0:
        st.warning(f"Consider taking {recovery_plan['rest_days_needed']} rest days")
        st.write("**If rest isn't possible:**")
        for alternative in recovery_plan['alternatives']:
            st.write(f"• {alternative}")
```

### 6. Ask AI Tab - Interactive Q&A

```python
with tab5:
    st.subheader("💬 Ask Your AI Fitness Coach")
    
    # Suggested questions
    st.write("**Suggested Questions:**")
    
    suggested_questions = [
        "Am I ready for a marathon based on my current fitness?",
        "How can I improve my soccer sprint recovery?",
        "What's causing my recent performance plateau?",
        "Should I be concerned about my elevated resting heart rate?",
        "How do I balance strength training with running?",
        "What's my optimal race pace for a 10K?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(question, key=f"q_{i}"):
                st.session_state.current_question = question
    
    # Custom question input
    user_question = st.text_area(
        "Or ask your own question:",
        value=st.session_state.get('current_question', ''),
        height=100
    )
    
    if st.button("Get AI Analysis", type="primary"):
        if user_question:
            with st.spinner("Analyzing your data..."):
                # Prepare context
                context = prepare_athlete_context(athlete_id, date_range)
                
                # Get AI response
                response = get_ai_response(user_question, context)
                
                # Display response
                st.markdown("### AI Coach Response:")
                st.write(response['answer'])
                
                # Show relevant charts if applicable
                if response.get('charts'):
                    for chart in response['charts']:
                        st.plotly_chart(chart, use_container_width=True)
                
                # Show data sources used
                with st.expander("Data sources used for this analysis"):
                    st.json(response['data_sources'])
```

### 7. AI Integration Layer

```python
# src/dashboard/ai_coach.py
class AIFitnessCoach:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.system_prompt = """
        You are an expert fitness coach and sports scientist. You have access to:
        - Workout data (duration, intensity, heart rate, calories)
        - Biometric data (weight, body composition) 
        - Training load metrics (CTL, ATL, TSB)
        - Sport-specific performance data
        
        Provide evidence-based recommendations that are:
        1. Specific and actionable
        2. Based on the athlete's actual data
        3. Scientifically sound
        4. Injury-prevention focused
        """
    
    def analyze_injury_risk(self, athlete_data: Dict) -> Dict:
        """Analyze injury risk using multiple factors"""
        
        risk_factors = {
            'load_spike': self._check_load_spike(athlete_data),
            'insufficient_recovery': self._check_recovery(athlete_data),
            'volume_intensity_imbalance': self._check_balance(athlete_data),
            'fatigue_accumulation': self._check_fatigue(athlete_data)
        }
        
        # Calculate composite risk score
        risk_score = sum(f['score'] * f['weight'] for f in risk_factors.values())
        
        return {
            'score': risk_score,
            'level': self._get_risk_level(risk_score),
            'factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_factors)
        }
    
    def generate_workout_recommendations(self, athlete_data: Dict) -> List[Dict]:
        """Generate personalized workout recommendations"""
        
        recommendations = []
        
        # Check training balance
        balance = self._analyze_training_balance(athlete_data)
        
        if balance['needs_more_easy']:
            recommendations.append({
                'type': 'workout',
                'title': 'Add Easy Recovery Runs',
                'explanation': f"You're doing {balance['hard_percentage']:.0f}% hard training. "
                              f"Aim for 80% easy, 20% hard.",
                'workout_plan': self._generate_easy_workout(athlete_data)
            })
        
        if balance['needs_strength']:
            recommendations.append({
                'type': 'workout',
                'title': 'Incorporate Strength Training',
                'explanation': "Adding 2x weekly strength sessions can improve "
                              "running economy by 5% and reduce injury risk by 30%.",
                'workout_plan': self._generate_strength_workout(athlete_data)
            })
        
        return recommendations
    
    def answer_question(self, question: str, context: Dict) -> Dict:
        """Answer user questions with context-aware responses"""
        
        # Prepare prompt with context
        prompt = f"""
        Athlete Context:
        - Recent Training Load: {context['training_load']}
        - Current Fitness (CTL): {context['fitness_score']}
        - Fatigue (ATL): {context['fatigue_score']}
        - Primary Sport: {context['primary_sport']}
        - Recent Performance: {context['recent_performance']}
        
        Question: {question}
        
        Provide a detailed, actionable answer based on the data.
        """
        
        # Get AI response
        response = self._call_ai_api(prompt)
        
        # Extract relevant data for charts
        chart_data = self._identify_relevant_charts(question, context)
        
        return {
            'answer': response,
            'charts': chart_data,
            'data_sources': context['data_sources']
        }
```

### 8. Visualization Components

```python
# src/dashboard/visualizations.py

def create_training_load_chart(data: pd.DataFrame) -> go.Figure:
    """Create interactive training load chart with CTL/ATL/TSB"""
    
    fig = go.Figure()
    
    # Fitness (CTL) - Blue
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['ctl'],
        name='Fitness (CTL)',
        line=dict(color='blue', width=3),
        fill='tozeroy',
        fillcolor='rgba(0,100,255,0.1)'
    ))
    
    # Fatigue (ATL) - Red
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['atl'],
        name='Fatigue (ATL)',
        line=dict(color='red', width=2)
    ))
    
    # Form (TSB) - Green
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['tsb'],
        name='Form (TSB)',
        line=dict(color='green', width=2),
        fill='tozeroy',
        fillcolor='rgba(0,255,0,0.1)'
    ))
    
    # Add annotations for key events
    fig.add_annotation(
        x=peak_date,
        y=peak_fitness,
        text="Peak Fitness",
        showarrow=True
    )
    
    fig.update_layout(
        title="Training Load Management",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_soccer_movement_chart(sprint_data: Dict) -> go.Figure:
    """Visualize soccer movement patterns"""
    
    fig = go.Figure()
    
    # Movement intensity distribution
    categories = ['Walk', 'Jog', 'Run', 'Sprint']
    percentages = [
        sprint_data['walk_pct'],
        sprint_data['jog_pct'],
        sprint_data['run_pct'],
        sprint_data['sprint_pct']
    ]
    
    fig.add_trace(go.Bar(
        x=categories,
        y=percentages,
        text=[f"{p:.1f}%" for p in percentages],
        textposition='auto',
        marker_color=['lightblue', 'blue', 'orange', 'red']
    ))
    
    fig.update_layout(
        title="Movement Pattern Distribution",
        yaxis_title="Percentage of Game Time",
        showlegend=False
    )
    
    return fig
```

### 9. Real-time Updates

```python
# Auto-refresh data
if st.checkbox("Auto-refresh (5 min)", value=True):
    st.empty()
    time.sleep(300)
    st.experimental_rerun()

# WebSocket for real-time updates (future enhancement)
async def stream_live_data():
    """Stream live data from connected devices"""
    pass
```

### 10. Configuration & Deployment

```yaml
# config/dashboard.yml
dashboard:
  title: "AI Fitness Coach"
  theme: "light"
  
ai_coach:
  provider: "openai"  # or "local_llm"
  model: "gpt-4"
  temperature: 0.7
  
features:
  live_hr_monitoring: false
  weather_integration: true
  social_sharing: false
  
cache:
  ttl_minutes: 15
  redis_enabled: false
```

### 11. Security & Privacy

```python
# Authentication
if not check_authentication():
    st.error("Please login to access your dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        authenticate_user(username, password)

# Data privacy
st.sidebar.markdown("---")
if st.sidebar.button("Download My Data"):
    export_athlete_data(athlete_id)
    
if st.sidebar.button("Delete My Data"):
    if st.confirm("Are you sure?"):
        delete_athlete_data(athlete_id)
```

## Launch Command

```bash
# Run dashboard
streamlit run src/dashboard/app.py --server.port 8501

# Or with make
make dashboard
```

This dashboard provides a comprehensive, AI-powered fitness analytics platform that grows more intelligent with use.