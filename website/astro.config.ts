import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import icon from "astro-icon";
import mdx from "@astrojs/mdx";

import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeCitation from "rehype-citation";

import react from "@astrojs/react";

import astroExpressiveCode from "astro-expressive-code";

// https://astro.build/config
// Before publishing on GitHub Pages, set `site` (for example "https://<user>.github.io") and `base`
// (for example "/<repository>/"); see README, "Publication checklist".
export default defineConfig({
  // site: "https://<user>.github.io",
  // base: "/<repository>/",
  vite: {
    plugins: [tailwindcss()],
  },
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [
      rehypeKatex,
      [
        rehypeCitation,
        {
          bibliography: "bibliography.bib",
          linkCitations: true,
        },
      ],
    ],
  },
  integrations: [
    icon(),
    astroExpressiveCode({
      styleOverrides: {
        borderRadius: "0.5rem",
        borderWidth: "0",
        codeBackground: ({ theme }) =>
          `var(--color-zinc-${theme.type === "dark" ? "800" : "200"})`,
        frames: {
          shadowColor: "transparent",
        },
      },
      themeCssSelector: (theme) =>
        theme.type === "dark" ? `[data-theme="dark"]` : `[data-theme="light"]`,
    }),
    mdx(),
    react(),
  ],
  // The template's Google font is not used: the page uses the reader's Palatino-style system serif (TeX Gyre Pagella
  // where installed), so nothing is fetched from a font service at build or run time.
  image: {
    responsiveStyles: true,
  },
});
