import pytest

from app.noise import is_noise


@pytest.mark.parametrize(
    "text",
    [
        "Quinteros, Oscar Lic",
        "Rivas Daniel Armando Lic",
        "https://developer.mozilla.org/es/docs",
        "2026",
        "Cuatrimestral Horas Cuerpo Docente Teórico",
        "Universidad Nacional de Catamarca Facultad de Tecnología",
        "PROGRAMA ANALITICO",
        "Contenidos mínimos",
        "Bibliografía básica",
    ],
)
def test_detects_administrative_noise(text):
    assert is_noise(text)


@pytest.mark.parametrize(
    "text",
    ["Closures y control de estado", "Asincronía", "Código limpio y refactorización", "Árboles binarios de búsqueda"],
)
def test_keeps_real_topics(text):
    assert not is_noise(text)
