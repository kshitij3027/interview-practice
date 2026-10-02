import { rowsAsObjects } from "./csv.js";
import { codePointLength, normalizeText } from "./normalize.js";
import { readText } from "./read.js";

function nonNegativeInteger(value, label) {
  if (!/^(0|[1-9]\d*)$/.test(value)) {
    throw new Error(label + " must be a non-negative integer");
  }
  return Number(value);
}

function required(value, label) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(label + " must be non-empty");
  }
  return value;
}

function activeValue(value) {
  if (value === "true") return true;
  if (value === "false") return false;
  throw new Error("active must be true or false");
}

export function loadSnapshot(termsPath, aliasesPath) {
  const termRows = rowsAsObjects(
    readText(termsPath),
    ["term_id", "locale", "text", "popularity", "active"]
  );
  const terms = new Map();

  for (const row of termRows) {
    const termId = required(row.term_id, "term_id");
    if (terms.has(termId)) throw new Error("duplicate term_id: " + termId);
    const normalizedText = normalizeText(row.text);
    if (codePointLength(normalizedText) > 80) throw new Error("term text too long");
    terms.set(termId, {
      termId,
      locale: required(row.locale, "locale"),
      text: row.text,
      normalizedText,
      popularity: nonNegativeInteger(row.popularity, "popularity"),
      active: activeValue(row.active),
      aliases: [],
    });
  }

  const aliasRows = rowsAsObjects(readText(aliasesPath), ["alias_id", "term_id", "text"]);
  const aliases = new Map();

  for (const row of aliasRows) {
    const aliasId = required(row.alias_id, "alias_id");
    const termId = required(row.term_id, "term_id");
    const normalizedText = normalizeText(row.text);
    if (codePointLength(normalizedText) > 80) throw new Error("alias text too long");
    const signature = termId + "\u0000" + row.text;

    if (aliases.has(aliasId)) {
      if (aliases.get(aliasId).signature !== signature) {
        throw new Error("conflicting alias_id: " + aliasId);
      }
      continue;
    }

    const term = terms.get(termId);
    if (!term) throw new Error("alias references unknown term: " + termId);

    const alias = { aliasId, termId, text: row.text, normalizedText, signature };
    aliases.set(aliasId, alias);
    term.aliases.push(alias);
  }

  for (const term of terms.values()) {
    term.aliases.sort((a, b) => a.aliasId.localeCompare(b.aliasId));
  }

  return { terms, aliasCount: aliases.size };
}
