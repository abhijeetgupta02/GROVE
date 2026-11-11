// axe-core accessibility check of the built page (light and dark, 1440 and 390 px), after every island has hydrated.
// Fails on any serious or critical violation. Usage: npm run build && npm run test:a11y
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { writeFileSync, mkdirSync } from "node:fs";
import { serve } from "./serve.mjs";

const { server, url } = await serve(4397);
const browser = await chromium.launch();
const out = [];
let serious = 0;
try {
  for (const width of [1440, 390]) {
    for (const scheme of ["light", "dark"]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
      const page = await context.newPage();
      await page.goto(url, { waitUntil: "networkidle" });
      const h = await page.evaluate(() => document.body.scrollHeight);
      for (let y = 0; y < h; y += 600) { await page.evaluate((yy) => window.scrollTo(0, yy), y); await page.waitForTimeout(100); }
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(600);
      const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"]).analyze();
      const v = r.violations.map((x) => ({ id: x.id, impact: x.impact, help: x.help, nodes: x.nodes.length, targets: x.nodes.slice(0, 5).map((n) => n.target.join(" ")) }));
      serious += v.filter((x) => x.impact === "serious" || x.impact === "critical").length;
      out.push({ width, scheme, violations: v, passes: r.passes.length });
      await context.close();
    }
  }
} finally {
  await browser.close();
  server.close();
}
mkdirSync(new URL("../screenshots/", import.meta.url), { recursive: true });
writeFileSync(new URL("../screenshots/a11y_report.json", import.meta.url), JSON.stringify(out, null, 1) + "\n");
for (const o of out) console.log(`${o.width} ${o.scheme}: ${o.violations.length} violations (${o.violations.map((v) => `${v.id}:${v.impact}:${v.nodes}`).join(", ") || "none"})`);
console.log(serious ? `FAILED: ${serious} serious or critical violations` : "No serious or critical violations");
if (serious) process.exit(1);
