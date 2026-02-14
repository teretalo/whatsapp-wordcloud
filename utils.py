"""Shared utility functions for WhatsApp WordCloud app."""
import re
import os
from collections import defaultdict
from datetime import datetime
from wordcloud import WordCloud, STOPWORDS
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation


def parse_whatsapp_messages_with_years(text):
    """Extract messages from WhatsApp conversation text with year and date information."""
    from datetime import datetime

    # WhatsApp format patterns (various formats)
    patterns = [
        r'\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\]\s*([^:]+):\s*(.+)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\s*-\s*([^:]+):\s*(.+)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?\s*([^:]+):\s*(.+)'
    ]

    messages_by_year = defaultdict(list)
    all_messages = []
    speakers = defaultdict(int)
    message_dates = []  # Store dates for timeline

    for line in text.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()
                # Extract date components
                day = int(groups[0])
                month = int(groups[1])
                year_str = groups[2]

                # Convert 2-digit year to 4-digit
                if len(year_str) == 2:
                    year_int = int(year_str)
                    # Assume 00-30 is 2000s, 31-99 is 1900s
                    year = 2000 + year_int if year_int <= 30 else 1900 + year_int
                else:
                    year = int(year_str)

                speaker = groups[-2].strip()
                message = groups[-1].strip()

                # Skip system messages
                if not any(sys_msg in message.lower() for sys_msg in [
                    'media omitted', 'missed voice call', 'missed video call',
                    'changed the subject', 'changed this group', 'left',
                    'added', 'removed', 'created group'
                ]):
                    # Create date object
                    try:
                        date_obj = datetime(year, month, day)
                        message_dates.append(date_obj)
                        messages_by_year[year].append(message)
                        all_messages.append(message)
                        speakers[speaker] += 1
                    except ValueError:
                        # Skip invalid dates
                        pass
                break

    return all_messages, messages_by_year, speakers, message_dates


def get_available_years(messages_by_year):
    """Get sorted list of years from the conversation."""
    return sorted(messages_by_year.keys(), reverse=True)


def aggregate_messages_by_time(message_dates):
    """Aggregate messages by week or month depending on conversation duration."""
    from datetime import timedelta
    from collections import Counter
    import pandas as pd

    if not message_dates:
        return [], []

    # Sort dates
    sorted_dates = sorted(message_dates)

    # Calculate conversation duration
    duration = (sorted_dates[-1] - sorted_dates[0]).days

    # Determine aggregation: weekly if < 365 days, monthly if >= 365 days
    if duration < 365:
        # Aggregate by week
        # Get the Monday of each week (ISO week)
        week_starts = [date - timedelta(days=date.weekday()) for date in sorted_dates]
        date_counts = Counter(week_starts)

        # Create complete timeline with zero counts for missing weeks
        all_weeks = []
        current = week_starts[0]
        while current <= week_starts[-1]:
            all_weeks.append(current)
            current += timedelta(days=7)

        dates = all_weeks
        counts = [date_counts.get(date, 0) for date in all_weeks]

    else:
        # Aggregate by month
        month_keys = [(date.year, date.month) for date in sorted_dates]
        month_counts = Counter(month_keys)

        # Create complete timeline with zero counts for missing months
        start_year, start_month = month_keys[0]
        end_year, end_month = month_keys[-1]

        all_months = []
        year, month = start_year, start_month
        while (year, month) <= (end_year, end_month):
            all_months.append((year, month))
            month += 1
            if month > 12:
                month = 1
                year += 1

        # Convert to datetime for plotting
        from datetime import datetime
        dates = [datetime(year, month, 1) for year, month in all_months]
        counts = [month_counts.get(month_key, 0) for month_key in all_months]

    return dates, counts


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


def parse_whatsapp_messages_with_dates(text):
    """Extract messages from WhatsApp conversation text with full datetime information."""
    # WhatsApp format patterns (various formats)
    patterns = [
        # Pattern with brackets: [DD/MM/YYYY, HH:MM:SS AM/PM]
        r'\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s?(AM|PM)?\]\s*([^:]+):\s*(.+)',
        # Pattern with dash: DD/MM/YYYY, HH:MM:SS AM/PM - Speaker:
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s?(AM|PM)?\s*-\s*([^:]+):\s*(.+)',
        # Pattern without separator: DD/MM/YYYY, HH:MM:SS AM/PM Speaker:
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s?(AM|PM)?\s*([^:]+):\s*(.+)'
    ]

    messages_with_dates = []
    all_messages = []
    messages_by_year = defaultdict(list)
    speakers = defaultdict(int)

    for line in text.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()

                # Extract date components
                day = int(groups[0])
                month = int(groups[1])
                year_str = groups[2]
                hour = int(groups[3])
                minute = int(groups[4])
                second = int(groups[5]) if groups[5] else 0
                am_pm = groups[6]
                speaker = groups[7].strip()
                message = groups[8].strip()

                # Convert 2-digit year to 4-digit
                if len(year_str) == 2:
                    year_int = int(year_str)
                    year = 2000 + year_int if year_int <= 30 else 1900 + year_int
                else:
                    year = int(year_str)

                # Convert to 24-hour format if AM/PM is present
                if am_pm:
                    if am_pm == 'PM' and hour != 12:
                        hour += 12
                    elif am_pm == 'AM' and hour == 12:
                        hour = 0

                # Create datetime object
                try:
                    msg_date = datetime(year, month, day, hour, minute, second)
                except ValueError:
                    # Skip invalid dates
                    break

                # Skip system messages
                if not any(sys_msg in message.lower() for sys_msg in [
                    'media omitted', 'missed voice call', 'missed video call',
                    'changed the subject', 'changed this group', 'left',
                    'added', 'removed', 'created group'
                ]):
                    messages_with_dates.append({
                        'text': message,
                        'date': msg_date,
                        'speaker': speaker
                    })
                    all_messages.append(message)
                    messages_by_year[year].append(message)
                    speakers[speaker] += 1
                break

    return messages_with_dates, all_messages, messages_by_year, speakers


def perform_topic_modeling(messages, num_topics=5, language='English'):
    """
    Perform topic modeling on messages using Latent Dirichlet Allocation (LDA).

    Args:
        messages: List of message texts
        num_topics: Number of topics to discover
        language: Language for stopwords

    Returns:
        topics: List of topics, each containing top words with weights
        model: Trained LDA model
        vectorizer: Fitted CountVectorizer
    """
    if not messages or len(messages) < num_topics:
        return [], None, None

    # Get language-specific stopwords
    stopwords = get_stopwords_for_language(language)

    # Convert to list for sklearn
    stopwords_list = list(stopwords)

    # Create document-term matrix
    vectorizer = CountVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.8,
        stop_words=stopwords_list,
        lowercase=True
    )

    try:
        doc_term_matrix = vectorizer.fit_transform(messages)
    except ValueError:
        # Not enough valid terms
        return [], None, None

    # Perform LDA
    lda_model = LatentDirichletAllocation(
        n_components=num_topics,
        max_iter=20,
        learning_method='online',
        random_state=42,
        n_jobs=-1
    )

    lda_model.fit(doc_term_matrix)

    # Extract topics with words and weights
    feature_names = vectorizer.get_feature_names_out()
    topics = []

    for topic_idx, topic in enumerate(lda_model.components_):
        # Get top 10 words for this topic
        top_indices = topic.argsort()[-10:][::-1]
        top_words = [(feature_names[i], topic[i]) for i in top_indices]
        topics.append(top_words)

    return topics, lda_model, vectorizer


def get_message_topics(messages, model, vectorizer):
    """
    Assign each message to its dominant topic.

    Args:
        messages: List of message texts
        model: Trained LDA model
        vectorizer: Fitted CountVectorizer

    Returns:
        List of topic assignments (integers)
    """
    if model is None or vectorizer is None:
        return []

    # Transform messages
    doc_term_matrix = vectorizer.transform(messages)

    # Get topic distributions
    topic_distributions = model.transform(doc_term_matrix)

    # Assign each message to its dominant topic
    topic_assignments = topic_distributions.argmax(axis=1)

    return topic_assignments.tolist()


def aggregate_topics_by_time(messages_with_topics, aggregation='day'):
    """
    Aggregate topic counts by time period.

    Args:
        messages_with_topics: List of dicts with 'date' and 'topic' keys
        aggregation: 'day', 'fortnight', or 'month'

    Returns:
        DataFrame with date and topic count columns
    """
    if not messages_with_topics:
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(messages_with_topics)

    # Set date as index
    df.set_index('date', inplace=True)

    # Determine resampling frequency
    if aggregation == 'day':
        freq = 'D'
    elif aggregation == 'fortnight':
        freq = '2W'
    elif aggregation == 'month':
        freq = 'M'
    else:
        freq = 'D'

    # Group by time period and topic, count messages
    topic_counts = df.groupby([pd.Grouper(freq=freq), 'topic']).size().unstack(fill_value=0)

    # Reset index to make date a column
    topic_counts.reset_index(inplace=True)
    topic_counts.rename(columns={'date': 'period'}, inplace=True)

    return topic_counts
