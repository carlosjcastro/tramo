const VERDICTS = {
  equivalencia_total: "Equivalencia total propuesta",
  equivalencia_parcial: "Equivalencia parcial propuesta. El docente define los temas a rendir (art. 88)",
  evidencia_insuficiente: "Evidencia insuficiente. La cobertura no supera el 50% (art. 87)",
};
const STATUS_LABELS = { cubierto: "Cubierto", parcial: "Parcial", sin_evidencia: "Sin evidencia" };
const EXAMPLE = {
  source: "Unidad 1: Tipos de datos simples, variables y expresiones.\nUnidad 2: Estructuras condicionales y repetitivas.\nUnidad 3: Subprogramas y pasaje de parámetros.\nUnidad 4: Arreglos y matrices.\nUnidad 5: Listas, pilas y colas como tipos abstractos de datos.\nUnidad 6: Algoritmos de búsqueda y ordenamiento.",
  target: "Variables, tipos de datos y operadores. Estructuras de control, condicionales y bucles. Funciones y modularización. Arreglos y objetos. Manipulación del modelo de objetos del documento (DOM). Programación asincrónica y eventos. Tipos de Datos Abstractos: pilas, colas y listas. Introducción a pruebas unitarias.",
};

const $ = (id) => document.getElementById(id);

const cell = (content) => {
  const td = document.createElement("td");
  td.append(content);
  return td;
};

const badge = (status) => {
  const span = document.createElement("span");
  span.className = `badge ${status}`;
  span.textContent = STATUS_LABELS[status];
  return span;
};

const renderRow = (match) => {
  const tr = document.createElement("tr");
  tr.append(
    cell(match.target.text),
    cell(badge(match.status)),
    cell(match.source ? match.source.text : "Sin fragmento relacionado"),
    cell(match.score.toFixed(2)),
  );
  return tr;
};

const render = (report) => {
  $("coverage").textContent = `${Math.round(report.coverage * 100)}%`;
  $("verdict").textContent = VERDICTS[report.verdict];
  $("rows").replaceChildren(...report.matches.map(renderRow));
  $("result").hidden = false;
};

const request = async (payload) => {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : "No se pudo analizar");
  }
  return response.json();
};

const setBusy = (busy) => {
  $("submit").disabled = busy;
  $("status").textContent = busy ? "Analizando" : "";
};

$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(true);
  try {
    render(await request({ source: $("source").value, target: $("target").value }));
    setBusy(false);
  } catch (error) {
    setBusy(false);
    $("status").textContent = error.message;
  }
});

$("example").addEventListener("click", () => {
  $("source").value = EXAMPLE.source;
  $("target").value = EXAMPLE.target;
});
