import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseDelay, parseLimit, RISKS, STATUSES } from "./validation.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(here, "..", "public");

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(payload) });
  res.end(payload);
}

function text(res, status, content, contentType) {
  res.writeHead(status, { "content-type": contentType, "content-length": Buffer.byteLength(content) });
  res.end(content);
}

async function readJson(req) {
  let raw = "";
  for await (const chunk of req) raw += chunk;
  if (!raw) return {};
  return JSON.parse(raw);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export function createHandler(store) {
  return async function handler(req, res) {
    try {
      const url = new URL(req.url, "http://localhost");
      const segments = url.pathname.split("/").filter(Boolean);

      if (req.method === "GET" && url.pathname === "/api/health") return json(res, 200, { ok: true });
      if (req.method === "GET" && url.pathname === "/api/meta") return json(res, 200, store.meta());

      if (req.method === "GET" && url.pathname === "/api/grants") {
        const meta = store.meta();
        const status = url.searchParams.get("status") || "all";
        const system = url.searchParams.get("system") || "all";
        const risk = url.searchParams.get("risk") || "all";
        if (status !== "all" && !STATUSES.has(status)) return json(res, 400, { error: "invalid status" });
        if (risk !== "all" && !RISKS.has(risk)) return json(res, 400, { error: "invalid risk" });
        if (system !== "all" && !meta.systems.includes(system)) return json(res, 400, { error: "invalid system" });
        const limit = parseLimit(url.searchParams.get("limit"), meta.cycle.maxPageSize);
        const delay = parseDelay(url.searchParams.get("delay_ms"));
        if (delay) await sleep(delay);
        return json(res, 200, store.list({ status, system, risk, cursor: url.searchParams.get("cursor"), limit }));
      }

      if (segments[0] === "api" && segments[1] === "grants" && segments.length === 3 && req.method === "GET") {
        const grant = store.get(segments[2]);
        return grant ? json(res, 200, { grant, datasetRevision: store.meta().datasetRevision }) : json(res, 404, { error: "grant not found" });
      }

      if (segments[0] === "api" && segments[1] === "grants" && segments[3] === "note" && segments.length === 4 && req.method === "PATCH") {
        let body;
        try { body = await readJson(req); } catch { return json(res, 400, { error: "invalid JSON body" }); }
        const result = store.updateNote(segments[2], body.expected_revision, body.note);
        if (result.kind === "not_found") return json(res, 404, { error: "grant not found" });
        if (result.kind === "invalid") return json(res, 400, { error: result.message });
        if (result.kind === "stale") return json(res, 409, { error: "stale grant revision", ...result });
        return json(res, 200, result);
      }

      if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        return text(res, 200, fs.readFileSync(path.join(publicDir, "index.html"), "utf8"), "text/html; charset=utf-8");
      }
      if (req.method === "GET" && url.pathname === "/app.js") {
        return text(res, 200, fs.readFileSync(path.join(publicDir, "app.js"), "utf8"), "text/javascript; charset=utf-8");
      }
      if (req.method === "GET" && url.pathname === "/styles.css") {
        return text(res, 200, fs.readFileSync(path.join(publicDir, "styles.css"), "utf8"), "text/css; charset=utf-8");
      }
      return json(res, 404, { error: "not found" });
    } catch (error) {
      return json(res, 400, { error: error.message || "bad request" });
    }
  };
}
