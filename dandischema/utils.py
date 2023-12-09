from __future__ import annotations

import re
from typing import Iterator, List

TITLE_CASE_LOWER = {
    "a",
    "an",
    "and",
    "as",
    "but",
    "by",
    "for",
    "in",
    "nor",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def name2title(name: str) -> str:
    # For use in autopopulating the titles of model schema fields
    words: List[str] = []
    for w in split_camel_case(name):
        w = w.lower()
        if w == "id" or w == "url":
            w = w.upper()
        elif not words or w not in TITLE_CASE_LOWER:
            w = w.capitalize()
        words.append(w)
    return " ".join(words)


def split_camel_case(s: str) -> Iterator[str]:
    last_start = 0
    # Don't split apart "ID":
    for m in re.finditer(r"(?<=I)[A-CE-Z]|(?<=[^I])[A-Z]", s):
        yield s[last_start : m.start()]
        last_start = m.start()
    if last_start < len(s):
        yield s[last_start:]


def version2tuple(ver: str) -> tuple[int, int, int]:
    """Convert version to numeric tuple"""
    if m := re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", ver, flags=re.ASCII):
        return (int(m[1]), int(m[2]), int(m[3]))
    else:
        raise ValueError(r"Version must be well formed: \d+\.\d+\.\d+")


def _ensure_newline(obj: str) -> str:
    if not obj.endswith("\n"):
        return obj + "\n"
    return obj
