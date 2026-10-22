const TIMEOUT_MS = 1800000;

const MESSAGES = {
  network:
    "No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.",
  timeout:
    "El análisis tardó demasiado. Un equipo sin GPU potente puede necesitar varios minutos. Probá con programas más cortos.",
  server:
    "El servidor no pudo procesar la solicitud. Intentá de nuevo en unos minutos.",
};

export class ApiError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
  }
}

const failure = async (response) => {
  const body = await response.json().catch(() => ({}));
  const { detail } = body;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    return new ApiError(detail.message, detail.code);
  }
  return new ApiError(MESSAGES.server, "server");
};

const guarded = async (run) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await run(controller.signal);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error.name === "AbortError")
      throw new ApiError(MESSAGES.timeout, "timeout");
    throw new ApiError(MESSAGES.network, "network");
  } finally {
    clearTimeout(timer);
  }
};

const request = (path, options) =>
  guarded(async (signal) => {
    const response = await fetch(path, { ...options, signal });
    if (!response.ok) throw await failure(response);
    return response;
  });

const send = async (path, options) => (await request(path, options)).json();

const handle = (event, onProgress) => {
  if (event.type === "error") throw new ApiError(event.message, event.code);
  if (event.type === "progress") onProgress(event);
  return event.type === "report" ? event.report : null;
};

const readReport = async (body, onProgress) => {
  const reader = body.pipeThrough(new TextDecoderStream()).getReader();
  let pending = "";
  let report = null;
  for (
    let chunk = await reader.read();
    !chunk.done;
    chunk = await reader.read()
  ) {
    const lines = (pending + chunk.value).split("\n");
    pending = lines.pop();
    for (const line of lines.filter(Boolean))
      report = handle(JSON.parse(line), onProgress) ?? report;
  }
  if (!report) throw new ApiError(MESSAGES.server, "server");
  return report;
};

export const getLimits = () => send("/api/limits");

export const analyze = (payload, onProgress) =>
  guarded(async (signal) => {
    const response = await fetch("/api/analyze/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
    if (!response.ok) throw await failure(response);
    return readReport(response.body, onProgress);
  });

export const recompute = (matches) =>
  send("/api/recompute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ matches }),
  });

export const extractFile = (file) => {
  const body = new FormData();
  body.append("file", file);
  return send("/api/extract", { method: "POST", body });
};
