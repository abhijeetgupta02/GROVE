// Server-side access to all site data (Astro components). Islands import the smaller modules directly.
import galleryJson from "../data/gallery.json";
import errorsJson from "../data/errors.json";
export * from "./numbers";
export * from "./format";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const GALLERY = galleryJson as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const ERRORS = errorsJson as any;
