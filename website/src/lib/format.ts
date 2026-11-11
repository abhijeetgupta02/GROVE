// Formatting shared by the Astro pages and the interactive islands. No data here.
const MINUS = "−";
export function fixed(x: number, d: number): string {
  const s = x.toFixed(d);
  return s.startsWith("-") && Number(s) !== 0 ? MINUS + s.slice(1) : s.replace(/^-/, "");
}
export function signed(x: number, d: number): string {
  const s = Math.abs(x).toFixed(d);
  return (x < 0 && Number(s) !== 0 ? MINUS : "+") + s;
}
export function interval(iv: [number, number] | undefined, d: number, sign = false): string {
  if (!iv) return "";
  const f = sign ? signed : fixed;
  return `[${f(iv[0], d)}, ${f(iv[1], d)}]`;
}
export const COLORS = {
  grove: "#2a78d6",
  main: "#1baf7a",
  gemma: "#eb6834",
  qwen: "#8a8984",
  label: "#ffffff",
} as const;
export type Cat = "fall" | "ppe";
export const CAT_NAME: Record<string, string> = {
  fall: "Fall",
  ppe: "Protective equipment",
  electrical: "Electrical",
};
export const CAT_SHORT: Record<string, string> = { fall: "Fall", ppe: "PPE", electrical: "Electrical" };
