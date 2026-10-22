import re
import unicodedata

HIDDEN_CHARACTERS = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff\u00ad]")
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
PROMPT_TAGS = re.compile(r"</?\s*(programa|origen|destino)\s*>", re.IGNORECASE)
INJECTION = re.compile(
    r"(ignor[aáeé]\w*|olvid[aáeé]\w*|desobedec\w*|omit[ií]\w*)\s+(todas?\s+)?(las\s+|tus\s+|esas\s+)?(instrucciones|reglas|indicaciones)"
    r"|ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier)"
    r"|disregard\s+(all\s+|the\s+)?(previous|prior|above)"
    r"|(system|developer)\s+prompt|prompt\s+del\s+sistema"
    r"|(marc[aá]|clasific[aá]|evalu[aá]|respond[eé]|devolv[eé])\w*\s+(todos?|todas?)\s+(los\s+|las\s+)?(temas?\s+)?(como\s+)?(cubiert|equivalent|aprobad)"
    r"|(mark|label|classify|rate)\s+(all|every)\s+\w*\s*(as\s+)?(covered|equivalent)"
    r"|act[uú]a\s+como|you\s+are\s+now|ahora\s+sos\s+un|nuevas\s+instrucciones|new\s+instructions",
    re.IGNORECASE,
)


def clean_input(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    visible = CONTROL_CHARACTERS.sub("", HIDDEN_CHARACTERS.sub("", normalized))
    return PROMPT_TAGS.sub("", visible)


def looks_like_injection(text: str) -> bool:
    return INJECTION.search(text) is not None


def safe_filename(name: str, limit: int = 120) -> str:
    base = re.split(r"[\\/]", name)[-1]
    visible = CONTROL_CHARACTERS.sub("", HIDDEN_CHARACTERS.sub("", base)).strip()
    return visible[:limit]
