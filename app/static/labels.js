export const STATUSES = {
  cubierto: "Cubierto",
  parcial: "Parcial",
  sin_evidencia: "Sin evidencia",
};

export const VERDICTS = {
  equivalencia_total: {
    tone: "ok",
    title: "Equivalencia total propuesta",
    detail: "Todos los temas de la materia de destino tienen un equivalente en el programa de origen.",
  },
  equivalencia_parcial: {
    tone: "mid",
    title: "Equivalencia parcial propuesta",
    detail: "Más del 50% del programa de destino tiene equivalente (art. 87). El docente define los temas a rendir (art. 88).",
  },
  evidencia_insuficiente: {
    tone: "bad",
    title: "Evidencia insuficiente",
    detail: "La cobertura no supera el 50% del programa de destino (art. 87). No alcanza para proponer una equivalencia.",
  },
};

export const PENDING_TITLES = {
  equivalencia_parcial: "Temas a rendir propuestos",
  evidencia_insuficiente: "Temas sin cubrir",
};

export const EXAMPLE = {
  source: "Unidad 1: Tipos de datos simples, variables y expresiones.\nUnidad 2: Estructuras condicionales y repetitivas.\nUnidad 3: Subprogramas y pasaje de parámetros.\nUnidad 4: Arreglos y matrices.\nUnidad 5: Listas, pilas y colas como tipos abstractos de datos.\nUnidad 6: Algoritmos de búsqueda y ordenamiento.",
  target: "Variables, tipos de datos y operadores. Estructuras de control, condicionales y bucles. Funciones y modularización. Arreglos y objetos. Manipulación del modelo de objetos del documento (DOM). Programación asincrónica y eventos. Tipos de Datos Abstractos: pilas, colas y listas. Introducción a pruebas unitarias.",
};
