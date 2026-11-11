// Screenshots of every section at 1440 and 390 px, light and dark, into screenshots/, plus the explorer check:
// at the refit thresholds the explorer must show the final-set micro-F1 and false alarms from numbers.json, and at the
// first-freeze thresholds the post hoc first-freeze values. Usage: npm run build && npm run screenshots
import { chromium } from "playwright";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { serve } from "./serve.mjs";

const NUM = JSON.parse(readFileSync(new URL("../src/data/numbers.json", import.meta.url), "utf8")).numbers;
const OUT = new URL("../screenshots/", import.meta.url);
mkdirSync(OUT, { recursive: true });
const SECTIONS = ["hero", "teaser", "glance", "how", "explorer", "results", "gallery", "failures", "limitations", "reproducibility", "cite"];
const { server, url } = await serve(4399);
const browser = await chromium.launch();
const report = { shots: [], explorer: {}, problems: [] };
try {
  for (const width of [1440, 390]) {
    for (const scheme of ["light", "dark"]) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, colorScheme: scheme, reducedMotion: "reduce" });
      page.on("pageerror", (e) => report.problems.push(`${width} ${scheme} page error: ${e.message}`));
      page.on("console", (m) => { if (m.type() === "error") report.problems.push(`${width} ${scheme} console: ${m.text()}`); });
      await page.goto(url, { waitUntil: "networkidle" });
      // scroll through the page so every client:visible island hydrates and lazy images load
      const h = await page.evaluate(() => document.body.scrollHeight);
      for (let y = 0; y < h; y += 600) { await page.evaluate((yy) => window.scrollTo(0, yy), y); await page.waitForTimeout(120); }
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(800);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (overflow > 1) report.problems.push(`${width} ${scheme}: page is ${overflow}px wider than the viewport`);
      for (const id of SECTIONS) {
        const loc = id === "hero" ? page.locator("header").first() : page.locator(`#${id}`);
        await loc.scrollIntoViewIfNeeded();
        await page.waitForTimeout(250);
        const file = `${id}_${width}_${scheme}.png`;
        await loc.screenshot({ path: new URL(file, OUT).pathname.replace(/^\/([A-Za-z]:)/, "$1"), animations: "disabled" });
        report.shots.push(file);
      }
      if (width === 1440 && scheme === "light") {
        const read = async () => Object.fromEntries(await Promise.all(["f1", "fa", "precision", "recall"].map(async (k) => [k, (await page.getByTestId(`explorer-${k}`).textContent())?.trim()])));
        report.explorer.refit = await read();
        await page.getByRole("button", { name: /first-freeze thresholds/ }).click();
        await page.waitForTimeout(300);
        report.explorer.first_freeze = await read();
        const want = {
          refit: { f1: NUM["final.grove.micro_f1"].value.toFixed(3), fa: NUM["final.grove.false_alarms"].value.toFixed(1) },
          first_freeze: { f1: NUM["final.first_freeze_grove.micro_f1"].value.toFixed(3), fa: NUM["final.first_freeze_grove.false_alarms"].value.toFixed(1) },
        };
        report.explorer.expected = want;
        for (const k of ["refit", "first_freeze"]) for (const q of ["f1", "fa"]) if (report.explorer[k][q] !== want[k][q]) report.problems.push(`explorer ${k} ${q}: shows ${report.explorer[k][q]}, expected ${want[k][q]}`);
      }
      await page.close();
    }
  }
} finally {
  await browser.close();
  server.close();
}
writeFileSync(new URL("report.json", OUT), JSON.stringify(report, null, 1) + "\n");
console.log(JSON.stringify({ shots: report.shots.length, explorer: report.explorer, problems: report.problems }, null, 1));
if (report.problems.length) process.exit(1);
