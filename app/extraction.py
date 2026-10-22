import re
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Protocol

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.errors import AppError
from app.sanitize import clean_input

NEW_TOPIC = re.compile(r"^(\d+[.)]|[•*·]|unidad|tema|m[oó]dulo)", re.IGNORECASE)
SENTENCE_END = (".", ";", ":", "?", "!")
EDGE_LINES = 3
MIN_HEADER_LENGTH = 20
PRIVATE_USE = re.compile(r"[\uf000-\uf8ff]")
ACTIVE_PDF = re.compile(rb"/(JavaScript|Launch|EmbeddedFile|RichMedia)\b")
ACTIVE_ACTIONS = {"/JavaScript", "/Launch"}
UNSAFE_MEMBERS = ("vbaproject.bin", "/activex/")
MAX_ARCHIVE_MEMBERS = 2000
PARSE_ERRORS = (PyPdfError, PackageNotFoundError, zipfile.BadZipFile, KeyError, ValueError, TypeError, OSError)


class ExtractionError(AppError):
    pass


class TextExtractor(Protocol):
    label: str
    signature: bytes

    def extract(self, data: bytes) -> str: ...


def corrupt(label: str) -> ExtractionError:
    return ExtractionError(
        "corrupt_file",
        f"El archivo no es un {label} válido. Puede estar dañado o tener otra extensión.",
        422,
    )


def unsafe(label: str) -> ExtractionError:
    return ExtractionError(
        "unsafe_file",
        f"El {label} contiene elementos activos o una estructura no segura (scripts, macros o adjuntos) y no se procesa. "
        "Guardalo de nuevo como un archivo limpio o pegá el texto.",
        422,
    )


def is_unsafe_member(name: str) -> bool:
    lowered = name.lower()
    parts = lowered.replace("\\", "/").split("/")
    return lowered.startswith(("/", "\\")) or ".." in parts or any(marker in f"/{lowered}" for marker in UNSAFE_MEMBERS)


def check_archive(data: bytes, max_unzipped: int, label: str) -> None:
    members = zipfile.ZipFile(BytesIO(data)).infolist()
    expanded = sum(member.file_size for member in members)
    if len(members) > MAX_ARCHIVE_MEMBERS or expanded > max_unzipped or any(is_unsafe_member(m.filename) for m in members):
        raise unsafe(label)


def has_active_content(reader: PdfReader) -> bool:
    root = reader.trailer["/Root"]
    names = root.get("/Names")
    if names is not None and any(key in names.get_object() for key in ("/JavaScript", "/EmbeddedFiles")):
        return True
    action = root.get("/OpenAction")
    resolved = action.get_object() if action is not None else None
    return hasattr(resolved, "get") and resolved.get("/S") in ACTIVE_ACTIONS


def unwrap_lines(text: str) -> str:
    merged: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if merged and not merged[-1].endswith(SENTENCE_END) and not NEW_TOPIC.match(line):
            merged[-1] = f"{merged[-1]} {line}"
        else:
            merged.append(line)
    return "\n".join(merged)


def line_shape(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


def edge_positions(size: int) -> set[int]:
    return set(range(min(EDGE_LINES, size))) | set(range(max(size - EDGE_LINES, 0), size))


def strip_repeated(pages: list[list[str]]) -> list[list[str]]:
    if len(pages) < 2:
        return pages
    edges = [edge_positions(len(page)) for page in pages]
    seen = [
        {line_shape(page[i]) for i in positions if len(page[i].strip()) >= MIN_HEADER_LENGTH}
        for page, positions in zip(pages, edges)
    ]
    counts = Counter(shape for shapes in seen for shape in shapes)
    limit = max(2, len(pages) // 2)
    repeated = {shape for shape, total in counts.items() if total >= limit}
    return [
        [line for index, line in enumerate(page) if not (index in positions and line_shape(line) in repeated)]
        for page, positions in zip(pages, edges)
    ]


def clean(text: str) -> str:
    plain = PRIVATE_USE.sub("", clean_input(text))
    lines = (" ".join(line.split()) for line in plain.splitlines())
    return "\n".join(line for line in lines if line)


class PdfExtractor:
    label = "PDF"
    signature = b"%PDF-"

    def __init__(self, max_pages: int) -> None:
        self._max_pages = max_pages

    def extract(self, data: bytes) -> str:
        if ACTIVE_PDF.search(data):
            raise unsafe(self.label)
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted and not reader.decrypt(""):
                raise ExtractionError(
                    "protected_file",
                    "El PDF está protegido con contraseña. Quitá la protección y volvé a subirlo.",
                    422,
                )
            self._check_reader(reader)
            pages = [(page.extract_text() or "").splitlines() for page in reader.pages]
        except ExtractionError:
            raise
        except PARSE_ERRORS as error:
            raise corrupt(self.label) from error
        return unwrap_lines("\n".join(line for page in strip_repeated(pages) for line in page))

    def _check_reader(self, reader: PdfReader) -> None:
        if len(reader.pages) > self._max_pages:
            raise ExtractionError(
                "too_many_pages",
                f"El PDF tiene {len(reader.pages)} páginas y el máximo es {self._max_pages}. Subí solo el programa de la materia.",
                413,
            )
        if has_active_content(reader):
            raise unsafe(self.label)


class DocxExtractor:
    label = "documento de Word"
    signature = b"PK\x03\x04"

    def __init__(self, max_unzipped: int) -> None:
        self._max_unzipped = max_unzipped

    def extract(self, data: bytes) -> str:
        try:
            check_archive(data, self._max_unzipped, self.label)
            document = Document(BytesIO(data))
            blocks = [self._block(item) for item in document.iter_inner_content()]
        except PARSE_ERRORS as error:
            raise corrupt(self.label) from error
        return "\n".join(blocks)

    def _block(self, item) -> str:
        if isinstance(item, Table):
            return "\n".join(self._row(row) for row in item.rows)
        return item.text

    def _row(self, row) -> str:
        cells: list[str] = []
        for cell in row.cells:
            text = cell.text.strip()
            if text and (not cells or cells[-1] != text):
                cells.append(text)
        return ". ".join(cells)


class DocumentReader:
    def __init__(self, max_bytes: int, max_chars: int, max_pages: int = 100, max_unzipped: int = 30 * 1048576) -> None:
        self._max_bytes = max_bytes
        self._max_chars = max_chars
        self._extractors: dict[str, TextExtractor] = {
            ".pdf": PdfExtractor(max_pages),
            ".docx": DocxExtractor(max_unzipped),
        }

    def read(self, filename: str, data: bytes) -> str:
        extractor = self._extractor_for(filename)
        self._check_size(data)
        if not data.startswith(extractor.signature):
            raise corrupt(extractor.label)
        return self._check_text(clean(extractor.extract(data)))

    def _extractor_for(self, filename: str) -> TextExtractor:
        suffix = Path(filename).suffix.lower()
        if suffix == ".doc":
            raise ExtractionError(
                "legacy_doc",
                "Los archivos .doc antiguos no se pueden leer. Abrilo en Word y guardalo como .docx.",
                415,
            )
        if suffix not in self._extractors:
            shown = suffix or "sin extensión"
            raise ExtractionError(
                "unsupported_type",
                f"Solo se aceptan archivos PDF o Word (.docx). El archivo recibido es {shown}.",
                415,
            )
        return self._extractors[suffix]

    def _check_size(self, data: bytes) -> None:
        if not data:
            raise ExtractionError("empty_file", "El archivo está vacío.", 422)
        if len(data) > self._max_bytes:
            limit = self._max_bytes / 1048576
            raise ExtractionError("file_too_large", f"El archivo supera el máximo de {limit:g} MB.", 413)

    def _check_text(self, text: str) -> str:
        if not text:
            raise ExtractionError(
                "no_text",
                "No se encontró texto en el archivo. Si es un PDF escaneado, usá la versión en Word o pegá el texto.",
                422,
            )
        if len(text) > self._max_chars:
            raise ExtractionError(
                "text_too_long",
                f"El documento tiene {len(text)} caracteres y el máximo es {self._max_chars}. "
                "Subí solo el programa de la materia.",
                413,
            )
        return text
