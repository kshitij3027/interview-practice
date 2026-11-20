"""Customer text normalization contract."""
import re

_WORD = re.compile(r"[A-Za-z0-9]+")


def tokens(text: str) -> tuple[str, ...]:
    return tuple(match.group().lower() for match in _WORD.finditer(text))
