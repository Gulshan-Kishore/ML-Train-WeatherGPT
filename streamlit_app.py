"""
WeatherGPT — Offline Supervised Machine Learning Weather Assistant
==================================================================
A modern conversational web interface built with Streamlit:
- User questions on the right in light green cards
- WeatherGPT answers on the left in clean white cards
- 100% offline predictions using scikit-learn Random Forest models
- Interactive atmospheric simulator & performance metrics
"""

import os
from datetime import datetime
import streamlit as st

# Local project modules
from src.predictor import WeatherPredictor, parse_weather_intent, format_chat_response
from src.city_database import resolve_city_climate
from src.utils import render_chat_bubble_html
from train import train_and_evaluate

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="WeatherGPT — Offline ML Assistant",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling and messenger container styles
st.markdown("""
<style>
    /* Dark background aesthetics */
    .stApp {
        background-color: #0e1117;
    }

    /* Offline badge */
    .offline-tag {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.3);
        display: inline-block;
        margin-bottom: 0.8rem;
    }

    /* Action buttons styling */
    .stButton button {
        border-radius: 8px;
        font-size: 0.85rem;
        padding: 6px 12px;
        transition: all 0.2s ease;
    }

    /* Sidebar quick city buttons */
    div[data-testid="stSidebar"] .stButton button {
        border-radius: 8px;
        font-size: 0.82rem;
    }

    /* Chat messages scroll container */
    .chat-scroll-container {
        padding: 0.5rem 0;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Model Loading (Cached for performance)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_predictor():
    """Loads the offline ML model once and caches it in memory."""
    model_path = "models/weather_model.pkl"
    if not os.path.exists(model_path):
        train_and_evaluate()
    return WeatherPredictor(model_path)


try:
    predictor = get_predictor()
except Exception as e:
    st.error(f"Error loading offline ML model: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# 3. Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    now_time = datetime.now().strftime("%H:%M")
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Hello! I am WeatherGPT.**\n\n"
                "I am an **offline Supervised Machine Learning assistant** trained on multi-year historical climate observations.\n\n"
                "• Ask me about **rain**, **temperature**, or **weather conditions** for any city.\n"
                "• All predictions run **100% locally** from trained decision tree models without an external API.\n\n"
                "💡 Try clicking one of the sample questions below to get started!"
            ),
            "tag": "Welcome",
            "timestamp": now_time
        }
    ]

if "current_city" not in st.session_state:
    st.session_state.current_city = "Mumbai"

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


# -----------------------------------------------------------------------------
# 4. Message Processing Helper
# -----------------------------------------------------------------------------
def process_user_query(query_text: str):
    """
    Handles user question:
    1. Appends question to chat messages
    2. Parses intent & extracts city/atmospheric overrides
    3. Runs offline ML inference
    4. Appends assistant response to chat messages
    """
    if not query_text or not query_text.strip():
        return

    user_time = datetime.now().strftime("%H:%M")

    # 1. Record user message
    st.session_state.messages.append({
        "role": "user",
        "content": query_text.strip(),
        "tag": "User",
        "timestamp": user_time
    })

    # 2. Parse query intent
    active_city = st.session_state.current_city
    parsed = parse_weather_intent(query_text, default_city=active_city)

    # Update active city if explicitly stated by the user
    if parsed.get("city_was_explicit") and parsed.get("city"):
        st.session_state.current_city = parsed["city"]

    # 3. Run model inference and format response
    response_dict = format_chat_response(parsed, predictor)
    bot_time = datetime.now().strftime("%H:%M")

    # 4. Record bot response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_dict["text"],
        "tag": response_dict.get("tag", "Forecast"),
        "timestamp": bot_time
    })


# Process any queued button click query
if st.session_state.pending_query:
    queued = st.session_state.pending_query
    st.session_state.pending_query = None
    process_user_query(queued)


# -----------------------------------------------------------------------------
# 5. Sidebar Layout
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌦️ WeatherGPT")
    st.caption("AI-powered weather assistant (ML-based)")
    st.markdown('<span class="offline-tag">⚡ 100% OFFLINE MODEL</span>', unsafe_allow_html=True)

    # City Search Input
    st.markdown("#### 📊 Select City")
    city_input = st.text_input(
        "Enter city name:",
        placeholder="e.g. Mumbai, London, Tokyo",
        label_visibility="visible"
    )
    if st.button("📍 Get Weather", width="stretch"):
        if city_input.strip():
            st.session_state.current_city = city_input.strip().title()
            st.session_state.pending_query = f"What is the weather in {city_input.strip().title()}?"
            st.rerun()

    # Quick Select City Buttons
    st.markdown("**⚡ Quick Cities**")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        if st.button("Mumbai", width="stretch"):
            st.session_state.current_city = "Mumbai"
            st.session_state.pending_query = "Will it rain today in Mumbai?"
            st.rerun()
        if st.button("Bangalore", width="stretch"):
            st.session_state.current_city = "Bangalore"
            st.session_state.pending_query = "What is the temperature in Bangalore?"
            st.rerun()
        if st.button("New York", width="stretch"):
            st.session_state.current_city = "New York"
            st.session_state.pending_query = "Weather forecast for New York"
            st.rerun()
    with q_col2:
        if st.button("Delhi", width="stretch"):
            st.session_state.current_city = "Delhi"
            st.session_state.pending_query = "Will it rain tomorrow in Delhi?"
            st.rerun()
        if st.button("London", width="stretch"):
            st.session_state.current_city = "London"
            st.session_state.pending_query = "Is it raining in London?"
            st.rerun()
        if st.button("Tokyo", width="stretch"):
            st.session_state.current_city = "Tokyo"
            st.session_state.pending_query = "Forecast for Tokyo"
            st.rerun()

    st.markdown("---")

    # Interactive Atmospheric Simulator
    with st.expander("🎛️ Atmospheric Simulator", expanded=False):
        st.caption("Tune atmospheric parameters to test the Random Forest models:")
        base_city = st.session_state.current_city
        base_stats = resolve_city_climate(base_city)

        sim_temp = st.slider("Mean Temp (°C)", -5.0, 48.0, float(base_stats["temp_avg"]), step=0.5)
        sim_humidity = st.slider("Humidity (%)", 10.0, 100.0, float(base_stats["humidity"]), step=1.0)
        sim_pressure = st.slider("Pressure (hPa)", 980.0, 1035.0, float(base_stats["pressure"]), step=0.5)
        sim_wind = st.slider("Wind (km/h)", 1.0, 60.0, float(base_stats["wind_speed"]), step=0.5)

        if st.button("🚀 Run Simulator Inference", width="stretch"):
            st.session_state.pending_query = (
                f"Simulate weather for {base_city}: "
                f"Temp={sim_temp}°C, Humidity={sim_humidity}%, Pressure={sim_pressure}hPa, Wind={sim_wind}km/h"
            )
            st.rerun()

    # Model Performance & Metrics
    with st.expander("📈 Model Performance", expanded=False):
        m = predictor.metrics
        t_reg = m.get("temperature_regression", {})
        r_clf = m.get("rain_classification", {})

        st.write(f"• **Temperature $R^2$:** `{t_reg.get('r2_score', 0.98):.3f}`")
        st.write(f"• **Temperature MAE:** `{t_reg.get('mae', 0.96):.2f} °C`")
        st.write(f"• **Rain Accuracy:** `{r_clf.get('accuracy', 0.73) * 100:.1f}%`")
        st.write(f"• **Rain ROC-AUC:** `{r_clf.get('roc_auc', 0.78):.3f}`")

        if st.button("🔄 Retrain Models", width="stretch"):
            with st.spinner("Retraining Random Forest models..."):
                train_and_evaluate()
                st.cache_resource.clear()
                st.success("Retrained successfully!")
                st.rerun()


# -----------------------------------------------------------------------------
# 6. Main Chat Area
# -----------------------------------------------------------------------------
st.markdown("### ☁️ WeatherGPT")
st.caption(f"Currently viewing: **{st.session_state.current_city}** • Pure Supervised ML (No Live API)")

# Display conversation messages
st.markdown('<div class="chat-scroll-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    html_card = render_chat_bubble_html(
        role=msg["role"],
        content=msg["content"],
        tag=msg.get("tag", "Forecast"),
        timestamp=msg.get("timestamp", "")
    )
    st.markdown(html_card, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. Bottom Input Bar & Send Button
# -----------------------------------------------------------------------------
with st.container():
    with st.form("chat_form", clear_on_submit=True):
        col_text, col_submit = st.columns([5, 1], vertical_alignment="bottom")
        with col_text:
            user_input = st.text_input(
                "chat_box",
                placeholder="e.g. 'Will it rain tomorrow?' or 'How humid is it?'",
                label_visibility="collapsed"
            )
        with col_submit:
            send_clicked = st.form_submit_button("Send ➤", width="stretch", type="primary")

        if send_clicked and user_input.strip():
            process_user_query(user_input.strip())
            st.rerun()


# -----------------------------------------------------------------------------
# 8. Quick Question Prompt Buttons
# -----------------------------------------------------------------------------
st.markdown("**💡 Try asking:**")

t_row1_col1, t_row1_col2, t_row1_col3, t_row1_col4 = st.columns(4)
with t_row1_col1:
    if st.button("What is the temperature?", width="stretch"):
        st.session_state.pending_query = f"What is the temperature in {st.session_state.current_city}?"
        st.rerun()
with t_row1_col2:
    if st.button("Will it rain today?", width="stretch"):
        st.session_state.pending_query = f"Will it rain today in {st.session_state.current_city}?"
        st.rerun()
with t_row1_col3:
    if st.button("Show the forecast", width="stretch"):
        st.session_state.pending_query = f"Show the weather forecast for {st.session_state.current_city}"
        st.rerun()
with t_row1_col4:
    if st.button("Any weather alerts?", width="stretch"):
        st.session_state.pending_query = f"Are there any rain or storm alerts for {st.session_state.current_city}?"
        st.rerun()

t_row2_col1, t_row2_col2, t_row2_col3, t_row2_col4 = st.columns(4)
with t_row2_col1:
    if st.button("How humid is it?", width="stretch"):
        st.session_state.pending_query = f"How humid is it in {st.session_state.current_city}?"
        st.rerun()
with t_row2_col2:
    if st.button("What is the wind speed?", width="stretch"):
        st.session_state.pending_query = f"What is the wind speed in {st.session_state.current_city}?"
        st.rerun()
with t_row2_col3:
    if st.button("Show model metrics", width="stretch"):
        st.session_state.pending_query = "What is the accuracy and evaluation metric of this model?"
        st.rerun()
with t_row2_col4:
    if st.button("How it works without API?", width="stretch"):
        st.session_state.pending_query = "How does this weather chatbot work without a weather API?"
        st.rerun()
