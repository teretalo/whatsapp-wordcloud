"""WhatsApp Conversation WordCloud - Home Page"""
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO
from utils import parse_whatsapp_messages_with_years, get_available_years, create_wordcloud

# Page config
st.set_page_config(
    page_title="WhatsApp WordCloud",
    page_icon="💬",
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

        all_messages, messages_by_year, speakers = parse_whatsapp_messages_with_years(text_content)

        if all_messages:
            # Store in session state
            st.session_state.chat_uploaded = True
            st.session_state.all_messages = all_messages
            st.session_state.messages_by_year = messages_by_year
            st.session_state.speakers = speakers

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

# Dashboard Overview (placeholder charts)
if st.session_state.chat_uploaded:
    st.header("📊 Dashboard Overview")

    # Timeline placeholder
    st.subheader("Activity Timeline")
    fig, ax = plt.subplots(figsize=(12, 3))
    # Dummy data for timeline
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    activity = [45, 52, 38, 65, 70, 58, 62, 55, 48, 60, 68, 75]
    ax.plot(months, activity, marker='o', linewidth=2, markersize=6, color='#1f77b4')
    ax.fill_between(range(len(months)), activity, alpha=0.3, color='#1f77b4')
    ax.set_xlabel('Month')
    ax.set_ylabel('Messages')
    ax.set_title('Message Activity Over Time (placeholder)')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close()

    st.divider()

    # Preview cards section
    st.header("🔍 Explore Insights")

    col1, col2, col3 = st.columns(3)

    # Speakers preview card
    with col1:
        st.subheader("👥 Speakers")
        if st.session_state.speakers:
            # Show top 5 speakers
            top_speakers = sorted(st.session_state.speakers.items(), key=lambda x: x[1], reverse=True)[:5]
            speaker_names = [s[0] for s in top_speakers]
            speaker_counts = [s[1] for s in top_speakers]

            fig, ax = plt.subplots(figsize=(5, 3))
            ax.barh(speaker_names, speaker_counts, color='#ff7f0e')
            ax.set_xlabel('Messages')
            ax.set_title('Top 5 Speakers')
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        else:
            st.info("📊 Speaker activity chart will appear here")

        if st.button("View Details →", key="speakers_btn", use_container_width=True):
            st.switch_page("pages/1_Speakers.py")

    # Words preview card
    with col2:
        st.subheader("📝 Words")

        # Generate quick wordcloud preview
        if st.session_state.selected_year == "All":
            messages_text = ' '.join(st.session_state.all_messages)
        else:
            year_int = int(st.session_state.selected_year)
            messages_text = ' '.join(st.session_state.messages_by_year[year_int])

        if messages_text.strip():
            wordcloud = create_wordcloud(messages_text, st.session_state.language)
            st.session_state.wordcloud_image = wordcloud

            fig, ax = plt.subplots(figsize=(5, 3))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title('WordCloud Preview')
            st.pyplot(fig)
            plt.close()
        else:
            st.info("☁️ Word cloud will appear here")

        if st.button("View Full Cloud →", key="words_btn", use_container_width=True):
            st.switch_page("pages/2_Words.py")

    # Themes preview card
    with col3:
        st.subheader("🏷️ Themes")

        # Placeholder topics
        topics = ["Topic 1: Social", "Topic 2: Work", "Topic 3: Family", "Topic 4: Events"]

        st.markdown("**Discovered Topics:**")
        for topic in topics:
            st.markdown(f"• {topic}")

        st.caption("_Topic modeling coming soon_")

        if st.button("Explore Themes →", key="themes_btn", use_container_width=True):
            st.switch_page("pages/3_Themes.py")

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
