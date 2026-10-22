import { extractFile } from "./api.js";
import { count, megabytes } from "./format.js";
import { limits } from "./limits.js";

const EXTENSIONS = [".pdf", ".docx"];

const extensionOf = (name) => name.slice(name.lastIndexOf(".")).toLowerCase();

const fileProblem = (file) => {
  const extension = extensionOf(file.name);
  if (extension === ".doc")
    return "Los archivos .doc antiguos no se pueden leer. Abrilo en Word y guardalo como .docx.";
  if (!EXTENSIONS.includes(extension))
    return "Solo se aceptan archivos PDF o Word (.docx).";
  if (file.size === 0) return "El archivo está vacío.";
  if (file.size > limits.maxFileBytes)
    return `El archivo supera el máximo de ${megabytes(limits.maxFileBytes)}.`;
  return "";
};

export const createField = (root, emptyMessage) => {
  const area = root.querySelector("textarea");
  const counter = root.querySelector("[data-count]");
  const input = root.querySelector("[data-input]");
  const pick = root.querySelector("[data-pick]");
  const fileName = root.querySelector("[data-file]");
  const remove = root.querySelector("[data-remove]");
  const error = root.querySelector("[data-error]");

  const showError = (message) => {
    error.textContent = message;
    error.hidden = !message;
    area.setAttribute("aria-invalid", String(Boolean(message)));
  };

  const refresh = () => {
    area.maxLength = limits.maxChars;
    counter.textContent = `${count(area.value.length)} de ${count(limits.maxChars)}`;
    counter.classList.toggle("near", area.value.length > limits.maxChars * 0.9);
  };

  const showFile = (name) => {
    fileName.textContent = name ?? "";
    fileName.hidden = !name;
    remove.hidden = !name;
  };

  const busy = (isBusy) => {
    root.classList.toggle("is-busy", isBusy);
    pick.disabled = isBusy;
    pick.textContent = isBusy ? "Leyendo archivo" : "Subir PDF o Word";
  };

  const load = async (file) => {
    showError("");
    const problem = fileProblem(file);
    if (problem) return showError(problem);
    busy(true);
    try {
      const result = await extractFile(file);
      area.value = result.text;
      showFile(
        `${result.filename}, ${count(result.characters)} caracteres. Revisá el texto.`,
      );
      refresh();
    } catch (failure) {
      showError(failure.message);
    } finally {
      busy(false);
      input.value = "";
    }
  };

  const drop = (event) => {
    event.preventDefault();
    root.classList.remove("is-dropping");
    const { files } = event.dataTransfer;
    if (files.length > 1)
      return showError("Subí un solo archivo por programa.");
    if (files.length === 1) load(files[0]);
  };

  pick.addEventListener("click", () => input.click());
  input.addEventListener(
    "change",
    () => input.files[0] && load(input.files[0]),
  );
  remove.addEventListener("click", () => api.set(""));
  area.addEventListener("input", () => {
    showError("");
    refresh();
  });
  root.addEventListener("dragover", (event) => {
    event.preventDefault();
    root.classList.add("is-dropping");
  });
  root.addEventListener("dragleave", (event) => {
    if (!root.contains(event.relatedTarget))
      root.classList.remove("is-dropping");
  });
  root.addEventListener("drop", drop);

  const api = {
    value: () => area.value.trim(),
    focus: () => area.focus(),
    refresh,
    set(text) {
      area.value = text;
      showFile(null);
      showError("");
      refresh();
    },
    validate() {
      const empty = !api.value();
      showError(empty ? emptyMessage : "");
      return !empty;
    },
  };
  refresh();
  return api;
};
