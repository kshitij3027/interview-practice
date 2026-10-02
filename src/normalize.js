export function normalizeText(value) {
  if (typeof value !== "string") throw new Error("text must be a string");
  const normalized = value.normalize("NFKC").toLowerCase().trim().replace(/\s+/gu, " ");
  if (!normalized) throw new Error("normalized text is empty");
  return normalized;
}

export function codePointLength(value) {
  return Array.from(value).length;
}
