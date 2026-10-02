import { codePointLength, normalizeText } from "./normalize.js";
import { readText } from "./read.js";

export function loadQueries(path) {
  return readText(path)
    .split(/\r?\n/)
    .filter((line) => line.trim() !== "")
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch {
        return { malformed: true, lineNumber: index + 1 };
      }
    });
}

export function validateQuery(raw) {
  const requestId =
    raw && typeof raw.request_id === "string" && raw.request_id.trim() !== ""
      ? raw.request_id
      : null;

  try {
    if (!raw || typeof raw !== "object" || Array.isArray(raw) || raw.malformed) {
      throw new Error("invalid object");
    }
    if (requestId === null) throw new Error("invalid request_id");
    if (typeof raw.locale !== "string" || raw.locale.trim() === "") {
      throw new Error("invalid locale");
    }

    const text = normalizeText(raw.text);
    if (codePointLength(text) > 48) throw new Error("query text too long");

    if (!Number.isInteger(raw.max_edits) || raw.max_edits < 0 || raw.max_edits > 2) {
      throw new Error("invalid max_edits");
    }
    if (!Number.isInteger(raw.limit) || raw.limit < 1 || raw.limit > 10) {
      throw new Error("invalid limit");
    }

    return {
      ok: true,
      query: {
        requestId,
        locale: raw.locale,
        text,
        maxEdits: raw.max_edits,
        limit: raw.limit,
      },
    };
  } catch {
    return { ok: false, requestId };
  }
}
