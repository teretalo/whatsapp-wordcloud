"""Words Analysis Page - WordCloud"""
import streamlit as st
import matplotlib.pyplot as plt
from utils import create_wordcloud, get_available_years
from navigation import render_sidebar_navigation

st.set_page_config(page_title="Word Analysis", page_icon="📝", layout="wide")
render_sidebar_navigation()

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
speaker_timeline_data = st.session_state.speaker_timeline_data

st.divider()

# Filter controls in main content
col1, col2, col3 = st.columns(3)

with col1:
    language = st.selectbox(
        "Language",
        options=["English", "Italian", "Spanish"],
        index=["English", "Italian", "Spanish"].index(st.session_state.language)
    )
    st.session_state.language = language

with col2:
    available_years = get_available_years(messages_by_year)
    year_options = ["All"] + [str(year) for year in available_years]
    selected_year = st.selectbox(
        "Filter by Year",
        options=year_options,
        index=0
    )

with col3:
    # Get all speakers
    speakers = sorted(st.session_state.speakers.keys())
    speaker_options = ["All"] + speakers
    selected_speaker = st.selectbox(
        "Filter by Speaker",
        options=speaker_options,
        index=0
    )

st.divider()

# Filter messages by year and speaker
if selected_year == "All" and selected_speaker == "All":
    # All messages
    messages_to_process = ' '.join(all_messages)
    display_filter = "all conversations"
    message_count = len(all_messages)
elif selected_year == "All" and selected_speaker != "All":
    # Filter by speaker only
    speaker_messages = [msg for date, msg, wc in speaker_timeline_data[selected_speaker]]
    messages_to_process = ' '.join(speaker_messages)
    display_filter = f"{selected_speaker}'s messages"
    message_count = len(speaker_messages)
elif selected_year != "All" and selected_speaker == "All":
    # Filter by year only
    year_int = int(selected_year)
    messages_to_process = ' '.join(messages_by_year[year_int])
    display_filter = f"year {selected_year}"
    message_count = len(messages_by_year[year_int])
else:
    # Filter by both year and speaker
    year_int = int(selected_year)
    speaker_messages = [msg for date, msg, wc in speaker_timeline_data[selected_speaker] if date.year == year_int]
    messages_to_process = ' '.join(speaker_messages)
    display_filter = f"{selected_speaker}'s messages in {selected_year}"
    message_count = len(speaker_messages)

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
    st.subheader(f"☁️ Word Cloud - {language}")
    st.caption(f"Showing: {display_filter}")

    with st.spinner("Generating word cloud..."):
        wordcloud = create_wordcloud(messages_to_process, language)
        st.session_state.wordcloud_image = wordcloud

        # Fixed size for consistency
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        plt.close()

    st.caption("ℹ️ *Common words like articles, prepositions, and other filler words have been removed to highlight meaningful content.*")

    # Download button
    st.download_button(
        label="💾 Download Word Cloud",
        data=wordcloud.to_image().tobytes(),
        file_name=f"wordcloud_{language}_{display_filter.replace(' ', '_')}.png",
        mime="image/png",
        help="Download the word cloud as a PNG image"
    )

else:
    st.warning(f"No messages found for {display_filter}")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
