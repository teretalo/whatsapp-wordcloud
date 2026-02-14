# WhatsApp WordCloud Generator

A Streamlit app that generates wordclouds from WhatsApp conversation exports, focusing on substantive words by filtering out articles, pronouns, prepositions, and other non-substantive parts of speech.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the app:
```bash
streamlit run app.py
```

Then upload a WhatsApp chat export (txt file) to generate the wordcloud.

## Features

- Upload WhatsApp conversation exports (.txt files)
- Automatic parsing of various WhatsApp date/time formats
- Filters out non-substantive words (articles, pronouns, prepositions, conjunctions, common verbs, etc.)
- Beautiful wordcloud visualization
- Shows word count statistics

## How to Export WhatsApp Chats

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
