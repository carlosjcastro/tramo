import pytest

from app.extraction import DocumentReader, ExtractionError, unwrap_lines
from tests.documents import make_blank_pdf, make_docx, make_pdf

reader = DocumentReader(max_bytes=50_000, max_chars=200)


def code_of(filename: str, data: bytes) -> str:
    with pytest.raises(ExtractionError) as caught:
        reader.read(filename, data)
    return caught.value.code


def test_reads_docx_paragraphs_and_tables_in_order():
    data = make_docx(["Unidad 1: Variables."], [["Unidad 2", "Bucles"], ["Unidad 3", "Funciones"]])
    assert reader.read("programa.docx", data) == "Unidad 1: Variables.\nUnidad 2. Bucles\nUnidad 3. Funciones"


def test_reads_pdf_text():
    assert "Arreglos y matrices" in reader.read("programa.pdf", make_pdf(["Arreglos y matrices."]))


def test_unwraps_lines_that_were_broken_by_the_page():
    text = "Tipos de datos y\noperadores.\nUnidad 2: Bucles"
    assert unwrap_lines(text) == "Tipos de datos y operadores.\nUnidad 2: Bucles"


@pytest.mark.parametrize(
    ("filename", "data", "code"),
    [pytest.param(*case, id=f"{case[2]}-{index}") for index, case in enumerate([
        ("programa.txt", b"hola", "unsupported_type"),
        ("programa.doc", b"hola", "legacy_doc"),
        ("programa", b"hola", "unsupported_type"),
        ("programa.pdf", b"", "empty_file"),
        ("programa.pdf", b"x" * 60_000, "file_too_large"),
        ("programa.pdf", b"no es un pdf", "corrupt_file"),
        ("programa.docx", b"PK\x03\x04roto", "corrupt_file"),
        ("programa.pdf", make_blank_pdf(), "no_text"),
        ("programa.docx", make_docx(["x" * 300]), "text_too_long"),
    ])],
)
def test_rejects_invalid_files_with_a_specific_code(filename, data, code):
    assert code_of(filename, data) == code


def test_removes_headers_that_repeat_across_pages():
    pages = [
        ["Universidad Nacional Página 1", "Variables y tipos"],
        ["Universidad Nacional Página 2", "Bucles"],
        ["Universidad Nacional Página 3", "Funciones"],
    ]
    from app.extraction import strip_repeated

    assert strip_repeated(pages) == [["Variables y tipos"], ["Bucles"], ["Funciones"]]


def test_keeps_repeated_words_that_are_not_at_the_page_edges():
    from app.extraction import strip_repeated

    fragments = ["Estructuras", "de", "datos", "y", "algoritmos", "eficientes", "en", "la", "resolución", "de", "problemas"]
    pages = [list(fragments) for _ in range(4)]
    assert strip_repeated(pages) == pages