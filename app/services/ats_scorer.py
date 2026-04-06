import re
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Common words to ignore in keyword extraction
_STOP_WORDS = "english"

# ATS-unfriendly patterns to detect
_ATS_ISSUE_PATTERNS = [
    (r"[^\x00-\x7F]", "Non-ASCII characters detected — may confuse ATS parsers"),
    (r"\|", "Pipe characters used — may indicate table formatting that ATS can't parse"),
    (r"^#{1,6}\s", "Markdown headers detected — use plain text section titles"),
]


def score_resume(resume_text: str, jd_text: str) -> dict:
    """
    Compute ATS match score, missing/present keywords, and formatting issues.

    Returns:
        {
            "match_score": int (0-100),
            "missing_keywords": List[str],
            "present_keywords": List[str],
            "ats_issues": List[str],
        }
    """
    match_score = _compute_similarity(resume_text, jd_text)
    jd_keywords = _extract_keywords(jd_text)
    resume_lower = resume_text.lower()

    present = [kw for kw in jd_keywords if kw.lower() in resume_lower]
    missing = [kw for kw in jd_keywords if kw.lower() not in resume_lower]
    ats_issues = _detect_ats_issues(resume_text)

    return {
        "match_score": match_score,
        "present_keywords": present[:30],
        "missing_keywords": missing[:30],
        "ats_issues": ats_issues,
    }


def _compute_similarity(text_a: str, text_b: str) -> int:
    vectorizer = TfidfVectorizer(stop_words=_STOP_WORDS, ngram_range=(1, 2))
    try:
        tfidf = vectorizer.fit_transform([text_a, text_b])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(score) * 100)
    except Exception:
        return 0


def _extract_keywords(text: str, top_n: int = 40) -> List[str]:
    """Extract top TF-IDF keywords from a single document."""
    vectorizer = TfidfVectorizer(
        stop_words=_STOP_WORDS,
        ngram_range=(1, 2),
        max_features=top_n,
    )
    try:
        vectorizer.fit([text])
        return list(vectorizer.get_feature_names_out())
    except Exception:
        # Fallback: simple word frequency
        words = re.findall(r"\b[a-zA-Z][a-zA-Z+#\.]{2,}\b", text)
        freq: dict = {}
        for w in words:
            freq[w.lower()] = freq.get(w.lower(), 0) + 1
        return sorted(freq, key=freq.get, reverse=True)[:top_n]  # type: ignore


def _detect_ats_issues(resume_text: str) -> List[str]:
    issues = []
    for pattern, message in _ATS_ISSUE_PATTERNS:
        if re.search(pattern, resume_text, re.MULTILINE):
            issues.append(message)
    if len(resume_text) < 200:
        issues.append("Resume text is very short — ensure the file parsed correctly")
    return issues
