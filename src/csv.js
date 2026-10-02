export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        field += ch;
      }
      continue;
    }

    if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(field);
      field = "";
    } else if (ch === '\n') {
      row.push(field.replace(/\r$/, ""));
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }

  if (quoted) throw new Error("unterminated quoted CSV field");
  if (field !== "" || row.length > 0) {
    row.push(field.replace(/\r$/, ""));
    if (row.some((value) => value !== "")) rows.push(row);
  }
  return rows;
}

export function rowsAsObjects(text, expectedHeaders) {
  const rows = parseCsv(text);
  if (rows.length === 0) throw new Error("empty CSV");
  const headers = rows[0];
  if (headers.length !== expectedHeaders.length || headers.some((h, i) => h !== expectedHeaders[i])) {
    throw new Error("unexpected CSV headers: " + headers.join(","));
  }
  return rows.slice(1).map((values, rowIndex) => {
    if (values.length !== headers.length) throw new Error("invalid CSV column count at row " + (rowIndex + 2));
    return Object.fromEntries(headers.map((header, i) => [header, values[i]]));
  });
}
