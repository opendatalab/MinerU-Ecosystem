"""MinerU supported language strings."""

import re
from typing import List

_other_lang = [
    'ch (Chinese, English, Chinese Traditional)',
    'ch_lite (Chinese, English, Chinese Traditional, Japanese)',
    'ch_server (Chinese, English, Chinese Traditional, Japanese)',
    'en (English)',
    'korean (Korean, English)',
    'japan (Chinese, English, Chinese Traditional, Japanese)',
    'chinese_cht (Chinese, English, Chinese Traditional, Japanese)',
    'ta (Tamil, English)',
    'te (Telugu, English)',
    'ka (Kannada)',
    'el (Greek, English)',
    'th (Thai, English)',
]

_add_lang = [
    (
        'latin (French, German, Afrikaans, Italian, Spanish, Bosnian, Portuguese, Czech, Welsh, '
        'Danish, Estonian, Irish, Croatian, Uzbek, Hungarian, Serbian (Latin), Indonesian, '
        'Occitan, Icelandic, Lithuanian, Maori, Malay, Dutch, Norwegian, Polish, Slovak, '
        'Slovenian, Albanian, Swedish, Swahili, Tagalog, Turkish, Latin, Azerbaijani, Kurdish, '
        'Latvian, Maltese, Pali, Romanian, Vietnamese, Finnish, Basque, Galician, Luxembourgish, '
        'Romansh, Catalan, Quechua)'
    ),
    'arabic (Arabic, Persian, Uyghur, Urdu, Pashto, Kurdish, Sindhi, Balochi, English)',
    'east_slavic (Russian, Belarusian, Ukrainian, English)',
    (
        'cyrillic (Russian, Belarusian, Ukrainian, Serbian (Cyrillic), Bulgarian, Mongolian, '
        'Abkhazian, Adyghe, Kabardian, Avar, Dargin, Ingush, Chechen, Lak, Lezgin, Tabasaran, '
        'Kazakh, Kyrgyz, Tajik, Macedonian, Tatar, Chuvash, Bashkir, Malian, Moldovan, Udmurt, '
        'Komi, Ossetian, Buryat, Kalmyk, Tuvan, Sakha, Karakalpak, English)'
    ),
    (
        'devanagari (Hindi, Marathi, Nepali, Bihari, Maithili, Angika, Bhojpuri, Magahi, '
        'Santali, Newari, Konkani, Sanskrit, Haryanvi, English)'
    ),
]

ALL_LANGUAGES: List[str] = [*_other_lang, *_add_lang]

# prefix (the code before the first space) → full language string
_PREFIX_MAP: dict = {s.split(" (")[0]: s for s in ALL_LANGUAGES}


def resolve_language(name: str) -> str:
    """Map a language name to the SDK prefix code.

    Searches ALL_LANGUAGES for the first entry whose prefix or parenthetical
    language list contains *name* as a whole word (case-insensitive).

    Examples::

        resolve_language("Chinese")    -> "ch"
        resolve_language("Korean")     -> "korean"
        resolve_language("Tamil")      -> "ta"
        resolve_language("Macedonian") -> "cyrillic"
        resolve_language("French")     -> "latin"
        resolve_language("ch")         -> "ch"   # prefix pass-through

    Falls back to the input unchanged when no match is found.
    """
    key = name.strip()
    key_lower = key.lower()

    for lang_str in ALL_LANGUAGES:
        prefix = lang_str.split(" (")[0]
        if key_lower == prefix.lower():
            return prefix
        if re.search(r'\b' + re.escape(key_lower) + r'\b', lang_str.lower()):
            return prefix

    return key


def get_language_list() -> List[str]:
    """Return all supported language strings."""
    return ALL_LANGUAGES
