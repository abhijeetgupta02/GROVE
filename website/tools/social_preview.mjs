// Draws public/social-preview.png (1200 x 630) for link previews: title and two headline numbers from numbers.json.
// No dataset image is used. Usage: node tools/social_preview.mjs
import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const N = JSON.parse(readFileSync(new URL("../src/data/numbers.json", import.meta.url), "utf8")).numbers;
const f = (k, d) => N[k].value.toFixed(d);
const html = `<!doctype html><html><body style="margin:0;width:1200px;height:630px;display:flex;flex-direction:column;justify-content:center;
  padding:0 90px;box-sizing:border-box;background:#0f172a;color:#f8fafc;font-family:'Palatino Linotype',Palatino,serif">
  <div style="font-size:84px;font-weight:700;letter-spacing:1px">GROVE</div>
  <div style="font-size:40px;margin-top:8px">Grounded Violation Evaluator for Visual Inspection</div>
  <div style="display:flex;gap:60px;margin-top:56px;font-family:system-ui,sans-serif">
    <div><div style="font-size:56px;color:#7cb3f0">${f("final.grove.micro_f1", 3)}</div><div style="font-size:24px;color:#cbd5e1">micro-F1 on ${N["final.n_images"].value.toLocaleString("en-US")} unseen images<br>(single pass: ${f("final.gemma.micro_f1", 3)})</div></div>
    <div><div style="font-size:56px;color:#7cb3f0">${f("final.grove.false_alarms", 1)}</div><div style="font-size:24px;color:#cbd5e1">false alarms per 100<br>violation-free images (single pass: ${f("final.gemma.false_alarms", 1)})</div></div>
  </div>
  <div style="font-size:24px;margin-top:48px;color:#cbd5e1">University of Dayton</div>
</body></html>`;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
await p.setContent(html);
await p.screenshot({ path: fileURLToPath(new URL("../public/social-preview.png", import.meta.url)) });
await b.close();
console.log("written public/social-preview.png");
