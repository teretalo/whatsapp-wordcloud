"""Shared utility functions for WhatsApp WordCloud app."""
import re
import os
from collections import defaultdict
from wordcloud import WordCloud, STOPWORDS


def detect_message_type(message):
    """Detect the types of message (link, media, emoji). Returns a list of applicable types.
    A message can belong to multiple categories."""
    import re

    message_lower = message.lower()
    types = []

    # Check for any media omitted patterns (images, videos, audio, documents, stickers, gifs)
    if any(pattern in message_lower for pattern in [
        'omitted', '<attached:', 'image', 'video', 'audio', 'voice message',
        'document', 'sticker', 'gif', '.pdf', '.jpg', '.png', '.mp4'
    ]):
        types.append('media')

    # Check for links (URLs)
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if re.search(url_pattern, message) or 'www.' in message:
        types.append('link')

    # Check for emojis (comprehensive Unicode emoji ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # extended symbols A
        "\U0001FA70-\U0001FAFF"  # extended symbols B
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F780-\U0001F7FF"  # geometric shapes
        "\U0001F800-\U0001F8FF"  # supplemental arrows
        "\U00002300-\U000023FF"  # misc technical
        "\U0001F004"             # mahjong tile
        "\U0001F0CF"             # playing card
        "\U0001F170-\U0001F251"  # enclosed characters
        "]+", flags=re.UNICODE
    )
    if emoji_pattern.search(message):
        types.append('emoji')

    return types


def extract_emojis(message):
    """Extract all emojis from a message, filtering out variation selectors and modifiers."""
    import re

    # More comprehensive emoji pattern including more ranges and skin tone modifiers
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # extended symbols A
        "\U0001FA70-\U0001FAFF"  # extended symbols B
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F780-\U0001F7FF"  # geometric shapes
        "\U0001F800-\U0001F8FF"  # supplemental arrows
        "\U00002300-\U000023FF"  # misc technical
        "\U0001F004"             # mahjong tile
        "\U0001F0CF"             # playing card
        "\U0001F170-\U0001F251"  # enclosed characters
        "\U0001F3FB-\U0001F3FF"  # skin tone modifiers
        "]+", flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(message)

    # Split combined emojis into individual ones and filter out modifiers/selectors
    all_emojis = []
    for emoji_group in emojis:
        for char in emoji_group:
            # Filter out variation selectors, zero-width joiners, and skin tone modifiers
            # Keep the base emoji, skip the modifiers
            if char not in ['\uFE0F', '\uFE0E', '\u200D'] and not ('\U0001F3FB' <= char <= '\U0001F3FF'):
                all_emojis.append(char)

    return all_emojis


def detect_date_format(text):
    """Detect if the date format is MM/DD/YYYY (US) or DD/MM/YYYY (international)."""
    patterns = [
        r'\[(\d{1,2})/(\d{1,2})/(\d{2,4})',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s\d{1,2}:\d{2}'
    ]

    # Check first 100 lines to detect format
    lines = text.split('\n')[:100]

    for line in lines:
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                first_num = int(match.group(1))
                second_num = int(match.group(2))

                # If first number > 12, format must be DD/MM
                if first_num > 12:
                    return 'DD/MM'
                # If second number > 12, format must be MM/DD
                if second_num > 12:
                    return 'MM/DD'

    # Default to MM/DD (US format) if ambiguous
    return 'MM/DD'


def parse_whatsapp_messages_with_years(text):
    """Extract messages from WhatsApp conversation text with year and date information."""
    from datetime import datetime, timedelta

    # Detect date format automatically
    date_format = detect_date_format(text)

    # WhatsApp format patterns (various formats) - now capturing time as well
    patterns = [
        r'\[(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s?(AM|PM)?\]\s*([^:]+):\s*(.+)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s?(AM|PM)?\s*-\s*([^:]+):\s*(.+)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4}),\s(\d{1,2}):(\d{2})(?::(\d{2}))?\s?(AM|PM)?\s*([^:]+):\s*(.+)'
    ]

    messages_by_year = defaultdict(list)
    all_messages = []
    speakers = defaultdict(int)
    message_dates = []  # Store dates for timeline
    speaker_timeline_data = defaultdict(list)  # Store (date, message, word_count) for each speaker
    speaker_message_types = defaultdict(lambda: defaultdict(int))  # Store message type counts per speaker
    speaker_emojis = defaultdict(list)  # Store all emojis used by each speaker
    speaker_initiations = defaultdict(int)  # Store initiation counts per speaker
    initiation_timeline_data = defaultdict(list)  # Store (datetime, speaker) for each initiation

    last_message_time = None  # Track last message timestamp to detect initiations

    for line in text.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()
                # Extract date and time components
                first_num = int(groups[0])
                second_num = int(groups[1])
                year_str = groups[2]
                hour = int(groups[3])
                minute = int(groups[4])
                seconds = int(groups[5]) if groups[5] else 0
                am_pm = groups[6] if groups[6] else None

                # Convert 2-digit year to 4-digit
                if len(year_str) == 2:
                    year_int = int(year_str)
                    # Assume 00-30 is 2000s, 31-99 is 1900s
                    year = 2000 + year_int if year_int <= 30 else 1900 + year_int
                else:
                    year = int(year_str)

                # Handle 12-hour format (AM/PM)
                if am_pm:
                    if am_pm.upper() == 'PM' and hour != 12:
                        hour += 12
                    elif am_pm.upper() == 'AM' and hour == 12:
                        hour = 0

                speaker = groups[-2].strip()
                message = groups[-1].strip()

                # Skip only system notification messages (not media)
                if not any(sys_msg in message.lower() for sys_msg in [
                    'missed voice call', 'missed video call',
                    'changed the subject', 'changed this group', 'left',
                    'added', 'removed', 'created group', 'you deleted this message',
                    'this message was deleted'
                ]):
                    # Parse datetime (date + time) based on detected format
                    datetime_obj = None
                    try:
                        if date_format == 'MM/DD':
                            # US format: first_num is month, second_num is day
                            datetime_obj = datetime(year, first_num, second_num, hour, minute, seconds)
                        else:
                            # International format: first_num is day, second_num is month
                            datetime_obj = datetime(year, second_num, first_num, hour, minute, seconds)
                    except ValueError:
                        # Skip invalid dates
                        pass

                    if datetime_obj:
                        # Check if this is an initiation (first message after 12+ hours)
                        if last_message_time is None or (datetime_obj - last_message_time) >= timedelta(hours=12):
                            speaker_initiations[speaker] += 1
                            initiation_timeline_data[speaker].append(datetime_obj)

                        last_message_time = datetime_obj
                        date_obj = datetime_obj.replace(hour=0, minute=0, second=0, microsecond=0)  # Date only for timeline compatibility
                        word_count = len(message.split())  # Count words in message

                        # Detect message types (can be multiple)
                        msg_types = detect_message_type(message)

                        # Extract emojis if present
                        emojis = extract_emojis(message)
                        if emojis:
                            speaker_emojis[speaker].extend(emojis)

                        message_dates.append(date_obj)
                        messages_by_year[year].append(message)
                        all_messages.append(message)
                        speakers[speaker] += 1

                        # Track message types for this speaker (a message can have multiple types)
                        for msg_type in msg_types:
                            speaker_message_types[speaker][msg_type] += 1

                        # Store timeline data for speaker
                        speaker_timeline_data[speaker].append((date_obj, message, word_count))
                break

    return all_messages, messages_by_year, speakers, message_dates, speaker_timeline_data, speaker_message_types, speaker_emojis, speaker_initiations, initiation_timeline_data


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

    # Common across all languages (chat slang/text speak)
    common_stopwords = {
        'media', 'omitted', 'media omitted',
        'oki', 'okii', 'okiii',
        'gl', 'im', 'tho',
        'yes', 'yess', 'yesss', 'yep', 'ye',
        'nope', 'nah', 'noo', 'nooo', 'noooo',
        'thing', 'things', 'anyway',
        'actually', 'really',
        'go', 'goo', 'tell',
        'ohh', 'mmm',
        'lemme',
        'one', 'two',
        'lot', 'around',
        'hahahaha', 'hahah',
        'yeah', 'dont', 'didnt', 'don',
        'see', 'always', 'though', 'something',
        'kay', 'ask', 'back', 'even', 'let', 'amp'
    }
    stopwords.update(common_stopwords)

    if language == "English":
        english_stopwords = {
            # Articles
            'an', 'the',
            # Pronouns
            'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
            'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'themselves',
            'this', 'that', 'these', 'those',
            'something', 'someone', 'somewhere', 'somehow',
            'everything', 'everyone', 'everywhere',
            'nothing', 'nobody', 'nowhere',
            'anything', 'anyone', 'anywhere',
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
            'here', 'there', 'yes', 'no', 'not', 'maybe', 'probably', 'actually', 'basically',
            # Common verbs
            'get', 'got', 'going', 'go', 'went', 'gone',
            'like', 'liked', 'liking',
            'know', 'knew', 'known', 'knowing',
            'think', 'thought', 'thinking',
            'see', 'saw', 'seen', 'seeing',
            'want', 'wanted', 'wanting',
            'make', 'made', 'making',
            'tell', 'told', 'telling',
            'give', 'gave', 'given', 'giving',
            'come', 'came', 'coming',
            'take', 'took', 'taken', 'taking',
            'look', 'looked', 'looking',
            'find', 'found', 'finding',
            'use', 'used', 'using',
            'feel', 'felt', 'feeling',
            'try', 'tried', 'trying',
            'keep', 'kept', 'keeping',
            'let', 'lets', 'letting',
            'mean', 'means', 'meant', 'meaning',
            'say', 'said', 'saying', 'says',
            # Informal/chat
            'oh', 'ok', 'okay', 'yeah', 'yep', 'nah', 'haha', 'lol',
            'gonna', 'wanna', 'gotta', 'dunno',
            "https"
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
            'qualcosa', 'qualcuno', 'qualche',
            'niente', 'nulla', 'nessuno',
            # Verbs (essere, avere, fare)
            'è', 'sono', 'sei', 'siamo', 'siete', 'era', 'erano', 'ero', 'essere', 'stato', 'stata', 'stati', 'state',
            'ho', 'hai', 'ha', 'abbiamo', 'avete', 'hanno', 'avere', 'aveva', 'avevano', 'avuto',
            'faccio', 'fai', 'fa', 'facciamo', 'fate', 'fanno', 'fare', 'fatto', 'fatta',
            'va', 'vai', 'vado', 'andiamo', 'andate', 'vanno', 'andare', 'andato',
            'può', 'puoi', 'posso', 'possiamo', 'potete', 'possono', 'potere', 'potuto',
            'devo', 'devi', 'deve', 'dobbiamo', 'dovete', 'devono', 'dovere', 'dovuto',
            'vuoi', 'vuole', 'voglio', 'vogliamo', 'volete', 'vogliono', 'volere', 'voluto',
            'dico', 'dici', 'dice', 'diciamo', 'dite', 'dicono', 'dire', 'detto',
            'vedo', 'vedi', 'vede', 'vediamo', 'vedete', 'vedono', 'vedere', 'visto',
            'vengo', 'vieni', 'viene', 'veniamo', 'venite', 'vengono', 'venire', 'venuto',
            'do', 'dai', 'dà', 'diamo', 'date', 'danno', 'dare', 'dato',
            'so', 'sai', 'sa', 'sappiamo', 'sapete', 'sanno', 'sapere', 'saputo',
            'sto', 'stai', 'sta', 'stiamo', 'state', 'stanno', 'stare', 'stato', 'stavo',
            'pensavo',
            # Prepositions
            'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'del', 'al', 'dal', 'nel', 'col', 'sul',
            'dello', 'alla', 'dalla', 'nella', 'sulla', 'dei', 'agli', 'dai', 'nei', 'sui', "ai", "al", 'della',
            'alle', 'fino', 'senza', 'dell',
            # Conjunctions
            'e', 'ed', 'o', 'od', 'ma', 'però', 'se', 'perché', 'perchè', 'perche', 'quando', 'come', 'mentre', 'dove',
            'anche', 'ancora', 'quindi', 'allora', 'però',
            # Common adverbs
            'non', 'più', 'molto', 'poco', 'tanto', 'così', 'cosi', 'già', 'mai', 'sempre', 'solo', 'quasi', 'proprio',
            'qui', 'qua', 'lì', "li", 'là', 'sì', 'si', 'no', 'quanto',
            'altro', 'altra', 'altri', 'altre',
            'meno', 'infatti', 'ora', 'oggi', 'ieri', 'prima', 'pare', 'dopo',
            'ogni', 'due', 'nono',
            # Other common words
            'cosa', 'cose', 'tutto', 'tutti', 'tutte',
            'ah', 'oh', 'eh', 'boh', 'ok', 'okay', 'haha', 'ahah', 'ahh', 'ahhh', 'hahaha',
            "sa", "ce", "https", "ne", "c'è", "c'era", "ad", "hihi", "cmq", "l'ho", "lho", "xo",
            'co', 'sia', 'lol', 'poi', 'pure', "po'", 'po',
            'comunque', 'xke', 'beh', 'html',
            'tipo', 'vabbe', 'sacco', 'preso', 'avevo',
            'cioè', 'cioe',
            # Media omitted translations
            'file', 'allegato', 'file allegato'
        }
        stopwords.update(italian_stopwords)

    elif language == "Spanish":
        spanish_stopwords = {
            # Articles
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            # Pronouns
            'yo', 'tú', 'él', 'ella', 'nosotros', 'nosotras', 'vosotros', 'vosotras', 'ellos', 'ellas',
            'me', 'te', 'se', 'nos', 'os', 'le', 'les', 'lo', 'la',
            'mi', 'mis', 'tu', 'tus', 'su', 'sus', 'nuestro', 'nuestra', 'nuestros', 'nuestras',
            'vuestro', 'vuestra', 'vuestros', 'vuestras',
            'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas',
            'que', 'quien', 'quienes', 'cual', 'cuales', 'cuál', 'cuáles',
            'algo', 'alguien', 'algún', 'alguna', 'algunos', 'algunas',
            'nada', 'nadie', 'ningún', 'ninguna', 'ningunos', 'ningunas',
            # Verbs (ser, estar, haber, hacer)
            'soy', 'eres', 'es', 'somos', 'sois', 'son', 'ser', 'era', 'eras', 'éramos', 'eran', 'sido',
            'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'estar', 'estaba', 'estado',
            'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'haber', 'había', 'habías', 'habían', 'habido',
            'hago', 'haces', 'hace', 'hacemos', 'hacéis', 'hacen', 'hacer', 'hecho',
            'voy', 'vas', 'va', 'vamos', 'vais', 'van', 'ir', 'ido', 'yendo',
            'puedo', 'puedes', 'puede', 'podemos', 'podéis', 'pueden', 'poder', 'podido',
            'debo', 'debes', 'debe', 'debemos', 'debéis', 'deben', 'deber', 'debido',
            'quiero', 'quieres', 'quiere', 'queremos', 'queréis', 'quieren', 'querer', 'querido',
            'digo', 'dices', 'dice', 'decimos', 'decís', 'dicen', 'decir', 'dicho',
            'veo', 'ves', 've', 'vemos', 'veis', 'ven', 'ver', 'visto',
            'vengo', 'vienes', 'viene', 'venimos', 'venís', 'vienen', 'venir', 'venido',
            'doy', 'das', 'da', 'damos', 'dais', 'dan', 'dar', 'dado',
            'sé', 'sabes', 'sabe', 'sabemos', 'sabéis', 'saben', 'saber', 'sabido',
            # Prepositions
            'de', 'del', 'a', 'al', 'en', 'con', 'por', 'para', 'sin', 'sobre', 'entre', 'desde', 'hasta', 'hacia',
            # Conjunctions
            'y', 'e', 'o', 'u', 'pero', 'sino', 'si', 'porque', 'aunque', 'cuando', 'como', 'donde', 'mientras',
            'también', 'tampoco', 'entonces', 'pues',
            # Common adverbs
            'no', 'más', 'muy', 'poco', 'mucho', 'tanto', 'así', 'ya', 'nunca', 'siempre', 'solo', 'sólo', 'casi',
            'aquí', 'ahí', 'allí', 'acá', 'allá', 'sí',
            'todavía', 'aún',
            'otro', 'otra', 'otros', 'otras',
            # Other common words
            'qué', 'cosa', 'cosas', 'todo', 'todos', 'todas',
            'ah', 'oh', 'eh', 'ok', 'okay', 'jaja', 'jeje', 'jajaja', 'jajajaja', "https",
            # Media omitted translations
            'archivo', 'adjunto', 'archivo adjunto', 'multimedia'
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
