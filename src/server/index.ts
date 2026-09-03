import { createServer } from "node:http";
import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { DataStore } from "./dataStore.js";
import { IncidentService } from "./incidentService.js";
import { handleApi } from "./routes.js";

const service = new IncidentService(new DataStore());
const port = Number(process.env.PORT ?? 8080);
const root = process.cwd();

const mime: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8"
};

function serveFile(path: string, res: any): boolean {
  if (!existsSync(path) || !statSync(path).isFile()) return false;
  res.writeHead(200, { "content-type": mime[extname(path)] ?? "application/octet-stream" });
  res.end(readFileSync(path, "utf-8"));
  return true;
}

createServer(async (req, res) => {
  if (await handleApi(req, res, service)) return;
  const url = new URL(req.url ?? "/", "http://localhost");
  if (url.pathname.startsWith("/assets/")) {
    const relative = normalize(url.pathname.slice("/assets/".length)).replace(/^\.\.(\/|\\)/, "");
    if (serveFile(join(root, "dist", "src", "client", relative), res)) return;
  }
  if (url.pathname === "/styles.css" && serveFile(join(root, "web", "styles.css"), res)) return;
  if ((url.pathname === "/" || url.pathname === "/index.html") && serveFile(join(root, "web", "index.html"), res)) return;
  res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
  res.end("Not found");
}).listen(port, () => console.log(`Incident Desk listening on http://localhost:${port}`));
