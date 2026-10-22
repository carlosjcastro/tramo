import re

URL = re.compile(r"https?://|www\.", re.IGNORECASE)
METADATA = re.compile(
    r"carga horaria|r[eé]gimen|cuatrimestral|correlativ|horas (totales|dedicadas|semanales)|"
    r"c[oó]digo (siu|guaran[ií])|a[nñ]o (acad[eé]mico|lectivo)|p[aá]gina \d+|departamento|facultad|"
    r"universidad|cuerpo docente|modalidad de|plan:|carrera:|[aá]rea:",
    re.IGNORECASE,
)
SECTION_LABEL = re.compile(
    r"^(programa anal[ií]tico|contenidos( m[ií]nimos)?|objetivos|fundamentaci[oó]n|metodolog[ií]a|"
    r"evaluaci[oó]n|actividades pr[aá]cticas|plan|[aá]rea|total|r[eé]gimen|bibliograf[ií]a.*)$",
    re.IGNORECASE,
)
PERSON = re.compile(r"\b(lic|ing|mg|dr|dra|prof|esp)\b\.?$", re.IGNORECASE)
MIN_LETTER_RATIO = 0.6


def is_noise(text: str) -> bool:
    letters = sum(char.isalpha() for char in text)
    return bool(
        letters / len(text) < MIN_LETTER_RATIO
        or URL.search(text)
        or METADATA.search(text)
        or SECTION_LABEL.match(text)
        or PERSON.search(text)
    )
