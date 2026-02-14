"""WhatsApp Conversation WordCloud - Home Page"""
import streamlit as st
import plotly.graph_objects as go
from io import StringIO
from utils import parse_whatsapp_messages_with_years, get_available_years, create_wordcloud, aggregate_messages_by_time

# Page config
st.set_page_config(
    page_title="Home - WhatsApp WordCloud",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_uploaded' not in st.session_state:
    st.session_state.chat_uploaded = False
if 'all_messages' not in st.session_state:
    st.session_state.all_messages = []
if 'messages_by_year' not in st.session_state:
    st.session_state.messages_by_year = {}
if 'speakers' not in st.session_state:
    st.session_state.speakers = {}
if 'message_dates' not in st.session_state:
    st.session_state.message_dates = []
if 'language' not in st.session_state:
    st.session_state.language = "English"
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = "All"
if 'wordcloud_image' not in st.session_state:
    st.session_state.wordcloud_image = None

# Sidebar navigation
st.sidebar.title("💬 Navigation")
st.sidebar.info("Upload a WhatsApp chat to unlock all features")

# Main content
st.title("WhatsApp Conversation Analytics")
st.markdown("""
Welcome to WhatsApp WordCloud! Upload your WhatsApp chat export to explore insights about your conversations.
Generate word clouds, analyze speaker activity, and discover conversation themes.
""")

# File uploader section
st.header("📁 Upload Your Chat")
uploaded_file = st.file_uploader("Choose a WhatsApp conversation file (.txt)", type=['txt'])

if uploaded_file is not None:
    # Read and parse the file
    with st.spinner("Processing conversation..."):
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        text_content = stringio.read()

        all_messages, messages_by_year, speakers, message_dates = parse_whatsapp_messages_with_years(text_content)

        if all_messages:
            # Store in session state
            st.session_state.chat_uploaded = True
            st.session_state.all_messages = all_messages
            st.session_state.messages_by_year = messages_by_year
            st.session_state.speakers = speakers
            st.session_state.message_dates = message_dates

            st.success(f"✅ Chat loaded successfully! Found {len(all_messages)} messages from {len(speakers)} speakers.")
        else:
            st.error("Could not extract messages from the file. Please make sure it's a valid WhatsApp chat export.")

# Configuration section (only show if chat is uploaded)
if st.session_state.chat_uploaded:
    st.header("⚙️ Configuration")
    col1, col2 = st.columns(2)

    with col1:
        language = st.selectbox(
            "Select Language",
            options=["English", "Italian", "Spanish"],
            index=["English", "Italian", "Spanish"].index(st.session_state.language),
            key="language_selector"
        )
        st.session_state.language = language

    with col2:
        available_years = get_available_years(st.session_state.messages_by_year)
        year_options = ["All"] + [str(year) for year in available_years]
        selected_year = st.selectbox(
            "Select Year",
            options=year_options,
            index=year_options.index(st.session_state.selected_year) if st.session_state.selected_year in year_options else 0,
            key="year_selector"
        )
        st.session_state.selected_year = selected_year

# Dashboard Overview
if st.session_state.chat_uploaded:
    st.header("📊 Message Activity Timeline")

    # Generate timeline data
    if st.session_state.message_dates:
        dates, counts = aggregate_messages_by_time(st.session_state.message_dates)

        # Determine aggregation type for display
        sorted_dates = sorted(st.session_state.message_dates)
        duration = (sorted_dates[-1] - sorted_dates[0]).days
        aggregation_type = "Weekly" if duration < 365 else "Monthly"

        # Create interactive Plotly chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#667eea', width=2.5),
            fillcolor='rgba(102, 126, 234, 0.2)',
            hovertemplate='<b>%{x|%B %d, %Y}</b><br>Messages: %{y}<extra></extra>',
            name='Messages'
        ))

        fig.update_layout(
            title=dict(
                text=f'{aggregation_type} Message Activity',
                font=dict(size=20, color='#1f2937')
            ),
            xaxis=dict(
                title='Time',
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)',
                zeroline=False
            ),
            yaxis=dict(
                title='Number of Messages',
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)',
                zeroline=False
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            height=400,
            margin=dict(l=60, r=40, t=80, b=60)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", f"{len(st.session_state.all_messages):,}")
        with col2:
            st.metric("Peak Activity", f"{max(counts)} messages")
        with col3:
            avg_messages = sum(counts) / len(counts) if counts else 0
            st.metric("Average", f"{avg_messages:.1f} messages/{aggregation_type.lower()[:-2]}")

else:
    # Show help when no file is uploaded
    st.info("👆 Upload a WhatsApp chat export file to get started")

    with st.expander("ℹ️ How to export WhatsApp chats"):
        st.markdown("""
        **On iPhone:**
        1. Open the chat you want to export
        2. Tap the contact/group name at the top
        3. Scroll down and tap "Export Chat"
        4. Choose "Without Media"
        5. Save the .txt file

        **On Android:**
        1. Open the chat you want to export
        2. Tap the three dots (⋮) in the top right
        3. Select "More" → "Export chat"
        4. Choose "Without media"
        5. Save the .txt file
        """)
