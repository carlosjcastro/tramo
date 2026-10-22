from app.syllabus import split_topics


def test_splits_sentences_and_removes_unit_headers():
    topics = split_topics("Unidad 1: Variables y tipos.\nUnidad 2: Bucles; funciones.")
    assert [topic.text for topic in topics] == ["Variables y tipos", "Bucles", "funciones"]


def test_ignores_fragments_that_are_too_short():
    assert split_topics("a. Arreglos.")[0].text == "Arreglos"


def test_strips_bullets_numbering_and_private_glyphs():
    topics = split_topics("● Consolidar el dominio\n1.2 Clases en JavaScript\n Closures y estado")
    assert [topic.text for topic in topics] == ["Consolidar el dominio", "Clases en JavaScript", "Closures y estado"]


def test_drops_bibliography_at_the_end_but_keeps_early_mentions():
    text = "Uso de bibliografía técnica. " + "Tema largo de ejemplo. " * 10 + "BIBLIOGRAFÍA Haverbeke, M. Eloquent JavaScript."
    texts = [topic.text for topic in split_topics(text)]
    assert "Uso de bibliografía técnica" in texts
    assert not any("Haverbeke" in item for item in texts)


def test_removes_duplicates_and_metadata():
    topics = split_topics("Arreglos y matrices.\narreglos y matrices.\nUniversidad Nacional de Catamarca.\nHoras dedicadas a Diseño.")
    assert [topic.text for topic in topics] == ["Arreglos y matrices"]


def test_keeps_vs_abbreviation_inside_one_topic_and_drops_trailing_section_numbers():
    topics = split_topics("Sincronía vs. Asincronía.\nTipos de Datos 2.4\nFunciones y parámetros 3.5.")
    assert [topic.text for topic in topics] == ["Sincronía vs. Asincronía", "Tipos de Datos", "Funciones y parámetros"]
