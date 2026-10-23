const STORAGE_KEY = "tramo-motion";
const SYSTEM_QUERY = "(prefers-reduced-motion: reduce)";
const root = document.documentElement;

const readChoice = () => {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
};

const saveChoice = (mode) => {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    return;
  }
};

const systemMode = () => (matchMedia(SYSTEM_QUERY).matches ? "off" : "on");

export const reducedMotion = () => root.dataset.motion === "off";

const apply = (button, mode) => {
  root.dataset.motion = mode;
  button.setAttribute("aria-pressed", String(mode === "on"));
};

const init = () => {
  const button = document.getElementById("motion");
  apply(button, readChoice() ?? systemMode());
  button.addEventListener("click", () => {
    const next = reducedMotion() ? "on" : "off";
    saveChoice(next);
    apply(button, next);
  });
};

init();
