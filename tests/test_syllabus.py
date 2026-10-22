from app.syllabus import split_topics


def test_splits_sentences_and_removes_unit_headers():
    topics = split_topics("Unidad 1: Variables y tipos.\nUnidad 2: Bucles; funciones.")
    assert [topic.text for topic in topics] == ["Variables y tipos", "Bucles", "funciones"]


def test_ignores_fragments_that_are_too_short():
    assert split_topics("a. Arreglos.")[0].text == "Arreglos"
