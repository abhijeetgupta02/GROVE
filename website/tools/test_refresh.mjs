// Integration checks against a served GROVE page; no model calls.
// GROVE_URL=http://127.0.0.1:4321/GROVE/ node tools/test_refresh.mjs
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";
const url = process.env.GROVE_URL ?? "http://127.0.0.1:4321/GROVE/";
const output = new URL("../screenshots/refresh/", import.meta.url);
mkdirSync(output, { recursive: true });
const browser = await chromium.launch(
  process.env.PLAYWRIGHT_CHANNEL
    ? { channel: process.env.PLAYWRIGHT_CHANNEL }
    : {},
);
const report = [];
try {
  for (const width of [1440, 390])
    for (const scheme of ["light", "dark"]) {
      const context = await browser.newContext({
        viewport: { width, height: 960 },
        colorScheme: scheme,
        reducedMotion: "reduce",
      });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.goto(url, { waitUntil: "networkidle" });
      await page.screenshot({
        path: new URL(`hero-${width}-${scheme}.png`, output).pathname,
        animations: "disabled",
      });
      await page.locator("#teaser").scrollIntoViewIfNeeded();
      await page
        .locator("#teaser astro-island[ssr]")
        .waitFor({ state: "detached" });
      await page
        .getByRole("button", { name: "Missing head protection", exact: true })
        .click();
      await page
        .getByRole("heading", { name: "Missing head protection", exact: true })
        .waitFor();
      assert.match(
        await page.locator(".comparison-notes").innerText(),
        /DEVELOPMENT SCENE\s+125/,
      );
      const slider = page.getByRole("slider", { name: /Drag to move/ });
      await slider.focus();
      const before = Number(await slider.getAttribute("aria-valuenow"));
      await slider.press("ArrowRight");
      const after = Number(await slider.getAttribute("aria-valuenow"));
      assert.ok(after > before, "comparison slider responds to keyboard");
      await page.getByLabel("Show annotated boxes").check();
      await page
        .locator("#teaser")
        .screenshot({
          path: new URL(`comparison-${width}-${scheme}.png`, output).pathname,
          animations: "disabled",
        });
      await page
        .getByRole("button", {
          name: "An opening in the work floor",
          exact: true,
        })
        .click();
      await page
        .locator(".comparison-notes")
        .getByRole("heading", {
          name: "An opening in the work floor",
          exact: true,
        })
        .waitFor();
      await page.locator("#gallery").scrollIntoViewIfNeeded();
      await page.locator("#gallery .example-card").first().waitFor();
      await page
        .locator("#gallery astro-island[ssr]")
        .waitFor({ state: "detached" });
      assert.equal(await page.locator("#gallery .example-card").count(), 13);
      await page
        .locator("#gallery")
        .getByLabel("Outcome")
        .selectOption("fails");
      await page.waitForFunction(
        () => document.querySelectorAll("#gallery .example-card").length === 3,
      );
      await page.locator("#gallery .example-card").first().click();
      await page.locator("#gallery dialog[open]").waitFor();
      await page
        .locator("#gallery dialog")
        .getByRole("button", { name: "Next image", exact: true })
        .click();
      await page.keyboard.press("Escape");
      await page.locator("#gallery dialog").waitFor({ state: "hidden" });
      await page.locator("#gallery").getByLabel("Category").selectOption("ppe");
      await page.waitForFunction(
        () => document.querySelectorAll("#gallery .example-card").length === 0,
      );
      await page
        .getByRole("button", { name: "Show all examples", exact: true })
        .click();
      await page.waitForFunction(
        () => document.querySelectorAll("#gallery .example-card").length === 13,
      );
      await page
        .locator("#gallery")
        .screenshot({
          path: new URL(`gallery-${width}-${scheme}.png`, output).pathname,
          animations: "disabled",
        });
      await page.locator("#explorer").scrollIntoViewIfNeeded();
      await page
        .locator("#explorer astro-island[ssr]")
        .waitFor({ state: "detached" });
      await page.getByTestId("explorer-f1").waitFor();
      assert.equal(
        (await page.getByTestId("explorer-f1").textContent()).trim(),
        "0.702",
      );
      await page
        .getByRole("button", { name: /first-freeze thresholds/ })
        .click();
      await page.waitForFunction(
        () =>
          document
            .querySelector('[data-testid="explorer-f1"]')
            ?.textContent.trim() === "0.483",
      );
      assert.equal(
        (await page.getByTestId("explorer-f1").textContent()).trim(),
        "0.483",
      );
      await page.getByRole("button", { name: /refit thresholds/ }).click();
      await page.locator("#how").scrollIntoViewIfNeeded();
      await page
        .locator("#how astro-island[ssr]")
        .waitFor({ state: "detached" });
      await page
        .getByRole("button", { name: "3. Formula", exact: true })
        .click();
      await page.waitForFunction(() =>
        document.querySelector("#how")?.textContent.includes("0.680"),
      );
      assert.match(await page.locator("#how").innerText(), /0.680/);
      // Hydrate the remaining lazy islands before accessibility/image checks.
      const height = await page.evaluate(() => document.body.scrollHeight);
      for (let y = 0; y < height; y += 800)
        await page.evaluate((y) => window.scrollTo(0, y), y);
      await page.waitForLoadState("networkidle");
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );
      assert.ok(overflow <= 1, `${width} ${scheme} page overflow ${overflow}`);
      const broken = await page
        .locator("img")
        .evaluateAll((imgs) =>
          imgs
            .filter((i) => i.complete && i.naturalWidth === 0)
            .map((i) => i.src),
        );
      assert.deepEqual(broken, []);
      const axe = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      const violations = axe.violations.map((x) => ({
        id: x.id,
        impact: x.impact,
        help: x.help,
        targets: x.nodes.map((n) => n.target),
      }));
      report.push({ width, scheme, errors, overflow, violations });
      assert.deepEqual(errors, []);
      await context.close();
    }
} finally {
  await browser.close();
  writeFileSync(
    new URL("report.json", output),
    JSON.stringify(report, null, 2),
  );
}
console.log(JSON.stringify(report, null, 2));
if (
  report.some((r) =>
    r.violations.some((v) => ["serious", "critical"].includes(v.impact)),
  )
)
  process.exitCode = 1;
