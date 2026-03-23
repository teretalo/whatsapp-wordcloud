"""Emotion Analysis Page - Dictionary Based."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import extract_emojis
from navigation import render_sidebar_navigation

st.set_page_config(page_title="Emotion Analysis", page_icon="😊", layout="wide")
render_sidebar_navigation()

st.title("😊 Emotion Analysis (Dictionary)")
st.markdown("Fast dictionary-based emotion insights by speaker and over time.")

if not st.session_state.get("chat_uploaded", False):
    st.warning("⚠️ No chat data loaded. Please upload a chat file on the Home page first.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
    st.stop()

messages_with_dates = st.session_state.get("messages_with_dates", [])
if not messages_with_dates:
    st.error("No message timeline data found. Please re-upload your chat file.")
    st.stop()

EMOTIONS = ["joy", "love", "trust", "surprise", "anger", "sadness", "fear", "disgust"]
EMOTION_COLORS = {
    "joy": "#43e97b",
    "love": "#ec4899",
    "trust": "#14b8a6",
    "surprise": "#f59e0b",
    "anger": "#ef4444",
    "sadness": "#3b82f6",
    "fear": "#7c3aed",
    "disgust": "#84cc16",
}

# Compact multilingual lexicons inspired by NRC-style categories.
LANGUAGE_RULES = {
    "English": {
        "lexicon": {
            "joy": {
                "happy", "joy", "glad", "great", "awesome", "amazing", "fun", "smile", "yay", "win",
                "delight", "cheerful", "excited", "celebrate", "laugh",
            },
            "love": {
                "love", "adore", "dear", "darling", "sweet", "kiss", "heart", "beloved", "romantic",
                "affection", "hug", "beautiful", "caring",
            },
            "trust": {
                "trust", "safe", "secure", "reliable", "honest", "faith", "confident", "sure",
                "dependable", "promise", "support", "stable",
            },
            "surprise": {
                "surprised", "wow", "unexpected", "suddenly", "shock", "astonished", "unbelievable",
                "omg", "whoa", "incredible", "amazed",
            },
            "anger": {
                "angry", "mad", "furious", "annoyed", "hate", "rage", "irritated", "upset", "damn",
                "stupid", "ridiculous", "frustrated",
            },
            "sadness": {
                "sad", "cry", "tears", "depressed", "hurt", "sorry", "alone", "miss", "unhappy",
                "heartbroken", "pain", "grief", "down",
            },
            "fear": {
                "afraid", "scared", "fear", "anxious", "worry", "panic", "terrified", "nervous",
                "danger", "risky", "uncertain", "stress",
            },
            "disgust": {
                "disgusting", "gross", "nasty", "awful", "sick", "horrible", "yuck", "repulsive",
                "filthy", "dirty", "ugh",
            },
        },
        "negations": {"not", "never", "no", "none", "nothing", "nobody", "cant", "cannot", "dont", "didnt"},
        "boosters": {"very", "really", "so", "super", "extremely", "totally", "absolutely"},
        "downtoners": {"slightly", "somewhat", "kinda", "kindof", "little", "bit", "maybe"},
    },
    "Italian": {
        "lexicon": {
            "joy": {
                "felice", "gioia", "contento", "evviva", "grande", "ottimo", "fantastico", "sorriso",
                "divertente", "festa", "ridere", "bello", "wow",
            },
            "love": {
                "amore", "adoro", "tesoro", "caro", "dolce", "bacio", "cuore", "affetto", "romantico",
                "abbraccio", "bellissima", "amato",
            },
            "trust": {
                "fiducia", "sicuro", "affidabile", "onesto", "certo", "tranquillo", "promessa",
                "supporto", "stabile", "sereno", "protezione",
            },
            "surprise": {
                "sorpresa", "inaspettato", "improvviso", "shock", "incredibile", "pazzesco", "wow",
                "davvero", "accidenti", "stupefatto",
            },
            "anger": {
                "arrabbiato", "rabbia", "furioso", "odio", "nervoso", "fastidio", "irritato", "stupido",
                "assurdo", "incazzato", "deluso",
            },
            "sadness": {
                "triste", "piango", "lacrime", "male", "solo", "mancanza", "dolore", "dispiace",
                "cuore spezzato", "abbattuto", "giu",
            },
            "fear": {
                "paura", "spaventato", "ansia", "preoccupato", "panico", "terrorizzato", "rischio",
                "incerto", "stress", "nervosismo",
            },
            "disgust": {
                "schifo", "disgustoso", "orribile", "nausea", "sporco", "puzza", "bleah", "che schifo",
                "ripugnante", "vomito",
            },
        },
        "negations": {"non", "mai", "nessuno", "niente", "nulla", "senza", "nemmeno", "neanche"},
        "boosters": {"molto", "davvero", "super", "estremamente", "assolutamente", "troppo"},
        "downtoners": {"poco", "forse", "quasi", "leggermente", "abbastanza", "po"},
    },
    "Spanish": {
        "lexicon": {
            "joy": {
                "feliz", "alegre", "genial", "excelente", "fantastico", "sonrisa", "fiesta", "reir",
                "divertido", "maravilloso", "bravo", "wow", "bien",
            },
            "love": {
                "amor", "adoro", "querido", "cariño", "dulce", "beso", "corazon", "afecto", "romantico",
                "abrazo", "precioso", "te amo",
            },
            "trust": {
                "confianza", "seguro", "fiable", "honesto", "cierto", "tranquilo", "promesa", "apoyo",
                "estable", "protegido", "calma",
            },
            "surprise": {
                "sorpresa", "inesperado", "de repente", "shock", "increible", "wow", "asombrado",
                "impactante", "no puede ser",
            },
            "anger": {
                "enojado", "rabia", "furioso", "odio", "molesto", "irritado", "tonto", "ridiculo",
                "frustrado", "cabreado",
            },
            "sadness": {
                "triste", "llorar", "lagrimas", "solo", "dolor", "lo siento", "deprimido", "mal",
                "desanimado", "corazon roto",
            },
            "fear": {
                "miedo", "asustado", "ansiedad", "preocupado", "panico", "riesgo", "incierto",
                "nervioso", "estres", "peligro",
            },
            "disgust": {
                "asco", "disgusto", "horrible", "nausea", "sucio", "repugnante", "guacala", "que asco",
                "vomito", "apestoso",
            },
        },
        "negations": {"no", "nunca", "jamas", "nadie", "nada", "ninguno", "ninguna", "sin", "tampoco"},
        "boosters": {"muy", "realmente", "super", "extremadamente", "absolutamente", "totalmente"},
        "downtoners": {"poco", "quizas", "casi", "algo", "medio"},
    },
}

EMOJI_EMOTION_MAP = {
    "😀": {"joy": 1.0}, "😃": {"joy": 1.0}, "😄": {"joy": 1.0}, "😁": {"joy": 1.0},
    "😊": {"joy": 0.8, "trust": 0.2}, "🙂": {"joy": 0.5}, "😂": {"joy": 1.0}, "🤣": {"joy": 1.0},
    "😍": {"love": 1.0, "joy": 0.4}, "🥰": {"love": 1.0, "joy": 0.4}, "😘": {"love": 0.8},
    "❤️": {"love": 1.0}, "💕": {"love": 1.0}, "💚": {"love": 0.7, "trust": 0.3}, "💙": {"trust": 0.6},
    "🙏": {"trust": 0.6, "love": 0.2}, "👍": {"trust": 0.6, "joy": 0.2}, "🎉": {"joy": 0.8, "surprise": 0.2},
    "😮": {"surprise": 1.0}, "😲": {"surprise": 1.0}, "😱": {"fear": 0.8, "surprise": 0.6},
    "😡": {"anger": 1.0}, "🤬": {"anger": 1.0}, "😠": {"anger": 0.9}, "👎": {"anger": 0.5, "disgust": 0.4},
    "😢": {"sadness": 0.8}, "😭": {"sadness": 1.0}, "😔": {"sadness": 0.7}, "💔": {"sadness": 0.8, "anger": 0.2},
    "😨": {"fear": 0.9}, "😰": {"fear": 0.8}, "😩": {"fear": 0.4, "sadness": 0.4},
    "🤢": {"disgust": 1.0}, "🤮": {"disgust": 1.0}, "😖": {"disgust": 0.5, "sadness": 0.3},
}

TOKEN_PATTERN = re.compile(r"[^\W\d_]+", flags=re.UNICODE)


def tokenize_text(text):
    """Tokenize unicode words and drop numbers/punctuation."""
    return TOKEN_PATTERN.findall(text.lower())


def build_complete_timeline(sorted_dates):
    """Build a complete weekly/monthly timeline from first to last date."""
    duration_days = (sorted_dates[-1] - sorted_dates[0]).days
    if duration_days < 365:
        start_week = sorted_dates[0] - timedelta(days=sorted_dates[0].weekday())
        end_week = sorted_dates[-1] - timedelta(days=sorted_dates[-1].weekday())
        timeline = []
        current = start_week
        while current <= end_week:
            timeline.append(current)
            current += timedelta(days=7)
        return "Weekly", timeline, None

    start_year, start_month = sorted_dates[0].year, sorted_dates[0].month
    end_year, end_month = sorted_dates[-1].year, sorted_dates[-1].month
    month_keys = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        month_keys.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    timeline = [datetime(year, month, 1) for year, month in month_keys]
    return "Monthly", timeline, month_keys


def analyze_message_emotions(text, language):
    """Score a single message with lexicon-based emotion categories."""
    rules = LANGUAGE_RULES[language]
    lexicon = rules["lexicon"]
    negations = rules["negations"]
    boosters = rules["boosters"]
    downtoners = rules["downtoners"]

    scores = {emotion: 0.0 for emotion in EMOTIONS}
    signal_hits = 0

    tokens = tokenize_text(text)
    for idx, token in enumerate(tokens):
        prev_token = tokens[idx - 1] if idx > 0 else ""
        left_window = tokens[max(0, idx - 2):idx]

        weight = 1.0
        if prev_token in boosters:
            weight *= 1.5
        elif prev_token in downtoners:
            weight *= 0.65

        if any(neg in left_window for neg in negations):
            weight *= 0.35

        for emotion in EMOTIONS:
            if token in lexicon[emotion]:
                scores[emotion] += weight
                signal_hits += 1

    for emoji in extract_emojis(text):
        if emoji in EMOJI_EMOTION_MAP:
            for emotion, emoji_weight in EMOJI_EMOTION_MAP[emoji].items():
                scores[emotion] += emoji_weight
            signal_hits += 1

    total_score = sum(scores.values())
    if total_score == 0:
        normalized = {emotion: 0.0 for emotion in EMOTIONS}
        dominant_emotion = "neutral"
        confidence = 0.0
    else:
        normalized = {emotion: scores[emotion] / total_score for emotion in EMOTIONS}
        dominant_emotion = max(scores, key=scores.get)
        confidence = normalized[dominant_emotion]

    return dominant_emotion, confidence, signal_hits, normalized


if "sentiment_results" not in st.session_state:
    st.session_state.sentiment_results = None

st.divider()

language_options = ["English", "Italian", "Spanish"]
default_language = st.session_state.get("language", "English")
default_language_idx = language_options.index(default_language) if default_language in language_options else 0

year_options = ["All"] + [str(year) for year in sorted({msg["date"].year for msg in messages_with_dates}, reverse=True)]
default_visible_emotions = EMOTIONS[:]

col1, col2, col3 = st.columns(3)
with col1:
    emotion_language = st.selectbox(
        "Language",
        options=language_options,
        index=default_language_idx,
    )
    st.session_state.language = emotion_language
with col2:
    selected_year = st.selectbox("Year", options=year_options, index=0)
with col3:
    min_words = st.slider("Min Words", min_value=1, max_value=12, value=2)

visible_emotions = st.multiselect(
    "Emotions to Display",
    options=EMOTIONS,
    default=default_visible_emotions,
)
st.caption("Available categories: joy, love, trust, surprise, anger, sadness, fear, disgust")

if not visible_emotions:
    st.warning("Select at least one emotion to display.")
    st.stop()

filtered_messages = []
for msg in messages_with_dates:
    if selected_year != "All" and msg["date"].year != int(selected_year):
        continue
    if len(msg["text"].split()) < min_words:
        continue
    filtered_messages.append(msg)

summary_col1, summary_col2 = st.columns(2)
with summary_col1:
    st.metric("Messages", f"{len(filtered_messages):,}")
with summary_col2:
    st.metric("Speakers", f"{len(set(msg['speaker'] for msg in filtered_messages)):,}")

if st.button("Analyze Emotions", type="primary", use_container_width=True):
    if not filtered_messages:
        st.warning("No messages match current filters.")
    else:
        with st.spinner(f"Analyzing {len(filtered_messages):,} messages..."):
            analyzed = []
            progress = st.progress(0)
            total = len(filtered_messages)

            for idx, msg in enumerate(filtered_messages):
                dominant_emotion, confidence, signal_hits, normalized = analyze_message_emotions(
                    msg["text"], emotion_language
                )
                row = {
                    "date": msg["date"],
                    "speaker": msg["speaker"],
                    "text": msg["text"],
                    "dominant_emotion": dominant_emotion,
                    "confidence": confidence,
                    "signal_hits": signal_hits,
                }
                for emotion in EMOTIONS:
                    row[f"score_{emotion}"] = normalized[emotion]
                analyzed.append(row)

                if idx % 50 == 0 or idx == total - 1:
                    progress.progress((idx + 1) / total)

            progress.empty()
            st.session_state.sentiment_results = {
                "messages": analyzed,
                "year": selected_year,
                "min_words": min_words,
                "language": emotion_language,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        st.success(f"✅ Analysis complete for {len(analyzed):,} messages.")

if not st.session_state.sentiment_results:
    st.info("Set options above and click `Analyze Emotions`.")
    st.stop()

results = st.session_state.sentiment_results

# Guard against old cached schema from prior sentiment versions.
required_score_columns = [f"score_{emotion}" for emotion in EMOTIONS]
if results.get("messages"):
    first_result = results["messages"][0]
    missing_columns = [col for col in required_score_columns if col not in first_result]
    if missing_columns:
        st.session_state.sentiment_results = None
        st.warning("Detected old cached sentiment data. Click `Analyze Emotions` to generate fresh emotion results.")
        st.stop()

if (
    results.get("year") != selected_year
    or results.get("min_words") != min_words
    or results.get("language") != emotion_language
):
    st.info("Filters changed. Click `Analyze Emotions` to refresh.")

emotion_df = pd.DataFrame(results["messages"])
if emotion_df.empty:
    st.warning("No emotion results to display.")
    st.stop()

st.divider()
st.caption(
    f"Dictionary analysis | Language: {results['language']} | Year: {results['year']} | "
    f"Min words: {results['min_words']} | Run: {results['analysis_time']}"
)

metric1, metric2, metric3 = st.columns(3)
neutral_rate = (emotion_df["dominant_emotion"] == "neutral").mean() * 100
top_non_neutral = emotion_df[emotion_df["dominant_emotion"] != "neutral"]["dominant_emotion"]
top_emotion = top_non_neutral.value_counts().idxmax() if not top_non_neutral.empty else "neutral"

with metric1:
    st.metric("Top Emotion", top_emotion.title())
with metric2:
    st.metric("Neutral Messages", f"{neutral_rate:.1f}%")
with metric3:
    st.metric("Avg Signals/Message", f"{emotion_df['signal_hits'].mean():.2f}")

st.divider()

st.subheader("🎭 Emotion Distribution")
overall_scores = {emotion: emotion_df[f"score_{emotion}"].sum() for emotion in visible_emotions}
overall_total = sum(overall_scores.values())

if overall_total == 0:
    st.info("No detectable emotion signals for the selected filters.")
else:
    distribution_df = pd.DataFrame(
        {
            "emotion": list(overall_scores.keys()),
            "share_pct": [(overall_scores[e] / overall_total) * 100 for e in overall_scores],
        }
    ).sort_values("share_pct", ascending=False)

    fig_distribution = go.Figure()
    fig_distribution.add_trace(
        go.Bar(
            x=distribution_df["emotion"],
            y=distribution_df["share_pct"],
            marker=dict(color=[EMOTION_COLORS[e] for e in distribution_df["emotion"]]),
            text=[f"{value:.1f}%" for value in distribution_df["share_pct"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Share: %{y:.1f}%<extra></extra>",
        )
    )
    fig_distribution.update_layout(
        title=dict(text="Overall Emotion Mix", font=dict(size=20, color="#1f2937")),
        xaxis=dict(title="Emotion", showgrid=False),
        yaxis=dict(title="Share of Emotion Signals (%)", showgrid=True, gridcolor="rgba(0,0,0,0.05)", range=[0, 100]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=420,
        margin=dict(l=60, r=40, t=70, b=60),
    )
    st.plotly_chart(fig_distribution, use_container_width=True)

st.divider()

st.subheader("👥 Emotion by Speaker (Dodged)")
speaker_group = emotion_df.groupby("speaker")[[f"score_{emotion}" for emotion in visible_emotions]].sum()
speaker_group = speaker_group.div(speaker_group.sum(axis=1).replace(0, 1), axis=0) * 100
speaker_group = speaker_group.sort_values(by=f"score_{visible_emotions[0]}", ascending=False)

fig_speaker = go.Figure()
for emotion in visible_emotions:
    fig_speaker.add_trace(
        go.Bar(
            x=speaker_group.index.tolist(),
            y=speaker_group[f"score_{emotion}"].tolist(),
            name=emotion.title(),
            marker=dict(color=EMOTION_COLORS[emotion]),
            hovertemplate=f"<b>{emotion.title()}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        )
    )

fig_speaker.update_layout(
    title=dict(text="Emotion Composition by Speaker", font=dict(size=20, color="#1f2937")),
    xaxis=dict(title="Speaker", showgrid=False),
    yaxis=dict(title="Emotion Share (%)", showgrid=True, gridcolor="rgba(0,0,0,0.05)", range=[0, 100]),
    barmode="group",
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=460,
    margin=dict(l=60, r=40, t=80, b=60),
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
)
st.plotly_chart(fig_speaker, use_container_width=True)

st.divider()

st.subheader("📈 Emotion Trends Over Time")
timeline_speaker = st.selectbox(
    "Speaker Filter",
    options=["All Speakers"] + sorted(emotion_df["speaker"].unique().tolist()),
)

timeline_df = emotion_df if timeline_speaker == "All Speakers" else emotion_df[emotion_df["speaker"] == timeline_speaker]
sorted_dates = sorted(timeline_df["date"].tolist())
aggregation_type, timeline_dates, timeline_month_keys = build_complete_timeline(sorted_dates)

period_data = defaultdict(lambda: {"count": 0, **{emotion: 0.0 for emotion in visible_emotions}})
if aggregation_type == "Weekly":
    for row in timeline_df.itertuples(index=False):
        key = row.date - timedelta(days=row.date.weekday())
        period_data[key]["count"] += 1
        for emotion in visible_emotions:
            period_data[key][emotion] += getattr(row, f"score_{emotion}")

    trend_values = {
        emotion: [
            (period_data[d][emotion] / period_data[d]["count"]) if period_data[d]["count"] > 0 else 0.0
            for d in timeline_dates
        ]
        for emotion in visible_emotions
    }
else:
    for row in timeline_df.itertuples(index=False):
        key = (row.date.year, row.date.month)
        period_data[key]["count"] += 1
        for emotion in visible_emotions:
            period_data[key][emotion] += getattr(row, f"score_{emotion}")

    trend_values = {
        emotion: [
            (period_data[k][emotion] / period_data[k]["count"]) if period_data[k]["count"] > 0 else 0.0
            for k in timeline_month_keys
        ]
        for emotion in visible_emotions
    }

# Use a tighter monthly y-range so trends are easier to see.
if aggregation_type == "Monthly":
    all_month_values = [value for emotion in visible_emotions for value in trend_values[emotion]]
    if all_month_values:
        y_min = min(all_month_values)
        y_max = max(all_month_values)
        span = y_max - y_min
        pad = max(0.02, span * 0.25)
        trend_y_min = max(0.0, y_min - pad)
        trend_y_max = min(1.0, y_max + pad)

        # Keep a minimum visible range so near-flat months still separate visually.
        if (trend_y_max - trend_y_min) < 0.10:
            center = (trend_y_max + trend_y_min) / 2
            trend_y_min = max(0.0, center - 0.05)
            trend_y_max = min(1.0, center + 0.05)
    else:
        trend_y_min, trend_y_max = 0.0, 1.0
else:
    trend_y_min, trend_y_max = 0.0, 1.0

fig_trend = go.Figure()
for emotion in visible_emotions:
    fig_trend.add_trace(
        go.Scatter(
            x=timeline_dates,
            y=trend_values[emotion],
            mode="lines+markers",
            name=emotion.title(),
            line=dict(color=EMOTION_COLORS[emotion], width=2.5),
            marker=dict(size=4),
            hovertemplate=f"<b>{emotion.title()}</b><br>%{{x}}<br>Avg score: %{{y:.3f}}<extra></extra>",
        )
    )

speaker_suffix = f" - {timeline_speaker}" if timeline_speaker != "All Speakers" else ""
fig_trend.update_layout(
    title=dict(text=f"{aggregation_type} Emotion Trends{speaker_suffix}", font=dict(size=20, color="#1f2937")),
    xaxis=dict(title="Time", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
    yaxis=dict(
        title="Average Emotion Score (0 to 1)",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)",
        range=[trend_y_min, trend_y_max],
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
    height=480,
    margin=dict(l=60, r=40, t=80, b=60),
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

st.subheader("😂 Top 10 Emojis by Speaker")
emoji_counts_by_speaker = defaultdict(Counter)
overall_emoji_counter = Counter()
for msg in messages_with_dates:
    if selected_year != "All" and msg["date"].year != int(selected_year):
        continue
    emojis = extract_emojis(msg["text"])
    if emojis:
        emoji_counts_by_speaker[msg["speaker"]].update(emojis)
        overall_emoji_counter.update(emojis)

if not overall_emoji_counter:
    st.info("No emojis found for the selected year.")
else:
    top_emojis = [emoji for emoji, _ in overall_emoji_counter.most_common(10)]
    speakers_with_emojis = sorted(emoji_counts_by_speaker.keys())
    selected_emoji_speakers = st.multiselect(
        "Emoji Speaker Filter",
        options=speakers_with_emojis,
        default=speakers_with_emojis,
    )

    if not selected_emoji_speakers:
        st.warning("Select at least one speaker to display emoji usage.")
    else:
        speaker_colors = st.session_state.get("speaker_colors", {})
        fig_emoji = go.Figure()
        for speaker in selected_emoji_speakers:
            fig_emoji.add_trace(
                go.Bar(
                    x=top_emojis,
                    y=[emoji_counts_by_speaker[speaker].get(emoji, 0) for emoji in top_emojis],
                    name=speaker,
                    marker=dict(color=speaker_colors.get(speaker, "#667eea")),
                    hovertemplate="<b>%{fullData.name}</b><br>Emoji: %{x}<br>Count: %{y}<extra></extra>",
                )
            )

        year_label = selected_year if selected_year != "All" else "All Years"
        fig_emoji.update_layout(
            title=dict(text=f"Top 10 Emojis by Speaker ({year_label})", font=dict(size=20, color="#1f2937")),
            xaxis=dict(title="Emoji", showgrid=False),
            yaxis=dict(title="Usage Count", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            barmode="group",
            height=460,
            margin=dict(l=60, r=40, t=80, b=60),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_emoji, use_container_width=True)

st.divider()

st.subheader("💾 Export")
export_df = emotion_df.copy()
if pd.api.types.is_datetime64_any_dtype(export_df["date"]):
    export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
else:
    export_df["date"] = export_df["date"].apply(
        lambda value: value.strftime("%Y-%m-%d %H:%M:%S") if hasattr(value, "strftime") else str(value)
    )

column_map = {
    "date": "Date",
    "speaker": "Speaker",
    "text": "Message",
    "dominant_emotion": "DominantEmotion",
    "confidence": "Confidence",
    "signal_hits": "EmotionSignals",
}
for emotion in EMOTIONS:
    column_map[f"score_{emotion}"] = f"Score_{emotion.title()}"
export_df = export_df.rename(columns=column_map)

csv_data = export_df.to_csv(index=False)
year_suffix = results["year"] if results["year"] != "All" else "all_years"
language_suffix = results["language"].lower()
st.download_button(
    label="📥 Download Emotion Results (CSV)",
    data=csv_data,
    file_name=f"emotion_dictionary_{language_suffix}_{year_suffix}_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True,
)
