"""Speakers Analysis Page"""
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Speakers Analysis", page_icon="👥", layout="wide")

st.title("👥 Speaker Analysis")
st.markdown("Analyze speaker activity and contribution patterns in your WhatsApp conversations.")

# Check if chat is uploaded
if not st.session_state.get('chat_uploaded', False):
    st.warning("⚠️ No chat data loaded. Please upload a chat file on the Home page first.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Get data from session state
speakers = st.session_state.speakers
all_messages = st.session_state.all_messages

if speakers:
    # Stats overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Speakers", len(speakers))

    with col2:
        st.metric("Total Messages", len(all_messages))

    with col3:
        most_active = max(speakers.items(), key=lambda x: x[1])
        st.metric("Most Active", most_active[0])

    with col4:
        avg_msgs = len(all_messages) / len(speakers) if speakers else 0
        st.metric("Avg Messages/Speaker", f"{avg_msgs:.0f}")

    st.divider()

    # Top speakers chart
    st.subheader("📊 Top Speakers by Message Count")

    top_n = st.slider("Number of speakers to show", 5, min(20, len(speakers)), 10)

    top_speakers = sorted(speakers.items(), key=lambda x: x[1], reverse=True)[:top_n]
    speaker_names = [s[0] for s in top_speakers]
    speaker_counts = [s[1] for s in top_speakers]

    fig, ax = plt.subplots(figsize=(12, max(6, top_n * 0.4)))
    bars = ax.barh(speaker_names, speaker_counts, color='#ff7f0e')
    ax.set_xlabel('Number of Messages')
    ax.set_title(f'Top {top_n} Most Active Speakers')
    ax.grid(axis='x', alpha=0.3)

    # Add value labels on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f'{int(width)}',
                ha='left', va='center', fontsize=9, color='#333')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.divider()

    # Speaker statistics table
    st.subheader("📋 Speaker Statistics Table")

    # Create dataframe
    speaker_data = []
    total_messages = sum(speakers.values())

    for name, count in sorted(speakers.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_messages * 100) if total_messages > 0 else 0
        speaker_data.append({
            'Speaker': name,
            'Messages': count,
            'Percentage': f"{percentage:.1f}%"
        })

    df = pd.DataFrame(speaker_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Speaker": st.column_config.TextColumn("Speaker Name", width="medium"),
            "Messages": st.column_config.NumberColumn("Message Count", width="small"),
            "Percentage": st.column_config.TextColumn("% of Total", width="small"),
        }
    )

    st.divider()

    # Message distribution pie chart
    st.subheader("🥧 Message Distribution")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Show top 10 in pie, combine rest as "Others"
        top_10_speakers = sorted(speakers.items(), key=lambda x: x[1], reverse=True)[:10]

        if len(speakers) > 10:
            top_names = [s[0] for s in top_10_speakers]
            top_values = [s[1] for s in top_10_speakers]
            others_value = sum(v for k, v in speakers.items() if k not in top_names)

            pie_names = top_names + ['Others']
            pie_values = top_values + [others_value]
        else:
            pie_names = [s[0] for s in top_10_speakers]
            pie_values = [s[1] for s in top_10_speakers]

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(pie_names)))
        wedges, texts, autotexts = ax.pie(
            pie_values,
            labels=pie_names,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )

        # Make percentage text more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('Message Distribution by Speaker')
        st.pyplot(fig)
        plt.close()

    with col2:
        st.info("""
        **About This Page**

        This page shows speaker activity analysis based on message counts.

        **Future Features:**
        - Message timestamps analysis
        - Response time metrics
        - Conversation initiation patterns
        - Peak activity hours per speaker
        - Sentiment analysis per speaker
        """)

else:
    st.info("No speaker data available. Upload a chat file that includes speaker names.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
