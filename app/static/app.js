import { analyze, getLimits, recompute } from "./api.js";
import { $ } from "./dom.js";
import { createField } from "./fields.js";
import { EXAMPLE } from "./labels.js";
import { limits } from "./limits.js";
import { clearNotice, notify } from "./notices.js";
import { filterReport, matchesWithStatus, renderReport, renderTopics, reportText } from "./report.js";

const fields = {
  source: createField($("fieldSource"), "Pegá o subí el programa de la materia aprobada."),
  target: createField($("fieldTarget"), "Pegá o subí el programa de la materia a reconocer."),
};

const setBusy = (busy) => {
  $("submit").disabled = busy;
  $("form").setAttribute("aria-busy", String(busy));
  if (busy) notify("info", "La IA lee los dos programas y razona cada tema. Puede tardar varios minutos, sobre todo la primera vez que carga el modelo.", { title: "Analizando" });
};

const submit = async (event) => {
  event.preventDefault();
  const checks = Object.values(fields).map((field) => field.validate());
  if (!checks.every(Boolean)) {
    notify("warning", "Completá los dos programas para generar el informe.", { title: "Faltan datos" });
    return Object.values(fields).find((field) => !field.value()).focus();
  }
  setBusy(true);
  try {
    const report = await analyze({ source: fields.source.value(), target: fields.target.value() });
    clearNotice();
    renderReport(report);
  } catch (failure) {
    notify("error", failure.message, { title: "No se pudo generar el informe" });
  } finally {
    $("submit").disabled = false;
    $("form").setAttribute("aria-busy", "false");
  }
};

const copy = async () => {
  try {
    await navigator.clipboard.writeText(reportText());
    notify("success", "El informe quedó copiado al portapapeles.", { title: "Copiado", ttl: 4000 });
  } catch {
    notify("error", "El navegador no permitió copiar. Usá la opción de imprimir o seleccioná el texto.", { title: "No se pudo copiar" });
  }
};

const announceEngine = ({ model, model_ready: ready }) => {
  $("engine").textContent = ready ? `IA local lista: ${model}.` : `IA local no disponible: ${model}.`;
  if (!ready) {
    notify("warning", `Comprobá que Ollama esté abierto y ejecutá: ollama pull ${model}`, { title: "Falta el modelo de IA" });
  }
};

const adjust = async (event) => {
  const select = event.target.closest(".status-select");
  if (!select) return;
  try {
    renderReport(await recompute(matchesWithStatus(Number(select.dataset.index), select.value)), { scroll: false });
  } catch (failure) {
    renderTopics();
    notify("error", failure.message, { title: "No se pudo recalcular" });
  }
};

const loadLimits = async () => {
  try {
    const remote = await getLimits();
    Object.assign(limits, { maxChars: remote.max_chars, maxFileBytes: remote.max_file_bytes });
    Object.values(fields).forEach((field) => field.refresh());
    announceEngine(remote);
  } catch (failure) {
    notify("error", failure.message, { title: "Sin conexión con el servidor" });
  }
};

$("form").addEventListener("submit", submit);
$("example").addEventListener("click", () => {
  fields.source.set(EXAMPLE.source);
  fields.target.set(EXAMPLE.target);
  clearNotice();
});
$("clear").addEventListener("click", () => {
  Object.values(fields).forEach((field) => field.set(""));
  clearNotice();
});
$("copy").addEventListener("click", copy);
$("topics").addEventListener("change", adjust);
$("print").addEventListener("click", () => window.print());
$("filters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-filter]");
  if (button) filterReport(button.dataset.filter);
});

loadLimits();
