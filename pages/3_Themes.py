"""Themes Analysis Page - Topic Modeling"""
import streamlit as st
import matplotlib.pyplot as plt
import random

st.set_page_config(page_title="Themes Analysis", page_icon="🏷️", layout="wide")

st.title("🏷️ Conversation Themes")
st.markdown("Discover main topics and themes in your conversations.")

# Check if chat is uploaded
if not st.session_state.get('chat_uploaded', False):
    st.warning("⚠️ No chat data loaded. Please upload a chat file on the Home page first.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
    st.stop()

st.info("""
🚧 **Topic Modeling Feature - Coming Soon**

This page will use advanced NLP techniques to automatically identify and categorize conversation themes.
For now, we're showing placeholder data to demonstrate the planned layout and features.
""")

st.divider()

# Placeholder topics with dummy keywords
topics = [
    {
        "name": "Social Activities",
        "keywords": ["party", "dinner", "meet", "weekend", "fun", "movie", "restaurant"],
        "percentage": 28,
        "message_count": 342
    },
    {
        "name": "Work & Projects",
        "keywords": ["meeting", "project", "deadline", "task", "work", "email", "report"],
        "percentage": 22,
        "message_count": 268
    },
    {
        "name": "Family & Home",
        "keywords": ["home", "family", "kids", "mom", "dad", "house", "dinner"],
        "percentage": 18,
        "message_count": 219
    },
    {
        "name": "Travel & Events",
        "keywords": ["trip", "vacation", "travel", "flight", "hotel", "beach", "holiday"],
        "percentage": 15,
        "message_count": 183
    },
    {
        "name": "Hobbies & Interests",
        "keywords": ["game", "sport", "music", "book", "series", "watch", "play"],
        "percentage": 10,
        "message_count": 122
    },
    {
        "name": "Other Topics",
        "keywords": ["various", "miscellaneous"],
        "percentage": 7,
        "message_count": 85
    }
]

# Topic distribution chart
st.subheader("📊 Topic Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    # Pie chart
    names = [t["name"] for t in topics]
    percentages = [t["percentage"] for t in topics]

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.Pastel1(range(len(names)))
    wedges, texts, autotexts = ax.pie(
        percentages,
        labels=names,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)

    ax.set_title('Distribution of Conversation Topics (Placeholder)', fontsize=14)
    st.pyplot(fig)
    plt.close()

with col2:
    st.markdown("### 📈 Topic Summary")
    for topic in topics:
        st.markdown(f"""
        **{topic['name']}**
        {topic['percentage']}% • {topic['message_count']} messages
        """)

st.divider()

# Topic cards grid
st.subheader("🗂️ Topic Details")

# Create grid of topic cards
cols = st.columns(2)

for idx, topic in enumerate(topics):
    with cols[idx % 2]:
        with st.container():
            st.markdown(f"### {topic['name']}")

            # Keywords
            st.markdown("**Key Terms:**")
            keyword_badges = " • ".join([f"`{kw}`" for kw in topic['keywords'][:5]])
            st.markdown(keyword_badges)

            # Stats
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Messages", topic['message_count'])
            with col_b:
                st.metric("Coverage", f"{topic['percentage']}%")

            # Sample messages placeholder
            st.markdown("**Sample Messages:**")
            st.caption("_Sample messages will appear here once topic modeling is implemented_")

            st.divider()

# Timeline placeholder
st.subheader("📅 Topic Trends Over Time")

fig, ax = plt.subplots(figsize=(12, 6))

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Generate random trend lines for each topic
for topic in topics[:4]:  # Show top 4 topics
    random.seed(hash(topic['name']))
    trend = [random.randint(10, 50) for _ in months]
    ax.plot(months, trend, marker='o', label=topic['name'], linewidth=2, markersize=5)

ax.set_xlabel('Month')
ax.set_ylabel('Message Count')
ax.set_title('Topic Activity Over Time (Placeholder Data)')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

st.pyplot(fig)
plt.close()

st.divider()

# Future features section
st.subheader("🔮 Planned Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Topic Detection**
    - Automatic topic identification
    - Keyword extraction
    - Topic labeling
    - Subtopic clustering
    """)

with col2:
    st.markdown("""
    **Trend Analysis**
    - Topic evolution over time
    - Peak activity periods
    - Emerging topics
    - Declining themes
    """)

with col3:
    st.markdown("""
    **Advanced Insights**
    - Topic sentiment analysis
    - Speaker-topic associations
    - Topic transitions
    - Custom topic filters
    """)

st.info("""
💡 **Implementation Note:**
Topic modeling will use techniques like Latent Dirichlet Allocation (LDA) or BERTopic
to automatically discover themes in your conversations without predefined categories.
""")
