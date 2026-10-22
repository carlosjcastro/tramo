import { $, el } from "./dom.js";

const TITLES = {
  info: "Procesando",
  success: "Listo",
  warning: "Atención",
  error: "Hay un problema",
};

let timer;

export const clearNotice = () => {
  clearTimeout(timer);
  $("notices").replaceChildren();
};

export const notify = (
  tone,
  message,
  { title = TITLES[tone], ttl = 0 } = {},
) => {
  clearNotice();
  const attrs = {
    class: `notice ${tone}`,
    ...(tone === "error" && { role: "alert" }),
  };
  $("notices").append(
    el("div", attrs, el("strong", {}, title), el("span", {}, message)),
  );
  if (ttl) timer = setTimeout(clearNotice, ttl);
};
