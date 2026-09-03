import type { IncomingMessage, ServerResponse } from "node:http";

export function json(res: ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(body));
}

export async function readJson<T>(req: IncomingMessage): Promise<T> {
  const chunks: Uint8Array[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString("utf-8");
  return JSON.parse(text || "{}") as T;
}

declare const Buffer: { concat(chunks: Uint8Array[]): { toString(encoding: string): string } };
