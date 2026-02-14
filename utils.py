"""Shared utility functions for WhatsApp WordCloud app."""
import re
import os
from collections import defaultdict
from wordcloud import WordCloud, STOPWORDS


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
    speakers = defaultdict(int)

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

                speaker = groups[-2].strip()
                message = groups[-1].strip()

                # Skip system messages
                if not any(sys_msg in message.lower() for sys_msg in [
                    'media omitted', 'missed voice call', 'missed video call',
                    'changed the subject', 'changed this group', 'left',
                    'added', 'removed', 'created group'
                ]):
                    messages_by_year[year].append(message)
                    all_messages.append(message)
                    speakers[speaker] += 1
                break

    return all_messages, messages_by_year, speakers


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
