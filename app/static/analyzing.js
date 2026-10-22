import { $, el, reducedMotion } from "./dom.js";

const WORD = "Analizando...";
const TICK_MS = 1000;
const SECONDS_PER_MINUTE = 60;

let timer;

const pad = (value) => String(value).padStart(2, "0");

const clock = (seconds) =>
  `${pad(Math.floor(seconds / SECONDS_PER_MINUTE))}:${pad(seconds % SECONDS_PER_MINUTE)}`;

const letter = (character, index) => {
  const node = el("span", {}, character);
  node.style.setProperty("--i", index);
  return node;
};

const buildTitle = () => {
  const title = $("analyzingLetters");
  if (!title.childElementCount) title.replaceChildren(...[...WORD].map(letter));
};

export const startAnalyzing = () => {
  buildTitle();
  const started = Date.now();
  $("elapsed").textContent = clock(0);
  timer = setInterval(() => {
    $("elapsed").textContent = clock(
      Math.floor((Date.now() - started) / TICK_MS),
    );
  }, TICK_MS);
  $("form").hidden = true;
  $("analyzing").hidden = false;
  $("analyzingTitle").focus({ preventScroll: true });
  $("analyzing").scrollIntoView({
    behavior: reducedMotion() ? "auto" : "smooth",
    block: "center",
  });
};

export const stopAnalyzing = () => {
  clearInterval(timer);
  $("analyzing").hidden = true;
  $("form").hidden = false;
};
