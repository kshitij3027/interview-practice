declare module "node:http" {
  export type IncomingMessage = any;
  export type ServerResponse = any;
  export function createServer(handler: (req: IncomingMessage, res: ServerResponse) => void | Promise<void>): { listen(port: number, cb?: () => void): void };
}
declare module "node:fs" {
  export function readFileSync(path: string, encoding: string): string;
  export function existsSync(path: string): boolean;
  export function statSync(path: string): { isFile(): boolean };
}
declare module "node:path" {
  export function join(...parts: string[]): string;
  export function extname(path: string): string;
  export function normalize(path: string): string;
}
declare const process: { env: Record<string, string | undefined>; cwd(): string };
