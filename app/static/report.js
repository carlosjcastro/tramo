import { $, el } from "./dom.js";
import { count, percent } from "./format.js";
import { reducedMotion } from "./motion.js";
import { PENDING_TITLES, STATUSES, VERDICTS } from "./labels.js";

const state = { report: null, filter: "todos" };

const tally = (matches) =>
  Object.keys(STATUSES).map((status) => ({
    status,
    total: matches.filter((match) => match.status === status).length,
  }));

const note = (label, text) =>
  el("p", { class: "topic-note" }, el("span", {}, label), text);

const notes = (match) => [
  note(
    "En el origen",
    match.sources.length
      ? match.sources.map((source) => source.text).join(". ")
      : "No se encontró un tema relacionado.",
  ),
  ...(match.reason ? [note("Razonamiento", match.reason)] : []),
];

const option =
  (match) =>
  ([value, label]) =>
    el(
      "option",
      { value, ...(value === match.status ? { selected: "" } : {}) },
      label,
    );

const statusSelect = (match) =>
  el(
    "select",
    {
      class: "status-select",
      "data-index": String(match.target.index),
      "aria-label": `Estado del tema ${match.target.text}`,
    },
    ...Object.entries(STATUSES).map(option(match)),
  );

const topic = (match) =>
  el(
    "li",
    { class: `topic ${match.status}` },
    el("span", { class: "mark", "aria-hidden": "true" }),
    el(
      "div",
      { class: "topic-body" },
      el("p", { class: "topic-text" }, match.target.text),
      ...notes(match),
    ),
    el(
      "div",
      { class: "topic-meta" },
      statusSelect(match),
      ...(match.overridden
        ? [el("span", { class: "topic-adjusted" }, "Ajustado por el docente")]
        : []),
    ),
  );

const filterButton = ([value, label]) =>
  el(
    "button",
    {
      type: "button",
      class: "filter",
      "data-filter": value,
      "aria-pressed": String(state.filter === value),
    },
    label,
  );

const renderFilters = () => {
  const options = [
    ["todos", `Todos (${count(state.report.matches.length)})`],
    ...Object.entries(STATUSES),
  ];
  $("filters").replaceChildren(...options.map(filterButton));
};

export const renderTopics = () => {
  const visible = state.report.matches.filter(
    (match) => state.filter === "todos" || match.status === state.filter,
  );
  const empty = el(
    "li",
    { class: "topics-empty" },
    "Ningún tema tiene este estado.",
  );
  $("topics").replaceChildren(
    ...(visible.length ? visible.map(topic) : [empty]),
  );
};

const renderTally = (matches) => {
  const items = tally(matches).map(({ status, total }) =>
    el(
      "div",
      { class: `tally-item ${status}` },
      el(
        "dt",
        {},
        el("span", { class: "swatch", "aria-hidden": "true" }),
        STATUSES[status],
      ),
      el("dd", {}, count(total)),
    ),
  );
  $("tally").replaceChildren(...items);
};

const renderVerdict = (verdict) => {
  const { tone, title, detail } = VERDICTS[verdict];
  $("verdict").dataset.tone = tone;
  $("verdictTitle").textContent = title;
  $("verdictDetail").textContent = detail;
};

const renderPending = (report) => {
  const pending = report.pending_topics;
  $("pending").hidden = pending.length === 0;
  $("pendingTitle").textContent = PENDING_TITLES[report.verdict] ?? "";
  $("pendingList").replaceChildren(
    ...pending.map((text) => el("li", {}, text)),
  );
};

const renderAdvice = (report) => {
  const adjusted = report.matches.some((match) => match.overridden);
  $("advice").hidden = !report.recommendation;
  $("adviceText").textContent = report.recommendation ?? "";
  $("adjusted").hidden = Boolean(report.recommendation) || !adjusted;
};

const renderCaution = (report) => {
  const message = (report.warnings ?? []).join(" ");
  $("caution").hidden = !message;
  $("caution").textContent = message;
};

const animateNumber = (node, target) => {
  if (reducedMotion()) {
    node.textContent = target;
    return;
  }
  const start = performance.now();
  const step = (now) => {
    const progress = Math.min((now - start) / 900, 1);
    node.textContent = Math.round(target * (1 - (1 - progress) ** 3));
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};

const renderMeter = (coverage) => {
  const value = percent(coverage);
  const fill = $("meterFill");
  fill.style.setProperty("--coverage", 0);
  requestAnimationFrame(() =>
    requestAnimationFrame(() => fill.style.setProperty("--coverage", value)),
  );
  $("meterRoad").setAttribute(
    "aria-label",
    `Cobertura de ${value}% sobre un umbral del 50%`,
  );
  animateNumber($("coverage"), value);
};

export const renderReport = (report, { scroll = true } = {}) => {
  state.report = report;
  $("informeMeta").textContent =
    `${count(report.matches.length)} temas del programa de destino analizados con ${report.model}.`;
  renderMeter(report.coverage);
  renderVerdict(report.verdict);
  renderCaution(report);
  renderAdvice(report);
  renderTally(report.matches);
  renderPending(report);
  renderFilters();
  renderTopics();
  $("informe").hidden = false;
  if (scroll) {
    state.filter = "todos";
    $("informe").scrollIntoView({
      behavior: reducedMotion() ? "auto" : "smooth",
      block: "start",
    });
    $("informeTitulo").focus({ preventScroll: true });
  }
};

export const filterReport = (value) => {
  state.filter = value;
  renderFilters();
  renderTopics();
};

export const withWarnings = (report) => ({
  ...report,
  warnings: state.report.warnings,
});

export const matchesWithStatus = (index, status) =>
  state.report.matches.map((match) =>
    match.target.index === index
      ? { ...match, status, overridden: true }
      : match,
  );

const matchLines = (match) => [
  `${STATUSES[match.status]}${match.overridden ? " (ajustado por el docente)" : ""}: ${match.target.text}`,
  `   En el origen: ${match.sources.length ? match.sources.map((source) => source.text).join(". ") : "sin tema relacionado"}`,
  ...(match.reason ? [`   Razonamiento: ${match.reason}`] : []),
];

export const reportText = () => {
  const { report } = state;
  const { title, detail } = VERDICTS[report.verdict];
  return [
    "Informe de equivalencia (borrador asistido por IA)",
    `Cobertura estimada: ${percent(report.coverage)}%`,
    `${title}. ${detail}`,
    ...(report.warnings?.length
      ? ["", `Atención: ${report.warnings.join(" ")}`]
      : []),
    ...(report.recommendation
      ? ["", `Recomendación de la IA: ${report.recommendation}`]
      : []),
    "",
    ...report.matches.flatMap(matchLines),
    "",
    `Análisis realizado con ${report.model}. Borrador generado por IA, puede contener errores. El docente lo revisa y firma, y el Consejo Directivo resuelve. No constituye dictamen ni acto administrativo.`,
  ].join("\n");
};
