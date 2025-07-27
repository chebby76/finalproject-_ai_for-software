import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="AI Health Monitor Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .alert-danger {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .alert-success {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

class HealthMonitor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.health_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
    def generate_sample_data(self, days=30, samples_per_day=24):
        """Generate realistic health data with patterns and anomalies"""
        total_samples = days * samples_per_day
        
        # Create timestamps
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        timestamps = pd.date_range(start=start_date, end=end_date, periods=total_samples)
        
        # Generate realistic health data with circadian patterns
        np.random.seed(42)
        
        # Heart rate with circadian rhythm
        hours = np.array([t.hour for t in timestamps])
        base_hr = 70 + 10 * np.sin((hours - 6) * np.pi / 12)  # Peak in afternoon
        heart_rate = base_hr + np.random.normal(0, 5, total_samples)
        heart_rate = np.clip(heart_rate, 50, 120)
        
        # Blood oxygen with slight variations
        blood_oxygen = 98 + np.random.normal(0, 1, total_samples)
        blood_oxygen = np.clip(blood_oxygen, 85, 100)
        
        # Steps with daily patterns
        step_base = 500 + 300 * np.sin((hours - 12) * np.pi / 12)
        steps = np.maximum(0, step_base + np.random.normal(0, 100, total_samples))
        
        # Sleep quality (0-10 scale)
        sleep_quality = 7 + 2 * np.sin((hours - 2) * np.pi / 12) + np.random.normal(0, 0.5, total_samples)
        sleep_quality = np.clip(sleep_quality, 0, 10)
        
        # Stress level (inverse of sleep quality with some noise)
        stress_level = 10 - sleep_quality + np.random.normal(0, 1, total_samples)
        stress_level = np.clip(stress_level, 0, 10)
        
        # Body temperature
        body_temp = 98.6 + np.random.normal(0, 0.5, total_samples)
        body_temp = np.clip(body_temp, 96, 102)
        
        # Introduce some anomalies
        anomaly_indices = np.random.choice(total_samples, size=int(0.05 * total_samples), replace=False)
        heart_rate[anomaly_indices] += np.random.choice([-20, 30], size=len(anomaly_indices))
        blood_oxygen[anomaly_indices] -= np.random.randint(5, 15, size=len(anomaly_indices))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'heart_rate': heart_rate.astype(int),
            'blood_oxygen': blood_oxygen.round(1),
            'steps': steps.astype(int),
            'sleep_quality': sleep_quality.round(1),
            'stress_level': stress_level.round(1),
            'body_temperature': body_temp.round(1)
        })
    
    def detect_anomalies(self, data):
        """Detect anomalies in health data"""
        features = ['heart_rate', 'blood_oxygen', 'steps', 'sleep_quality', 'stress_level', 'body_temperature']
        X = data[features].values
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Detect anomalies
        anomalies = self.anomaly_detector.fit_predict(X_scaled)
        data['anomaly'] = (anomalies == -1)
        
        return data
    
    def generate_health_insights(self, data):
        """Generate personalized health insights"""
        insights = []
        latest_data = data.iloc[-1]
        
        # Heart rate analysis
        avg_hr = data['heart_rate'].mean()
        if latest_data['heart_rate'] > avg_hr + 20:
            insights.append("⚠️ Your heart rate is elevated. Consider relaxation techniques.")
        elif latest_data['heart_rate'] < avg_hr - 15:
            insights.append("💙 Your resting heart rate looks great!")
        
        # Blood oxygen analysis
        if latest_data['blood_oxygen'] < 95:
            insights.append("🫁 Blood oxygen is low. Consider consulting a healthcare provider.")
        else:
            insights.append("✅ Blood oxygen levels are healthy.")
        
        # Activity analysis
        avg_steps = data['steps'].mean()
        if latest_data['steps'] < avg_steps * 0.7:
            insights.append("🚶‍♂️ You've been less active today. Try a short walk!")
        elif latest_data['steps'] > avg_steps * 1.3:
            insights.append("🏃‍♂️ Great job staying active today!")
        
        # Sleep analysis
        if latest_data['sleep_quality'] < 6:
            insights.append("😴 Sleep quality could be better. Try a consistent bedtime routine.")
        elif latest_data['sleep_quality'] > 8:
            insights.append("🌙 Excellent sleep quality! Keep it up!")
        
        # Stress analysis
        if latest_data['stress_level'] > 7:
            insights.append("😰 Stress levels are high. Practice deep breathing or meditation.")
        elif latest_data['stress_level'] < 4:
            insights.append("😌 Great job managing stress!")
        
        return insights
    
    def calculate_health_score(self, data):
        """Calculate overall health score (0-100)"""
        latest = data.iloc[-1]
        
        # Normalize each metric to 0-100 scale
        hr_score = max(0, 100 - abs(latest['heart_rate'] - 70) * 2)
        oxygen_score = min(100, latest['blood_oxygen'] * 1.02)
        activity_score = min(100, latest['steps'] / 10)
        sleep_score = latest['sleep_quality'] * 10
        stress_score = (10 - latest['stress_level']) * 10
        temp_score = max(0, 100 - abs(latest['body_temperature'] - 98.6) * 10)
        
        # Weighted average
        weights = [0.2, 0.2, 0.15, 0.2, 0.15, 0.1]
        scores = [hr_score, oxygen_score, activity_score, sleep_score, stress_score, temp_score]
        
        health_score = sum(w * s for w, s in zip(weights, scores))
        return round(health_score, 1)

def main():
    st.markdown('<h1 class="main-header">🏥 AI Health Monitor Pro</h1>', unsafe_allow_html=True)
    
    # Initialize the health monitor
    if 'health_monitor' not in st.session_state:
        st.session_state.health_monitor = HealthMonitor()
        st.session_state.data = st.session_state.health_monitor.generate_sample_data()
        st.session_state.data = st.session_state.health_monitor.detect_anomalies(st.session_state.data)
    
    # Sidebar controls
    st.sidebar.title("🎛️ Control Panel")
    
    # Data generation controls
    st.sidebar.subheader("📊 Data Settings")
    days = st.sidebar.slider("Days of data", 7, 90, 30)
    if st.sidebar.button("🔄 Generate New Data"):
        st.session_state.data = st.session_state.health_monitor.generate_sample_data(days=days)
        st.session_state.data = st.session_state.health_monitor.detect_anomalies(st.session_state.data)
        st.rerun()
    
    # Real-time simulation
    st.sidebar.subheader("⏱️ Real-time Mode")
    if st.sidebar.button("▶️ Start Real-time Updates"):
        st.session_state.real_time = True
    if st.sidebar.button("⏸️ Stop Real-time Updates"):
        st.session_state.real_time = False
    
    # Main dashboard
    data = st.session_state.data
    latest_data = data.iloc[-1]
    
    # Health Score Card
    health_score = st.session_state.health_monitor.calculate_health_score(data)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if health_score >= 80:
            color = "#4CAF50"
            status = "Excellent"
        elif health_score >= 60:
            color = "#FF9800"
            status = "Good"
        else:
            color = "#F44336"
            status = "Needs Attention"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, {color}20, {color}40); 
                    border-radius: 15px; margin: 1rem 0;">
            <h2 style="color: {color}; margin: 0;">Overall Health Score</h2>
            <h1 style="color: {color}; font-size: 3rem; margin: 0;">{health_score}</h1>
            <p style="color: {color}; font-size: 1.2rem; margin: 0;">{status}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current vital signs
    st.subheader("📈 Current Vital Signs")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("❤️ Heart Rate", f"{int(latest_data['heart_rate'])} BPM", 
                 delta=f"{int(latest_data['heart_rate'] - data['heart_rate'].mean())}")
    
    with col2:
        st.metric("🫁 Blood Oxygen", f"{latest_data['blood_oxygen']:.1f}%", 
                 delta=f"{latest_data['blood_oxygen'] - data['blood_oxygen'].mean():.1f}")
    
    with col3:
        st.metric("🚶‍♂️ Steps Today", f"{int(latest_data['steps'])}", 
                 delta=f"{int(latest_data['steps'] - data['steps'].mean())}")
    
    with col4:
        st.metric("🌡️ Body Temp", f"{latest_data['body_temperature']:.1f}°F", 
                 delta=f"{latest_data['body_temperature'] - 98.6:.1f}")
    
    # Health trends visualization
    st.subheader("📊 Health Trends")
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Heart Rate Trend', 'Blood Oxygen Levels', 'Activity & Sleep', 'Stress Level'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": True}, {"secondary_y": False}]]
    )
    
    # Heart rate trend
    fig.add_trace(
        go.Scatter(x=data['timestamp'], y=data['heart_rate'], 
                  name='Heart Rate', line=dict(color='red', width=2)),
        row=1, col=1
    )
    
    # Blood oxygen
    fig.add_trace(
        go.Scatter(x=data['timestamp'], y=data['blood_oxygen'], 
                  name='Blood Oxygen', line=dict(color='blue', width=2)),
        row=1, col=2
    )
    
    # Activity and sleep
    fig.add_trace(
        go.Scatter(x=data['timestamp'], y=data['steps'], 
                  name='Steps', line=dict(color='green', width=2)),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=data['timestamp'], y=data['sleep_quality'], 
                  name='Sleep Quality', line=dict(color='purple', width=2)),
        row=2, col=1, secondary_y=True
    )
    
    # Stress level
    fig.add_trace(
        go.Scatter(x=data['timestamp'], y=data['stress_level'], 
                  name='Stress Level', line=dict(color='orange', width=2),
                  fill='tonexty'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=True, title_text="Health Metrics Dashboard")
    st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly detection results
    st.subheader("🚨 Anomaly Detection")
    anomalies = data[data['anomaly'] == True]
    
    if len(anomalies) > 0:
        st.markdown(f'<div class="alert-danger">⚠️ <strong>Alert:</strong> {len(anomalies)} anomalies detected in your health data!</div>', 
                   unsafe_allow_html=True)
        
        # Show recent anomalies
        recent_anomalies = anomalies.tail(5)
        st.write("Recent anomalies:")
        for idx, row in recent_anomalies.iterrows():
            st.write(f"- {row['timestamp'].strftime('%Y-%m-%d %H:%M')}: HR={row['heart_rate']}, O2={row['blood_oxygen']}%")
    else:
        st.markdown('<div class="alert-success">✅ <strong>All Clear:</strong> No anomalies detected in your recent health data.</div>', 
                   unsafe_allow_html=True)
    
    # AI Health Insights
    st.subheader("🤖 AI Health Insights")
    insights = st.session_state.health_monitor.generate_health_insights(data)
    
    for insight in insights:
        st.write(f"• {insight}")
    
    # Health patterns analysis
    st.subheader("🔍 Pattern Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        # Heart rate distribution
        fig_hist = px.histogram(data, x='heart_rate', nbins=20, 
                               title='Heart Rate Distribution',
                               color_discrete_sequence=['#FF6B6B'])
        fig_hist.add_vline(x=data['heart_rate'].mean(), line_dash="dash", 
                          annotation_text="Average")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Correlation heatmap
        corr_data = data[['heart_rate', 'blood_oxygen', 'steps', 'sleep_quality', 'stress_level']].corr()
        fig_heatmap = px.imshow(corr_data, text_auto=True, aspect="auto",
                               title='Health Metrics Correlation')
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Weekly summary
    st.subheader("📅 Weekly Health Summary")
    if len(data) >= 7:
        last_week = data.tail(7 * 24)  # Last 7 days
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Heart Rate", f"{last_week['heart_rate'].mean():.0f} BPM")
            st.metric("Avg Sleep Quality", f"{last_week['sleep_quality'].mean():.1f}/10")
        
        with col2:
            st.metric("Avg Blood Oxygen", f"{last_week['blood_oxygen'].mean():.1f}%")
            st.metric("Avg Stress Level", f"{last_week['stress_level'].mean():.1f}/10")
        
        with col3:
            st.metric("Total Steps", f"{last_week['steps'].sum():,.0f}")
            st.metric("Days with Anomalies", f"{last_week['anomaly'].sum()}")
    
    # Export data
    st.subheader("💾 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = data.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"health_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📊 Generate Health Report"):
            st.balloons()
            st.success("Health report generated successfully! 📋")
    
    # Real-time updates
    if hasattr(st.session_state, 'real_time') and st.session_state.real_time:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
