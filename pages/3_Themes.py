"""Themes Analysis Page - Topic Modeling"""
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
from utils import perform_topic_modeling, get_message_topics, aggregate_topics_by_time

st.set_page_config(page_title="Themes Analysis", page_icon="🏷️", layout="wide")

st.title("🏷️ Conversation Themes")
st.markdown("Discover main topics and themes in your conversations using topic modeling.")

# Check if chat is uploaded
if not st.session_state.get('chat_uploaded', False):
    st.warning("⚠️ No chat data loaded. Please upload a chat file on the Home page first.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Info box explaining topic modeling
st.info("""
**What is Topic Modeling?**

Topic modeling automatically discovers themes in your conversations by finding groups of words that frequently appear together.
Each topic represents a theme or subject you discuss. The analysis shows you:
- What topics you talk about most
- How these topics evolve over time
- Key words associated with each theme
""")

st.divider()

# Sidebar controls
st.sidebar.header("⚙️ Analysis Settings")

# Get available years and months from messages
messages_with_dates = st.session_state.get('messages_with_dates', [])

if not messages_with_dates:
    st.error("No messages with date information found. Please re-upload your chat file.")
    st.stop()

# Extract years from messages
years = sorted(set(msg['date'].year for msg in messages_with_dates), reverse=True)
year_options = ["All"] + [str(year) for year in years]

# Year selection
selected_year = st.sidebar.selectbox(
    "Select Year",
    options=year_options,
    help="Choose a specific year or 'All' to analyze all messages"
)

# Month selection (only show if specific year selected)
selected_month = "All"
if selected_year != "All":
    month_names = ["All", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    selected_month = st.sidebar.selectbox(
        "Select Month",
        options=month_names,
        help="Choose a specific month or 'All' for the entire year"
    )

# Filter messages based on selection
filtered_messages = messages_with_dates.copy()

if selected_year != "All":
    year_int = int(selected_year)
    filtered_messages = [msg for msg in filtered_messages if msg['date'].year == year_int]

    if selected_month != "All":
        month_int = month_names.index(selected_month)
        filtered_messages = [msg for msg in filtered_messages if msg['date'].month == month_int]

# Number of topics slider
num_topics = st.sidebar.slider(
    "Number of Topics",
    min_value=2,
    max_value=10,
    value=5,
    help="Choose how many themes to find. Fewer topics (3-5) give broader categories. More topics (7-10) find more specific themes."
)

# Language selector
language = st.sidebar.selectbox(
    "Language",
    options=["English", "Italian", "Spanish"],
    index=["English", "Italian", "Spanish"].index(st.session_state.get('language', 'English')),
    help="Select the language of your conversations for better stopword filtering"
)

st.sidebar.divider()

# Show filtered message count and warning
num_filtered = len(filtered_messages)
st.sidebar.metric("Messages in Selection", f"{num_filtered:,}")

if num_filtered > 10000:
    st.sidebar.warning("⚠️ Large dataset detected. Analysis may take a moment. Consider narrowing the timeframe.")
elif num_filtered < 100:
    st.sidebar.warning("⚠️ Small dataset detected. Results may not be meaningful. Try selecting a larger timeframe.")

# Analysis button
if st.sidebar.button("🔍 Run Topic Analysis", type="primary", use_container_width=True):
    if num_filtered < num_topics:
        st.error(f"Not enough messages ({num_filtered}) for {num_topics} topics. Please select fewer topics or a larger timeframe.")
    else:
        with st.spinner("Analyzing themes... this may take a moment"):
            # Extract message texts
            message_texts = [msg['text'] for msg in filtered_messages]

            # Perform topic modeling
            topics, model, vectorizer = perform_topic_modeling(
                message_texts,
                num_topics=num_topics,
                language=language
            )

            if not topics:
                st.error("Could not perform topic modeling. Please try a different selection or check your data.")
            else:
                # Get topic assignments for each message
                topic_assignments = get_message_topics(message_texts, model, vectorizer)

                # Store results in session state
                st.session_state.topics = topics
                st.session_state.topic_assignments = topic_assignments
                st.session_state.filtered_messages = filtered_messages
                st.session_state.analysis_params = {
                    'year': selected_year,
                    'month': selected_month,
                    'num_topics': num_topics,
                    'language': language,
                    'num_messages': num_filtered
                }

                st.success("✅ Topic analysis complete!")

# Display results if available
if 'topics' in st.session_state and 'topic_assignments' in st.session_state:
    topics = st.session_state.topics
    topic_assignments = st.session_state.topic_assignments
    filtered_messages = st.session_state.filtered_messages
    params = st.session_state.analysis_params

    st.divider()

    # Header with analysis info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Timeframe", f"{params['year']} - {params['month']}")
    with col2:
        st.metric("Messages Analyzed", f"{params['num_messages']:,}")
    with col3:
        st.metric("Topics Found", params['num_topics'])
    with col4:
        st.metric("Language", params['language'])

    st.divider()

    # Calculate topic statistics
    topic_counts = pd.Series(topic_assignments).value_counts().sort_index()
    total_messages = len(topic_assignments)

    # Topic Distribution Chart
    st.subheader("📊 Topic Distribution")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(topic_counts)))

        labels = [f"Topic {i}" for i in topic_counts.index]
        sizes = topic_counts.values

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        ax.set_title('Distribution of Topics')
        st.pyplot(fig)
        plt.close()

    with col2:
        st.markdown("### 📈 Topic Summary")
        for topic_idx in topic_counts.index:
            count = topic_counts[topic_idx]
            percentage = (count / total_messages) * 100
            st.markdown(f"""
            **Topic {topic_idx}**
            {percentage:.1f}% • {count:,} messages
            """)

    st.divider()

    # Topic Cards Grid
    st.subheader("🗂️ Topic Details")

    cols = st.columns(2)

    for topic_idx, topic_words in enumerate(topics):
        with cols[topic_idx % 2]:
            with st.container():
                # Topic header
                count = topic_counts.get(topic_idx, 0)
                percentage = (count / total_messages) * 100 if total_messages > 0 else 0

                st.markdown(f"### Topic {topic_idx}")

                # Top words
                st.markdown("**Key Terms:**")
                # Show top 10 words as badges
                top_words = [word for word, weight in topic_words[:10]]
                keyword_badges = " • ".join([f"`{word}`" for word in top_words])
                st.markdown(keyword_badges)

                # Stats
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Messages", f"{count:,}")
                with col_b:
                    st.metric("Coverage", f"{percentage:.1f}%")

                # Word weights (expandable)
                with st.expander("View word weights"):
                    for word, weight in topic_words[:10]:
                        st.text(f"{word}: {weight:.4f}")

                st.divider()

    st.divider()

    # Topic Prevalence Over Time
    st.subheader("📅 Topic Trends Over Time")

    # Determine aggregation based on timeframe
    if params['month'] != "All":
        # Single month selected -> aggregate by day
        aggregation = 'day'
        time_label = "Day"
    elif params['year'] != "All":
        # Single year -> aggregate by fortnight
        aggregation = 'fortnight'
        time_label = "Period"
    else:
        # All years -> aggregate by month
        aggregation = 'month'
        time_label = "Month"

    # Prepare data for aggregation
    messages_with_topics = []
    for i, msg in enumerate(filtered_messages):
        if i < len(topic_assignments):
            messages_with_topics.append({
                'date': msg['date'],
                'topic': topic_assignments[i]
            })

    # Aggregate topics by time
    if messages_with_topics:
        topic_time_df = aggregate_topics_by_time(messages_with_topics, aggregation=aggregation)

        if not topic_time_df.empty:
            # Plot
            fig, ax = plt.subplots(figsize=(12, 6))

            # Get topic columns (all except 'period')
            topic_cols = [col for col in topic_time_df.columns if col != 'period']

            # Plot each topic
            colors = plt.cm.Set3(range(len(topic_cols)))
            for idx, topic_col in enumerate(topic_cols):
                ax.plot(
                    topic_time_df['period'],
                    topic_time_df[topic_col],
                    marker='o',
                    label=f'Topic {topic_col}',
                    linewidth=2,
                    markersize=5,
                    color=colors[idx]
                )

            ax.set_xlabel(time_label)
            ax.set_ylabel('Message Count')
            ax.set_title(f'Topic Activity Over Time (by {aggregation})')
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)

            # Rotate x-axis labels for readability
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            st.pyplot(fig)
            plt.close()
        else:
            st.info("Not enough data points for time-based visualization.")
    else:
        st.info("No topic assignments available for time-based analysis.")

    st.divider()

    # Export section
    st.subheader("💾 Export Results")

    col1, col2 = st.columns(2)

    with col1:
        # Prepare export data
        export_data = {
            'analysis_date': datetime.now().isoformat(),
            'parameters': params,
            'topics': [
                {
                    'topic_id': idx,
                    'top_words': [word for word, weight in topic_words[:10]],
                    'word_weights': {word: float(weight) for word, weight in topic_words[:10]},
                    'message_count': int(topic_counts.get(idx, 0)),
                    'percentage': float((topic_counts.get(idx, 0) / total_messages) * 100) if total_messages > 0 else 0
                }
                for idx, topic_words in enumerate(topics)
            ]
        }

        export_json = json.dumps(export_data, indent=2)

        st.download_button(
            label="📥 Download Topics (JSON)",
            data=export_json,
            file_name=f"whatsapp_topics_{params['year']}_{params['month']}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        # Prepare CSV export
        csv_data = []
        for idx, topic_words in enumerate(topics):
            count = topic_counts.get(idx, 0)
            percentage = (count / total_messages) * 100 if total_messages > 0 else 0
            top_words = ", ".join([word for word, weight in topic_words[:10]])
            csv_data.append({
                'Topic': f'Topic {idx}',
                'Message Count': count,
                'Percentage': f'{percentage:.1f}%',
                'Top Words': top_words
            })

        csv_df = pd.DataFrame(csv_data)
        csv_string = csv_df.to_csv(index=False)

        st.download_button(
            label="📥 Download Summary (CSV)",
            data=csv_string,
            file_name=f"whatsapp_topics_summary_{params['year']}_{params['month']}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    # Show instructions if no analysis has been run yet
    st.info("👈 Configure your analysis settings in the sidebar and click 'Run Topic Analysis' to begin.")
