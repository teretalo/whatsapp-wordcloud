"""Words Analysis Page - WordCloud"""
import streamlit as st
import matplotlib.pyplot as plt
from utils import create_wordcloud, get_available_years

st.set_page_config(page_title="Word Analysis", page_icon="📝", layout="wide")

st.title("📝 Word Cloud Analysis")
st.markdown("Explore the most frequently used words in your conversations.")

# Check if chat is uploaded
if not st.session_state.get('chat_uploaded', False):
    st.warning("⚠️ No chat data loaded. Please upload a chat file on the Home page first.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Get data from session state
all_messages = st.session_state.all_messages
messages_by_year = st.session_state.messages_by_year

# Sidebar controls
st.sidebar.header("🎨 Customization")

language = st.sidebar.selectbox(
    "Language",
    options=["English", "Italian", "Spanish"],
    index=["English", "Italian", "Spanish"].index(st.session_state.language)
)
st.session_state.language = language

available_years = get_available_years(messages_by_year)
year_options = ["All"] + [str(year) for year in available_years]
selected_year = st.sidebar.selectbox(
    "Filter by Year",
    options=year_options,
    index=year_options.index(st.session_state.selected_year) if st.session_state.selected_year in year_options else 0
)
st.session_state.selected_year = selected_year

# Size options
size_option = st.sidebar.radio(
    "Cloud Size",
    options=["Standard", "Large", "Extra Large"],
    index=1
)

size_map = {
    "Standard": (800, 400),
    "Large": (1200, 600),
    "Extra Large": (1600, 800)
}

# Filter messages by year
if selected_year == "All":
    messages_to_process = ' '.join(all_messages)
    display_year = "all years"
    message_count = len(all_messages)
else:
    year_int = int(selected_year)
    messages_to_process = ' '.join(messages_by_year[year_int])
    display_year = selected_year
    message_count = len(messages_by_year[year_int])

# Generate and display wordcloud
if messages_to_process.strip():
    # Stats
    word_count = len(messages_to_process.split())
    unique_words = len(set(messages_to_process.lower().split()))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Words", f"{word_count:,}")
    with col2:
        st.metric("Unique Words", f"{unique_words:,}")
    with col3:
        st.metric("Messages", f"{message_count:,}")

    st.divider()

    # Generate wordcloud
    st.subheader(f"☁️ Word Cloud - {language} ({display_year})")

    with st.spinner("Generating word cloud..."):
        wordcloud = create_wordcloud(messages_to_process, language)
        st.session_state.wordcloud_image = wordcloud

        # Adjust figure size based on selected size
        width, height = size_map[size_option]
        figsize = (width/80, height/80)  # Convert pixels to inches (approx 80 dpi)

        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        plt.close()

    # Download button
    st.download_button(
        label="💾 Download Word Cloud",
        data=wordcloud.to_image().tobytes(),
        file_name=f"wordcloud_{language}_{display_year}.png",
        mime="image/png",
        help="Download the word cloud as a PNG image"
    )

    st.divider()

    # Word frequency analysis
    st.subheader("📊 Top Words Frequency")

    # Get word frequencies from wordcloud
    word_freq = wordcloud.words_

    if word_freq:
        # Show top 20 words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        col1, col2 = st.columns([2, 1])

        with col1:
            # Bar chart
            words = [w[0] for w in top_words]
            freqs = [w[1] for w in top_words]

            fig, ax = plt.subplots(figsize=(10, 8))
            bars = ax.barh(words, freqs, color='#2ecc71')
            ax.set_xlabel('Relative Frequency')
            ax.set_title('Top 20 Most Frequent Words')
            ax.grid(axis='x', alpha=0.3)

            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2,
                        f'{width:.3f}',
                        ha='left', va='center', fontsize=9)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col2:
            st.info("""
            **About Word Frequencies**

            The frequencies shown are relative scores that indicate how prominently each word appears in the cloud.

            Common filler words (stopwords) are filtered out based on the selected language.

            **Tips:**
            - Try different years to see how word usage evolved
            - Switch languages if your chat contains mixed languages
            - Larger cloud sizes show more detail
            """)

else:
    st.warning(f"No messages found for {display_year}")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
