import fs from "node:fs";

export function readText(path) {
  return fs.readFileSync(path, "utf8");
}
