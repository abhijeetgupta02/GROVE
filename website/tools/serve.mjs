// Minimal static server for dist/ (used by the screenshot and accessibility scripts; `npm run preview` works too).
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".ico": "image/x-icon", ".txt": "text/plain", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".xml": "application/xml", ".webmanifest": "application/manifest+json" };

export function serve(port = 4399) {
  const server = createServer(async (req, res) => {
    try {
      let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
      if (p.endsWith("/")) p += "index.html";
      const f = normalize(join(DIST, p));
      if (!f.startsWith(normalize(DIST))) throw new Error("outside dist");
      const s = await stat(f);
      if (!s.isFile()) throw new Error("not a file");
      const type = TYPES[extname(f)] ?? "application/octet-stream";
      let body = await readFile(f);
      const headers = { "Content-Type": type, "Cache-Control": "max-age=3600" };
      // Compress text like GitHub Pages does, so local page-weight and Lighthouse numbers match the published site.
      if (/text|javascript|json|svg/.test(type) && /\bgzip\b/.test(req.headers["accept-encoding"] ?? "")) {
        body = gzipSync(body);
        headers["Content-Encoding"] = "gzip";
        headers["Vary"] = "Accept-Encoding";
      }
      res.writeHead(200, headers);
      res.end(body);
    } catch {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("not found");
    }
  });
  return new Promise((resolve) => server.listen(port, "127.0.0.1", () => resolve({ server, url: `http://127.0.0.1:${port}/` })));
}
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const { url } = await serve(Number(process.env.PORT ?? 4399));
  console.log(`serving dist/ at ${url}`);
}
