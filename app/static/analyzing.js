import { $, reducedMotion } from "./dom.js";
import { stageText } from "./labels.js";

const TICK_MS = 1000;
const SECONDS_PER_MINUTE = 60;
const FULL_PAUSE_MS = 700;
const MAX_BEFORE_REPORT = 99;

let timer;
let reached = 0;

const pad = (value) => String(value).padStart(2, "0");

const clock = (seconds) => `${pad(Math.floor(seconds / SECONDS_PER_MINUTE))}:${pad(seconds % SECONDS_PER_MINUTE)}`;

const paint = (percent) => {
  $("analyzing").style.setProperty("--p", `${percent}%`);
  $("paint").setAttribute("aria-valuenow", String(percent));
  $("percent").textContent = `${percent} %`;
};

export const showProgress = (event) => {
  const share = Math.round((event.done / event.total) * 100);
  reached = event.stage === "finished" ? 100 : Math.max(reached, Math.min(share, MAX_BEFORE_REPORT));
  paint(reached);
  $("stage").textContent = stageText(event);
};

export const startAnalyzing = () => {
  const started = Date.now();
  reached = 0;
  paint(0);
  $("stage").textContent = "Preparando el análisis";
  $("elapsed").textContent = clock(0);
  timer = setInterval(() => {
    $("elapsed").textContent = clock(Math.floor((Date.now() - started) / TICK_MS));
  }, TICK_MS);
  $("form").hidden = true;
  $("analyzing").hidden = false;
  $("analyzingTitle").focus({ preventScroll: true });
  $("analyzing").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "center" });
};

export const completeAnalyzing = async () => {
  paint(100);
  if (!reducedMotion()) await new Promise((resolve) => setTimeout(resolve, FULL_PAUSE_MS));
};

export const stopAnalyzing = () => {
  clearInterval(timer);
  $("analyzing").hidden = true;
  $("form").hidden = false;
};
