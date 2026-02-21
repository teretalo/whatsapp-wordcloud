# WhatsApp Conversation Analyzer - Development Log

This file tracks the development progress and architecture decisions for the WhatsApp Conversation Analyzer project.

## Project Overview

A Streamlit-based web application that analyzes WhatsApp chat exports to provide insights about conversations including:
- Word clouds and word frequency analysis
- Speaker activity and contribution patterns
- Dictionary-based emotion analysis over time and by speaker

## Tech Stack

- **Frontend**: Streamlit 1.31.0
- **Visualization**: Plotly 5.18.0, WordCloud 1.9.3, Matplotlib 3.8.2
- **ML/NLP**: Transformers 4.30.0+, PyTorch 2.0.0+, scikit-learn 1.3.0+
- **Data Processing**: Pandas 2.0.0+

## Current Structure

```
whatsapp-wordcloud/
├── 🏠 Home.py              # Main entry point, file upload, timeline
├── pages/
│   ├── 1_👥 Who writes the most?.py    # Speaker analysis
│   ├── 2_📝Words.py                     # Word analysis
│   └── 4_😊 Sentiment.py               # Dictionary-based emotion analysis
├── utils.py                # Shared utilities and parsing functions
├── requirements.txt        # Python dependencies
└── .streamlit/
    └── config.toml        # Streamlit configuration
```

## Feature Documentation

### Home Page (🏠 Home.py)
- **File Upload**: Accepts WhatsApp .txt exports
- **Parsing**: Dual parsing system
  - `parse_whatsapp_messages_with_years()` - For main analysis with speaker timeline data
  - `parse_whatsapp_messages_with_dates()` - For theme classification (preserves full datetime)
- **Timeline Visualization**: Interactive Plotly chart showing message activity over time
- **Color Consistency**: Generates speaker color palette stored in session state
- **Session State**: Manages all shared data across pages

### Speakers Page (1_👥 Who writes the most?.py)
- **Activity Analysis**: Message count and word count metrics by speaker
- **Distribution Charts**: Doughnut charts showing speaker contributions
- **Timeline**: Weekly/monthly activity visualization with consistent speaker colors
- **Message Types**: Analysis of links, media, emojis per speaker
- **Design**: Plotly-based with consistent color palette

### Words Page (2_📝Words.py)
- **Word Frequency**: Analysis of most common words
- **Filtering**: Language-aware stopword removal (English, Italian, Spanish)
- **WordCloud**: Visual representation of word frequencies

### Themes Page (3_🏷️Themes.py) ⭐ **Latest Update - Team Alfredo**
- **Zero-Shot Classification**: Uses `facebook/bart-large-mnli` model
- **Language Selector**: Dedicated dropdown for classification language (English/Italian/Spanish)
  - Updates session state to persist across pages
  - Located at top of page for easy access
- **Predefined Themes**: 6 WhatsApp-optimized categories
  - Family & Relationships
  - Love & Romance
  - Work & Career
  - Social Plans & Events
  - Entertainment & Leisure
  - Daily Life & Routine
- **Theme Comparison**: Select primary theme + optional comparison theme
- **Speaker Analysis**: Grouped bar charts showing theme discussion by speaker
  - Uses speaker colors from session state
  - Grouped bars when comparing themes
- **Timeline Visualization**: Bar charts focused on theme activity over time
  - Speaker filter dropdown (All Speakers or specific person)
  - Grouped bars when comparing two themes
  - Weekly or monthly aggregation based on duration
  - Consistent design language with other pages
- **Performance**: Cached model loading, batched inference (50 messages/batch)
- **Exports**: CSV downloads with confidence scores and match flags

### Sentiment Page (4_😊 Sentiment.py) ⭐ **Latest Update - Team Teresa**
- **Method**: Fast dictionary-based emotion scoring (lexicon + lightweight negation/intensity rules)
- **Languages**: English, Italian, Spanish selectable in-page
- **Filters**: Year filter + minimum words per message to reduce noise
- **Emotions**: joy, love, trust, surprise, anger, sadness, fear, disgust
- **Visualization**:
  - Emotion distribution chart
  - Stacked emotion mix by speaker
  - Emotion trends over time with selectable emotion filters
  - Grouped bar chart of top 10 most used emojis by speaker
- **Export**: CSV download with dominant emotion, confidence, and per-emotion scores

## Architecture Decisions

### Session State Management
All pages share data through Streamlit session state:
- `chat_uploaded`: Boolean flag
- `all_messages`: List of message texts
- `messages_by_year`: Dict of messages grouped by year
- `messages_with_dates`: List of dicts with {text, date, speaker} for emotion timeline analysis
- `speakers`: Dict of speaker message counts
- `message_dates`: List of datetime objects
- `speaker_colors`: Consistent color mapping for all visualizations
- `speaker_timeline_data`: Timeline data for speaker activity
- `language`: Selected language (English/Italian/Spanish)
- `sentiment_results`: Cached sentiment inference results for the current chat

### Themes Page Status
- `pages/3_🏷️Themes.py` has been removed from the app for temporary redesign/brainstorming.

### Parsing Strategy
Two parsing functions serve different needs:
1. **`parse_whatsapp_messages_with_years()`**: Returns detailed speaker analytics
2. **`parse_whatsapp_messages_with_dates()`**: Returns messages with full datetime for timeline/emotion pages

### Color Consistency
- Speaker colors assigned alphabetically on first upload
- Colors stored in session state and reused across all pages
- Palette: `['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#fee140', '#30cfd0', '#a8edea', '#fed6e3', '#c471ed']`

### Visualization Standards
- **All charts use Plotly** (no matplotlib for visualizations)
- White background (`plot_bgcolor='white', paper_bgcolor='white'`)
- Light grid lines (`gridcolor='rgba(0,0,0,0.05)'`)
- Consistent margins and spacing
- Horizontal legends at bottom for multi-trace charts
- Hover templates with `<extra></extra>` to hide trace info

### Timeline Aggregation
Consistent logic across Speakers and Emotion pages:
- **< 365 days**: Weekly aggregation
- **≥ 365 days**: Monthly aggregation
- All speakers get consistent x-axis (zero-filled for missing periods)

## Development History

### Team Alfredo - February 14, 2026

#### Initial Setup
- Ran the existing Streamlit app
- Fixed Home.py filename (was 🏠 Home.py with emoji)
- Resolved merge conflicts in requirements.txt

#### Topic Model Recovery & Replacement
- Recovered old topic modeling code from git history (commit a376e1f)
- Replaced matplotlib pie charts with Plotly horizontal bar charts
- Added meaningful topic names using top 3 keywords

#### Zero-Shot Classification Implementation
- **Complete rewrite of Themes page** replacing LDA topic modeling
- Implemented zero-shot classification with `facebook/bart-large-mnli`
- Added predefined theme dropdown (6 themes)
- Implemented theme comparison feature (select 2 themes)
- Added language awareness (displays language from Home page)
- Created speaker comparison visualizations
- Built timeline matching "Who writes the most?" page style
- Harmonized all designs with speaker color consistency

#### Bug Fixes
- Fixed `messages_with_dates` tuple unpacking in Home.py
- Added missing `parse_whatsapp_messages_with_dates` import
- Initialized `messages_with_dates` in session state

#### Final Refinements
- **Added language selector** to Themes page (top of page, updates session state)
- **Redesigned timeline visualization** to focus on themes (not speakers)
  - Changed from line charts per speaker to grouped bar charts per theme
  - Added speaker filter dropdown (All Speakers or specific person)
  - Simplified to show theme activity over time with optional comparison
- **Updated CLAUDE.md** to clarify team responsibilities
  - Team Alfredo owns Themes page
  - Team Teresa establishes design patterns that Team Alfredo follows

### Team Teresa - February 21, 2026
- Added `pages/4_😊 Sentiment.py` with a new dedicated sentiment analysis section
- Implemented multilingual sentiment inference with cached model loading and batched processing
- Added sentiment breakdown by speaker (average score + positive/neutral/negative mix)
- Added weekly/monthly sentiment timeline charts with optional speaker filter
- Added CSV export for full sentiment results
- Updated `🏠 Home.py` to initialize/reset `sentiment_results` when a new chat is uploaded

### Team Teresa - February 21, 2026 (Sentiment Rework)
- Reworked sentiment analysis from transformer-based inference to dictionary-based scoring for faster runtime
- Added explicit language selector (English/Italian/Spanish) tied to language-specific lexicons
- Kept the same speaker/time breakdown visualizations to preserve app style consistency
- Added a top-10 emoji usage grouped bar chart broken down by speaker
- Updated sentiment CSV export to include sentiment signal counts and method metadata

### Team Teresa - February 21, 2026 (Emotion Overhaul + Theme Removal)
- Simplified the sentiment UI and renamed the section to Emotion Analysis
- Expanded dictionary analysis beyond polarity with selectable categories: joy, love, trust, surprise, anger, sadness, fear, disgust
- Added user multiselect to control which emotions appear in charts
- Removed `pages/3_🏷️Themes.py` from the app and cleaned theme references in app copy
- Removed `transformers` and `torch` from `requirements.txt` since model-based theme/sentiment inference is no longer active

### Team Teresa - February 21, 2026 (Privacy + Sharing Export)
- Added a `Data Privacy` section on `🏠 Home.py` in simple language
- Added a downloadable JSON highlights export designed for sharing with an LLM
- Embedded LLM instructions inside the JSON payload, including what extra data to request if needed
- Tuned monthly emotion trend y-axis scaling so low-variance lines are easier to read
- Tightened privacy wording for legal accuracy and clarified Cloud Run deployment assumptions
- Moved the `Data Privacy` section to the bottom of the Home page

### Team Teresa - [Previous Contributions]
- Added speaker analysis features
- Implemented word filtering
- Created comprehensive speaker timeline
- [To be documented by Team Teresa]

## Known Issues & TODOs

### Current Issues
- None reported

### Future Enhancements
- [ ] Additional theme categories or custom theme input
- [ ] Multi-language support for zero-shot classification prompts
- [ ] Sentiment analysis per theme
- [ ] Export theme timelines as images
- [ ] Message search/filter by theme

## Team Responsibilities

### Team Alfredo
**Primary Focus**: Themes page (3_🏷️Themes.py)
- Owns the zero-shot classification feature
- Responsible for theme analysis and visualization
- **IMPORTANT**: Automatically adopts design choices and patterns from Team Teresa
- Must maintain consistency with Speakers and Words pages
- Document all changes with "Team Alfredo" tag

### Team Teresa
**Primary Focus**: Speakers and Words pages
- Owns speaker analysis features
- Sets design standards for the application
- Establishes visualization patterns to be followed
- Document all changes with "Team Teresa" tag

## Development Guidelines

### Design Consistency (Critical)
- **Team Teresa establishes design patterns** that Team Alfredo follows
- All pages must use consistent:
  - Color palettes (speaker_colors from session state)
  - Chart styles (Plotly with white backgrounds)
  - Layout patterns (margins, spacing, typography)
  - Interaction patterns (dropdowns, buttons, filters)
- When Team Teresa updates a design element, Team Alfredo adopts it in Themes page

### Code Standards
- Document all significant changes in this file
- Follow existing session state patterns
- Maintain speaker color consistency across features
- Keep visualization styles consistent with Plotly standards
- Use established color palette for new visualizations

## Testing Notes

- Test with both short (<1 year) and long (multi-year) conversations
- Verify speaker colors remain consistent across page navigation
- Test theme classification with various message types
- Check memory usage with large conversations (10k+ messages)

## Deployment Notes

- Streamlit app runs on port 8501
- No model download is required for dictionary-based emotion analysis
- Recommended: 4GB+ RAM for smooth operation with large chats

---

**Last Updated**: February 21, 2026 by Team Teresa
