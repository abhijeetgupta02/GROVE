// Numbers and thresholds from src/data (written by tools/export_site_data.py). A missing key throws.
import numbersJson from "../data/numbers.json";
import thresholdsJson from "../data/thresholds.json";
import { fixed, signed, interval } from "./format";

export interface NumEntry {
  value: number | string;
  interval?: [number, number];
  unit: string;
  source: string;
  key_path: unknown[];
  post_hoc: boolean;
  note?: string;
}
export const NUMBERS = (numbersJson as unknown as { numbers: Record<string, NumEntry> }).numbers;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const THRESHOLDS = thresholdsJson as any;

export function entry(key: string): NumEntry {
  const e = NUMBERS[key];
  if (!e) throw new Error(`src/data/numbers.json has no entry "${key}"`);
  return e;
}
export function has(key: string): boolean {
  return key in NUMBERS;
}
export function val(key: string): number {
  const v = entry(key).value;
  if (typeof v !== "number") throw new Error(`numbers.json entry "${key}" is not a number`);
  return v;
}
export function str(key: string): string {
  return String(entry(key).value);
}
export function fmt(key: string, d = 3): string {
  return fixed(val(key), d);
}
export function fmtSigned(key: string, d = 3): string {
  return signed(val(key), d);
}
export function fmtCI(key: string, d = 3, sign = false): string {
  const iv = entry(key).interval;
  if (!iv) throw new Error(`numbers.json entry "${key}" has no interval`);
  return interval(iv, d, sign);
}
export function fmtInt(key: string): string {
  return Math.round(val(key)).toLocaleString("en-US");
}
export function sourceOf(key: string): string {
  const e = entry(key);
  return `${e.source} → ${e.key_path.map((x) => (Array.isArray(x) ? x.join(" | ") : String(x))).join(" / ")}${e.post_hoc ? " (post hoc)" : ""}`;
}
export function isPostHoc(key: string): boolean {
  return entry(key).post_hoc;
}
