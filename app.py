import streamlit as st
import re
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from io import StringIO
import os
from collections import defaultdict

def parse_whatsapp_messages_with_years(text):
    """Extract messages from WhatsApp conversation text with year information."""
    # WhatsApp format patterns (various formats)
    patterns = [
        r'\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\]\s*([^:]+):\s*(.+)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\s*-\s*([^:]+):\s*(.+)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\s*([^:]+):\s*(.+)'
    ]

    messages_by_year = defaultdict(list)
    all_messages = []

    for line in text.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()
                # Extract year - it could be 2-digit or 4-digit
                year_str = groups[2]

                # Convert 2-digit year to 4-digit
                if len(year_str) == 2:
                    year_int = int(year_str)
                    # Assume 00-30 is 2000s, 31-99 is 1900s
                    year = 2000 + year_int if year_int <= 30 else 1900 + year_int
                else:
                    year = int(year_str)

                message = groups[-1].strip()

                # Skip system messages
                if not any(sys_msg in message.lower() for sys_msg in [
                    'media omitted', 'missed voice call', 'missed video call',
                    'changed the subject', 'changed this group', 'left',
                    'added', 'removed', 'created group'
                ]):
                    messages_by_year[year].append(message)
                    all_messages.append(message)
                break

    return all_messages, messages_by_year

def get_available_years(messages_by_year):
    """Get sorted list of years from the conversation."""
    return sorted(messages_by_year.keys(), reverse=True)

def get_font_path():
    """Find an available TrueType font on the system."""
    # Common font locations on macOS (note: filenames have spaces)
    font_paths = [
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/System/Library/Fonts/Supplemental/Arial Narrow.ttf',
        '/System/Library/Fonts/Monaco.ttf',
        '/System/Library/Fonts/Geneva.ttf',
        '/Library/Fonts/Arial.ttf',
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path

    # If no font found, return None and let wordcloud use default
    return None

def get_stopwords_for_language(language):
    """Get stopwords for the specified language."""
    # Base stopwords (always included)
    stopwords = set(STOPWORDS)

    # Single letters (all languages)
    single_letters = {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
    }
    stopwords.update(single_letters)

    if language == "English":
        english_stopwords = {
            # Articles
            'an', 'the',
            # Pronouns
            'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
            'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'themselves',
            'this', 'that', 'these', 'those',
            # Common verbs (to be, to have, etc.)
            'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing',
            'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could',
            # Prepositions
            'in', 'on', 'at', 'to', 'for', 'with', 'from', 'of', 'by', 'about', 'as',
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between',
            'under', 'over', 'up', 'down', 'out', 'off', 'along',
            # Conjunctions
            'and', 'but', 'or', 'nor', 'so', 'yet', 'if', 'because', 'although', 'though',
            'while', 'when', 'where', 'why', 'how',
            # Common adverbs
            'just', 'very', 'really', 'too', 'also', 'well', 'still', 'now', 'then',
            'here', 'there', 'yes', 'no', 'not',
            # Other common words
            'get', 'got', 'going', 'go', 'went', 'like', 'know', 'think', 'see', 'want',
            'oh', 'ok', 'okay', 'yeah', 'yep', 'nah', 'haha', 'lol', "https"
        }
        stopwords.update(english_stopwords)

    elif language == "Italian":
        italian_stopwords = {
            # Articles
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'dei', 'degli', 'delle',
            # Pronouns
            'io', 'tu', 'lui', 'lei', 'noi', 'voi', 'loro', 'mi', 'ti', 'ci', 'vi', 'si',
            'me', 'te', 'lui', 'lei', 'noi', 'voi', 'loro',
            'mio', 'mia', 'miei', 'mie', 'tuo', 'tua', 'tuoi', 'tue', 'suo', 'sua', 'suoi', 'sue',
            'nostro', 'nostra', 'nostri', 'nostre', 'vostro', 'vostra', 'vostri', 'vostre',
            'questo', 'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle',
            'che', 'chi', 'cui', 'quale', 'quali',
            # Verbs (essere, avere, fare)
            'è', 'sono', 'sei', 'siamo', 'siete', 'era', 'erano', 'essere', 'stato', 'stata', 'stati', 'state',
            'ho', 'hai', 'ha', 'abbiamo', 'avete', 'hanno', 'avere', 'aveva', 'avevano', 'avuto',
            'faccio', 'fai', 'fa', 'facciamo', 'fate', 'fanno', 'fare', 'fatto',
            'va', 'vai', 'vado', 'andiamo', 'andate', 'vanno', 'andare', 'andato',
            'può', 'puoi', 'posso', 'possiamo', 'potete', 'possono', 'potere',
            'devo', 'devi', 'deve', 'dobbiamo', 'dovete', 'devono', 'dovere',
            'vuoi', 'vuole', 'voglio', 'vogliamo', 'volete', 'vogliono', 'volere',
            # Prepositions
            'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'del', 'al', 'dal', 'nel', 'col', 'sul',
            'dello', 'alla', 'dalla', 'nella', 'sulla', 'dei', 'agli', 'dai', 'nei', 'sui', "ai", "al"
            # Conjunctions
            'e', 'ed', 'o', 'od', 'ma', 'però', 'se', 'perché', 'quando', 'come', 'mentre', 'dove',
            'anche', 'ancora', 'quindi', 'allora', 'però',
            # Common adverbs
            'non', 'più', 'molto', 'poco', 'tanto', 'così', 'già', 'mai', 'sempre', 'solo', 'già',
            'qui', 'qua', 'lì', "li", 'là', 'sì', 'no',
            # Other common words
            'cosa', 'cose', 'tutto', 'tutti', 'tutte', 'niente', 'nulla',
            'ah', 'oh', 'eh', 'boh', 'ok', 'okay', 'haha', 'ahah', "sa", "ce", "https", "ne", "c'è", "ad", "hihi", "cmq", "l'ho", "sto", "lho", "sta", "xo", "della"
        }
        stopwords.update(italian_stopwords)

    elif language == "Spanish":
        spanish_stopwords = {
            # Articles
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            # Pronouns
            'yo', 'tú', 'él', 'ella', 'nosotros', 'nosotras', 'vosotros', 'vosotras', 'ellos', 'ellas',
            'me', 'te', 'se', 'nos', 'os', 'le', 'les', 'lo', 'lo',
            'mi', 'mis', 'tu', 'tus', 'su', 'sus', 'nuestro', 'nuestra', 'nuestros', 'nuestras',
            'vuestro', 'vuestra', 'vuestros', 'vuestras',
            'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas',
            'que', 'quien', 'quienes', 'cual', 'cuales', 'cuál', 'cuáles',
            # Verbs (ser, estar, haber, hacer)
            'soy', 'eres', 'es', 'somos', 'sois', 'son', 'ser', 'era', 'eras', 'éramos', 'eran', 'sido',
            'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'estar', 'estaba', 'estado',
            'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'haber', 'había', 'habías', 'habían', 'habido',
            'hago', 'haces', 'hace', 'hacemos', 'hacéis', 'hacen', 'hacer', 'hecho',
            'voy', 'vas', 'va', 'vamos', 'vais', 'van', 'ir', 'ido',
            'puedo', 'puedes', 'puede', 'podemos', 'podéis', 'pueden', 'poder',
            'debo', 'debes', 'debe', 'debemos', 'debéis', 'deben', 'deber',
            'quiero', 'quieres', 'quiere', 'queremos', 'queréis', 'quieren', 'querer',
            # Prepositions
            'de', 'del', 'a', 'al', 'en', 'con', 'por', 'para', 'sin', 'sobre', 'entre', 'desde', 'hasta', 'hacia',
            # Conjunctions
            'y', 'e', 'o', 'u', 'pero', 'sino', 'si', 'porque', 'aunque', 'cuando', 'como', 'donde', 'mientras',
            'también', 'tampoco', 'entonces', 'pues',
            # Common adverbs
            'no', 'más', 'muy', 'poco', 'mucho', 'tanto', 'así', 'ya', 'nunca', 'siempre', 'solo', 'sólo',
            'aquí', 'ahí', 'allí', 'acá', 'allá', 'sí',
            # Other common words
            'qué', 'cosa', 'cosas', 'todo', 'todos', 'todas', 'nada',
            'ah', 'oh', 'eh', 'ok', 'okay', 'jaja', 'jeje', 'jajaja', "https"
        }
        stopwords.update(spanish_stopwords)

    return stopwords

def create_wordcloud(text, language):
    """Generate wordcloud from text with language-specific stopwords."""
    # Get language-specific stopwords
    stopwords = get_stopwords_for_language(language)

    # Get a suitable font
    font_path = get_font_path()

    # Generate wordcloud
    wordcloud_kwargs = {
        'width': 800,
        'height': 400,
        'background_color': 'white',
        'stopwords': stopwords,
        'colormap': 'viridis',
        'min_font_size': 10,
        'max_words': 100,
        'relative_scaling': 0.5,
        'collocations': False
    }

    # Add font_path if found
    if font_path:
        wordcloud_kwargs['font_path'] = font_path

    wordcloud = WordCloud(**wordcloud_kwargs).generate(text)

    return wordcloud

# Streamlit app
st.set_page_config(page_title="WhatsApp WordCloud", page_icon="💬", layout="wide")

st.title("💬 WhatsApp Conversation WordCloud")
st.markdown("Upload a WhatsApp chat export (txt file) to generate a wordcloud of the most frequent substantive words.")

# File uploader
uploaded_file = st.file_uploader("Choose a WhatsApp conversation file", type=['txt'])

if uploaded_file is not None:
    # Read the file
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    text_content = stringio.read()

    with st.spinner("Processing conversation..."):
        # Parse messages with year information
        all_messages, messages_by_year = parse_whatsapp_messages_with_years(text_content)

        if not all_messages:
            st.error("Could not extract messages from the file. Please make sure it's a valid WhatsApp chat export.")
        else:
            # Get available years
            available_years = get_available_years(messages_by_year)

            # Create two columns for dropdowns
            col1, col2 = st.columns(2)

            with col1:
                # Language selection
                language = st.selectbox(
                    "Select Language",
                    options=["English", "Italian", "Spanish"],
                    index=0
                )

            with col2:
                # Year selection
                year_options = ["All"] + [str(year) for year in available_years]
                selected_year = st.selectbox(
                    "Select Year",
                    options=year_options,
                    index=0
                )

            # Filter messages by year
            if selected_year == "All":
                messages_to_process = ' '.join(all_messages)
                display_year = "all years"
            else:
                year_int = int(selected_year)
                messages_to_process = ' '.join(messages_by_year[year_int])
                display_year = selected_year

            # Create wordcloud
            if messages_to_process.strip():
                wordcloud = create_wordcloud(messages_to_process, language)

                # Display wordcloud
                st.subheader(f"WordCloud - {language} ({display_year})")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)

                # Show statistics
                word_count = len(messages_to_process.split())
                message_count = len(messages_by_year[year_int]) if selected_year != "All" else len(all_messages)
                st.info(f"📊 Processed {word_count} words from {message_count} messages ({display_year})")
            else:
                st.warning(f"No messages found for {display_year}")

else:
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
