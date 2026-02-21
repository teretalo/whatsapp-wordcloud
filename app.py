"""WhatsApp Conversation Analyzer - Home Page"""
import json
import streamlit as st
import plotly.graph_objects as go
from io import StringIO
from collections import defaultdict, Counter
from datetime import datetime, timezone
from utils import parse_whatsapp_messages_with_years, parse_whatsapp_messages_with_dates, get_available_years, create_wordcloud, aggregate_messages_by_time

# Page config
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏠 Home")

__name__ = "🏠 Home"

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
if 'messages_with_dates' not in st.session_state:
    st.session_state.messages_with_dates = []
if 'speaker_timeline_data' not in st.session_state:
    st.session_state.speaker_timeline_data = {}
if 'speaker_message_types' not in st.session_state:
    st.session_state.speaker_message_types = {}
if 'speaker_emojis' not in st.session_state:
    st.session_state.speaker_emojis = {}
if 'speaker_initiations' not in st.session_state:
    st.session_state.speaker_initiations = {}
if 'initiation_timeline_data' not in st.session_state:
    st.session_state.initiation_timeline_data = {}
if 'speaker_colors' not in st.session_state:
    st.session_state.speaker_colors = {}
if 'language' not in st.session_state:
    st.session_state.language = "English"
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = "All"
if 'wordcloud_image' not in st.session_state:
    st.session_state.wordcloud_image = None
if 'sentiment_results' not in st.session_state:
    st.session_state.sentiment_results = None


def build_highlights_json():
    """Build a shareable summary payload for external analysis."""
    all_messages = st.session_state.get("all_messages", [])
    speakers = st.session_state.get("speakers", {})
    message_dates = st.session_state.get("message_dates", [])
    messages_with_dates = st.session_state.get("messages_with_dates", [])
    speaker_emojis = st.session_state.get("speaker_emojis", {})
    sentiment_results = st.session_state.get("sentiment_results")
    uploaded_filename = st.session_state.get("uploaded_filename", "unknown_file")

    top_speakers = sorted(speakers.items(), key=lambda item: item[1], reverse=True)[:5]
    top_speaker_payload = [
        {"speaker": speaker, "messages": int(count)}
        for speaker, count in top_speakers
    ]

    date_values = []
    if messages_with_dates:
        date_values = sorted(msg["date"] for msg in messages_with_dates)
    elif message_dates:
        date_values = sorted(message_dates)

    if date_values:
        date_range = {
            "start": date_values[0].strftime("%Y-%m-%d"),
            "end": date_values[-1].strftime("%Y-%m-%d"),
        }
    else:
        date_range = {"start": None, "end": None}

    activity_summary = {
        "aggregation": None,
        "peak_period_start": None,
        "peak_messages": 0,
        "average_messages_per_period": 0.0,
    }
    if message_dates:
        timeline_dates, timeline_counts = aggregate_messages_by_time(message_dates)
        if timeline_dates and timeline_counts:
            sorted_dates = sorted(message_dates)
            duration_days = (sorted_dates[-1] - sorted_dates[0]).days
            aggregation = "weekly" if duration_days < 365 else "monthly"
            peak_index = timeline_counts.index(max(timeline_counts))

            activity_summary = {
                "aggregation": aggregation,
                "peak_period_start": timeline_dates[peak_index].strftime("%Y-%m-%d"),
                "peak_messages": int(timeline_counts[peak_index]),
                "average_messages_per_period": round(sum(timeline_counts) / len(timeline_counts), 2),
            }

    emoji_counter = Counter()
    for emoji_list in speaker_emojis.values():
        emoji_counter.update(emoji_list)
    top_emojis_payload = [
        {"emoji": emoji, "count": int(count)}
        for emoji, count in emoji_counter.most_common(10)
    ]

    emotion_summary = {
        "available": False,
        "language": None,
        "top_emotions": [],
        "top_dominant_emotions": [],
    }
    if sentiment_results and sentiment_results.get("messages"):
        messages = sentiment_results["messages"]
        emotion_totals = defaultdict(float)
        dominant_counter = Counter()

        for msg in messages:
            for key, value in msg.items():
                if key.startswith("score_"):
                    emotion_totals[key.replace("score_", "")] += float(value)
            dominant = msg.get("dominant_emotion")
            if dominant:
                dominant_counter[dominant] += 1

        total_emotion_score = sum(emotion_totals.values())
        top_emotions = sorted(emotion_totals.items(), key=lambda item: item[1], reverse=True)[:6]

        emotion_summary = {
            "available": True,
            "language": sentiment_results.get("language"),
            "top_emotions": [
                {
                    "emotion": emotion,
                    "share_pct": round((value / total_emotion_score * 100), 2) if total_emotion_score else 0.0,
                }
                for emotion, value in top_emotions
            ],
            "top_dominant_emotions": [
                {"emotion": emotion, "messages": int(count)}
                for emotion, count in dominant_counter.most_common(6)
            ],
        }

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "app": "WhatsApp Conversation Analyzer",
            "uploaded_file": uploaded_filename,
        },
        "privacy_context": {
            "deployment": "google_cloud_run",
            "storage_policy": "application_does_not_intentionally_persist_chat_content; runtime_memory_and_platform_logs_may_exist",
            "sharing_policy": "application_code_makes_no_outbound_llm_or_third_party_data_sharing_calls",
            "operator_access_note": "privileged_cloud_or_service_operators_may_access_runtime_or_logs",
        },
        "highlights": {
            "total_messages": int(len(all_messages)),
            "total_speakers": int(len(speakers)),
            "date_range": date_range,
            "top_speakers": top_speaker_payload,
            "activity_summary": activity_summary,
            "top_emojis": top_emojis_payload,
            "emotion_summary": emotion_summary,
        },
        "llm_instructions": {
            "goal": "Use this summary to produce deeper conversation insights.",
            "required_output": [
                "1) Short plain-language summary of communication patterns.",
                "2) Key behavior changes over time with likely triggers.",
                "3) Speaker-level relationship dynamics and possible tensions.",
                "4) Actionable recommendations for healthier communication.",
                "5) Confidence notes and assumptions.",
            ],
            "if_more_data_needed": [
                "Ask for the full Emotion Results CSV exported from this app.",
                "Ask for timeline screenshots for months with unusual emotion spikes.",
                "Ask for a longer date range or more chats only if user explicitly agrees.",
            ],
            "privacy_rule_for_llm": "Do not request personal identifiers unless strictly necessary.",
        },
    }

# Main content
st.title("WhatsApp Conversation Analyzer")
st.markdown("""
Welcome to WhatsApp Analyzer! Upload your WhatsApp chat to discover new insights about your conversations.
Generate word clouds, analyze speaker activity, and explore rich emotion trends.
""")

st.divider()

# Export instructions BEFORE uploader - more prominent
st.warning("⚠️ **Not sure how to upload your chat?** Learn how to export it from WhatsApp and upload it here.✨")

with st.expander("📱 How to export WhatsApp chats - Click here!", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **On iPhone:**
        1. Open the chat you want to export
        2. Tap the contact/group name at the top
        3. Scroll down and tap "Export Chat"
        4. Choose "Without Media"
        5. Save the .txt file
        """)

    with col2:
        st.markdown("""
        **On Android:**
        1. Open the chat you want to export
        2. Tap the three dots (⋮) in the top right
        3. Select "More" → "Export chat"
        4. Choose "Without media"
        5. Save the .txt file
        """)

st.divider()

# File uploader section
st.header("📁 Upload Your Chat")
uploaded_file = st.file_uploader("Choose a WhatsApp conversation file (.txt)", type=['txt'])

# Initialize uploaded_filename in session state
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = None

if uploaded_file is not None:
    # Only process if it's a new file (or first upload)
    if st.session_state.uploaded_filename != uploaded_file.name:
        # Read and parse the file
        with st.spinner("Processing conversation..."):
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            text_content = stringio.read()

            all_messages, messages_by_year, speakers, message_dates, speaker_timeline_data, speaker_message_types, speaker_emojis, speaker_initiations, initiation_timeline_data = parse_whatsapp_messages_with_years(text_content)

            # Also parse with dates for emotion timeline analysis
            messages_with_dates, _, _, _ = parse_whatsapp_messages_with_dates(text_content)

            if all_messages:
                # Create consistent color mapping for all speakers (alphabetically sorted)
                color_palette = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a',
                                '#fee140', '#30cfd0', '#a8edea', '#fed6e3', '#c471ed']
                sorted_speakers = sorted(speakers.keys())
                speaker_colors = {speaker: color_palette[idx % len(color_palette)]
                                 for idx, speaker in enumerate(sorted_speakers)}

                # Store in session state
                st.session_state.chat_uploaded = True
                st.session_state.all_messages = all_messages
                st.session_state.messages_by_year = messages_by_year
                st.session_state.speakers = speakers
                st.session_state.message_dates = message_dates
                st.session_state.messages_with_dates = messages_with_dates
                st.session_state.speaker_timeline_data = speaker_timeline_data
                st.session_state.speaker_message_types = speaker_message_types
                st.session_state.speaker_emojis = speaker_emojis
                st.session_state.speaker_initiations = speaker_initiations
                st.session_state.initiation_timeline_data = initiation_timeline_data
                st.session_state.speaker_colors = speaker_colors
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.pending_merges = []  # Reset pending merges for new file
                st.session_state.sentiment_results = None

                st.success(f"✅ Chat loaded successfully! Found {len(all_messages)} messages from {len(speakers)} people.")
            else:
                st.error("Could not extract messages from the file. Please make sure it's a valid WhatsApp chat export.")

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

        # Set hover format based on aggregation type
        if aggregation_type == "Weekly":
            hover_format = '<b>Week of %{x|%B %d, %Y}</b><br>Messages: %{y}<extra></extra>'
        else:
            hover_format = '<b>%{x|%B %Y}</b><br>Messages: %{y}<extra></extra>'

        # Create interactive Plotly chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#667eea', width=2.5),
            fillcolor='rgba(102, 126, 234, 0.2)',
            hovertemplate=hover_format,
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

    # People management section
    st.divider()

    speakers = st.session_state.speakers
    num_people = len(speakers)
    speaker_list = sorted(speakers.keys())

    # Initialize pending merges in session state if not exists
    if 'pending_merges' not in st.session_state:
        st.session_state.pending_merges = []

    # Calculate how many people after merges
    people_in_merges = set()
    for merge in st.session_state.pending_merges:
        people_in_merges.update(merge['old_names'])

    num_people_after = num_people - len(people_in_merges) + len(st.session_state.pending_merges)

    # Show count with arrow if there are pending merges
    if st.session_state.pending_merges:
        st.subheader(f"👥 People Found: {num_people} → {num_people_after} after merges")
    else:
        st.subheader(f"👥 People Found: {num_people}")

    # Show all people names
    st.write("**People in this conversation:**")
    st.write(", ".join(speaker_list))

    # Merge people section - in an expander since it's not always needed
    with st.expander("🔄 Merge duplicate people (optional)", expanded=False):
        st.markdown("""
        If the same person appears with different names (e.g., "Paolo IT" and "Paolo UK"),
        you can merge them here. This will combine their message counts and data.
        """)

        st.markdown("#### Create a new merge")

        # Show checkboxes for all people
        available_people = [p for p in speaker_list if not any(p in merge['old_names'] for merge in st.session_state.pending_merges)]

        if not available_people:
            st.info("✅ All people have been assigned to merge groups!")
        else:
            selected_people = []
            cols = st.columns(min(3, len(available_people)))

            for idx, person in enumerate(available_people):
                with cols[idx % 3]:
                    if st.checkbox(person, key=f"person_{person}"):
                        selected_people.append(person)

            if selected_people:
                st.markdown("**Selected people to merge:**")
                st.write(", ".join(selected_people))

                new_name = st.text_input(
                    "New name for this person:",
                    value=selected_people[0] if len(selected_people) == 1 else "",
                    placeholder="Enter the merged name",
                    key="new_merge_name"
                )

                if st.button("➕ Add this merge", key="add_merge"):
                    if len(selected_people) >= 2:
                        if new_name:
                            st.session_state.pending_merges.append({
                                'old_names': selected_people,
                                'new_name': new_name
                            })
                            st.rerun()
                        else:
                            st.error("Please provide a name for the merged person.")
                    else:
                        st.warning("Select at least 2 people to create a merge.")

        # Show pending merges
        if st.session_state.pending_merges:
            st.markdown("---")
            st.markdown("#### Pending Merges")

            for idx, merge in enumerate(st.session_state.pending_merges):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.info(f"**{', '.join(merge['old_names'])}** → **{merge['new_name']}**")
                with col2:
                    if st.button("❌", key=f"remove_{idx}", help="Remove this merge"):
                        st.session_state.pending_merges.pop(idx)
                        st.rerun()

            st.markdown("---")

            # Apply all merges button
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("✅ Apply All Merges", type="primary", use_container_width=True):
                    # Apply all merges
                    for merge in st.session_state.pending_merges:
                        old_names = merge['old_names']
                        new_name = merge['new_name']

                        # Merge speaker counts
                        merged_count = sum(st.session_state.speakers.get(name, 0) for name in old_names)

                        # Remove old speakers
                        for name in old_names:
                            if name in st.session_state.speakers:
                                del st.session_state.speakers[name]

                        # Add merged speaker
                        st.session_state.speakers[new_name] = merged_count

                        # Merge speaker_timeline_data
                        merged_timeline = []
                        for name in old_names:
                            if name in st.session_state.speaker_timeline_data:
                                merged_timeline.extend(st.session_state.speaker_timeline_data[name])
                                del st.session_state.speaker_timeline_data[name]

                        st.session_state.speaker_timeline_data[new_name] = sorted(merged_timeline, key=lambda x: x[0])

                        # Merge speaker_message_types
                        merged_message_types = defaultdict(int)
                        for name in old_names:
                            if name in st.session_state.speaker_message_types:
                                for msg_type, count in st.session_state.speaker_message_types[name].items():
                                    merged_message_types[msg_type] += count
                                del st.session_state.speaker_message_types[name]

                        st.session_state.speaker_message_types[new_name] = dict(merged_message_types)

                        # Merge speaker_emojis
                        merged_emojis = []
                        for name in old_names:
                            if name in st.session_state.speaker_emojis:
                                merged_emojis.extend(st.session_state.speaker_emojis[name])
                                del st.session_state.speaker_emojis[name]

                        st.session_state.speaker_emojis[new_name] = merged_emojis

                        # Merge speaker_initiations
                        merged_initiations = sum(st.session_state.speaker_initiations.get(name, 0) for name in old_names)
                        for name in old_names:
                            if name in st.session_state.speaker_initiations:
                                del st.session_state.speaker_initiations[name]

                        st.session_state.speaker_initiations[new_name] = merged_initiations

                        # Merge initiation_timeline_data
                        merged_init_timeline = []
                        for name in old_names:
                            if name in st.session_state.initiation_timeline_data:
                                merged_init_timeline.extend(st.session_state.initiation_timeline_data[name])
                                del st.session_state.initiation_timeline_data[name]

                        st.session_state.initiation_timeline_data[new_name] = sorted(merged_init_timeline)

                        # Update color mapping (use color of first old name)
                        if old_names and old_names[0] in st.session_state.speaker_colors:
                            st.session_state.speaker_colors[new_name] = st.session_state.speaker_colors[old_names[0]]

                        for name in old_names:
                            if name in st.session_state.speaker_colors:
                                del st.session_state.speaker_colors[name]

                    # Clear pending merges
                    num_merges = len(st.session_state.pending_merges)
                    st.session_state.pending_merges = []

                    st.success(f"✅ Successfully applied {num_merges} merge(s)!")
                    st.rerun()

            with col2:
                if st.button("🗑️ Clear All", use_container_width=True):
                    st.session_state.pending_merges = []
                    st.rerun()

else:
    # Show helpful message when no file is uploaded
    st.info("👆 Upload a WhatsApp chat export file above to get started and see your conversation timeline!")

st.divider()

# Data privacy and safe export section
st.header("🔐 Data Privacy")
st.markdown("""
This app is deployed on **Google Cloud Run**.

In simple terms:
- Your chat is processed in app memory while you use the session.
- The app code does **not intentionally store** chat text in a database or file.
- The app code does **not send** chat content to LLM APIs or other third-party analysis services.
- Cloud/runtime memory and operational logs may still exist as part of normal infrastructure behavior.
- People with privileged cloud/service admin access could access runtime data or logs.

If your policy requires strict controls, avoid uploading highly sensitive or regulated data.
""")

if st.session_state.chat_uploaded:
    highlights_payload = build_highlights_json()
    highlights_json = json.dumps(highlights_payload, indent=2, ensure_ascii=False)

    st.download_button(
        label="📥 Download Analysis Highlights (JSON for LLM)",
        data=highlights_json,
        file_name=f"analysis_highlights_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        help="Share this summary with an LLM for deeper analysis without sharing the full chat export.",
    )
else:
    st.caption("Upload a chat to enable the highlights JSON export.")
