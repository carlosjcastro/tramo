const TIMEOUT_MS = 1800000;

const MESSAGES = {
  network: "No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.",
  timeout: "El análisis tardó demasiado. Un equipo sin GPU potente puede necesitar varios minutos. Probá con programas más cortos.",
  server: "El servidor no pudo procesar la solicitud. Intentá de nuevo en unos minutos.",
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

const send = async (path, options) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    if (!response.ok) throw await failure(response);
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error.name === "AbortError") throw new ApiError(MESSAGES.timeout, "timeout");
    throw new ApiError(MESSAGES.network, "network");
  } finally {
    clearTimeout(timer);
  }
};

export const getLimits = () => send("/api/limits");

export const analyze = (payload) =>
  send("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
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
