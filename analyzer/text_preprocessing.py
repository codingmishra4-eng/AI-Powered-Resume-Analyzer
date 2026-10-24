"""
Text Preprocessing Module
-------------------------
Handles text cleaning, tokenization, stopword removal, and normalization.
Designed to be beginner-friendly, deterministic, and resilient.
"""

import re
from typing import List, Set

# Comprehensive built-in English stopwords so processing works offline
# and deterministically without requiring external network downloads.
DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "will", "shall", "also", "using", "used"
}

# Try loading NLTK stopwords if downloaded, otherwise fall back to DEFAULT_STOPWORDS
try:
    import nltk
    from nltk.corpus import stopwords as nltk_stopwords
    try:
        STOPWORDS = set(nltk_stopwords.words("english")).union(DEFAULT_STOPWORDS)
    except LookupError:
        STOPWORDS = DEFAULT_STOPWORDS
except ImportError:
    STOPWORDS = DEFAULT_STOPWORDS


def clean_text(raw_text: str) -> str:
    """
    Cleans raw document text by:
    1. Lowercasing all characters.
    2. Replacing URLs and email addresses with empty spaces.
    3. Preserving special technical characters (e.g., 'c++', 'c#', '.net').
    4. Removing extraneous non-alphanumeric punctuation.
    5. Normalizing multiple whitespace characters to a single space.

    Example:
        Input:  "Passionate C++ and Python developer! Email: alex@test.com\\nVisit https://alex.dev"
        Output: "passionate c++ and python developer visit"

    Parameters:
        raw_text (str): Raw string extracted from document or user input.

    Returns:
        str: Cleaned, normalized string.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    text = raw_text.lower()

    # Remove URLs (http, https, www)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses so they do not distort keyword similarity
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", " ", text)

    # Replace special symbols while preserving C++, C#, .NET
    # We temporarily protect these tokens
    text = text.replace("c++", "__cplusplus__")
    text = text.replace("c#", "__csharp__")
    text = text.replace(".net", "__dotnet__")

    # Replace punctuation characters with whitespace
    # Keep alphanumeric characters and spaces
    text = re.sub(r"[^a-zA-Z0-9\s_]", " ", text)

    # Restore protected tokens
    text = text.replace("__cplusplus__", "c++")
    text = text.replace("__csharp__", "c#")
    text = text.replace("__dotnet__", ".net")

    # Collapse multiple whitespace characters into a single space
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_text(text: str) -> List[str]:
    """
    Splits cleaned text into a list of individual words/tokens.

    Example:
        Input:  "fastapi python docker"
        Output: ["fastapi", "python", "docker"]

    Parameters:
        text (str): Cleaned text string.

    Returns:
        List[str]: List of token strings.
    """
    if not text:
        return []

    # Match alphanumeric words, including preserved tech words like c++, c#
    tokens = re.findall(r"\b[a-zA-Z0-9+#.]+\b", text)
    return tokens


def remove_stopwords(tokens: List[str]) -> List[str]:
    """
    Filters out common grammatical words (stopwords) that carry little
    discriminative informational value for semantic matching.

    Example:
        Input:  ["the", "engineer", "builds", "with", "python"]
        Output: ["engineer", "builds", "python"]

    Parameters:
        tokens (List[str]): List of word tokens.

    Returns:
        List[str]: Filtered list of tokens excluding stopwords.
    """
    if not tokens:
        return []

    filtered = [token for token in tokens if token.lower() not in STOPWORDS and len(token) > 1]
    return filtered


def preprocess_for_tfidf(text: str) -> str:
    """
    Complete end-to-end preprocessing pipeline for TF-IDF vectorization:
    cleans the text, tokenizes it, removes stopwords, and joins back into a string.

    Example:
        Input:  "Looking for an experienced Python developer who knows Docker."
        Output: "looking experienced python developer knows docker"

    Parameters:
        text (str): Input text.

    Returns:
        str: Normalized, stopword-free string ready for vectorization.
    """
    cleaned = clean_text(text)
    tokens = tokenize_text(cleaned)
    filtered = remove_stopwords(tokens)
    return " ".join(filtered)
