"""Text processing helpers."""

import re


def tokenize_sentence(sentence: str) -> list[str]:
    """Split text into words and individual punctuation or symbol tokens.

    Preserve spelling and Romanian diacritics, and discard whitespace. Hyphens
    and Unicode dashes are separate tokens even when they connect words.

    >>> tokenize_sentence("S-a dus—repede!")
    ['S', '-', 'a', 'dus', '—', 'repede', '!']
    """
    return re.findall(r"[^\W_]+|\S", sentence)
