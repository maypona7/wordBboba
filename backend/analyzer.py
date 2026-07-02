from collections import Counter
from dataclasses import dataclass

from kiwipiepy import Kiwi

NOUN_POS_PREFIXES = ("NNG",)

_kiwi: Kiwi | None = None


def get_kiwi() -> Kiwi:
    global _kiwi
    if _kiwi is None:
        _kiwi = Kiwi()
    return _kiwi


def is_noun(pos: str, form: str) -> bool:
    if not any(pos.startswith(p) for p in NOUN_POS_PREFIXES):
        return False
    if len(form) < 2:
        return False
    return True


@dataclass
class WordResult:
    word: str
    count: int
    ratio: float


@dataclass
class AnalyzeResult:
    words: list[WordResult]
    total_tokens: int
    unique_words: int


def analyze_text(text: str, min_count: int = 2, top_n: int = 20) -> AnalyzeResult:
    kiwi = get_kiwi()
    tokens: list[str] = []

    for token in kiwi.tokenize(text):
        if is_noun(token.tag, token.form):
            tokens.append(token.form)

    counts = Counter(tokens)
    total_tokens = len(tokens)
    unique_words = len(counts)

    filtered = [(word, count) for word, count in counts.items() if count >= min_count]
    sorted_words = sorted(filtered, key=lambda x: (-x[1], x[0]))[:top_n]

    words = [
        WordResult(
            word=word,
            count=count,
            ratio=round(count / total_tokens, 4) if total_tokens > 0 else 0.0,
        )
        for word, count in sorted_words
    ]

    return AnalyzeResult(words=words, total_tokens=total_tokens, unique_words=unique_words)
