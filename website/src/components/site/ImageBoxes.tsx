// A gallery image with switchable box layers. Boxes come from gallery.json (fractions of width and height);
// nothing is burnt into the image files.
import { COLORS, CAT_SHORT } from "../../lib/format";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type GalleryImage = any;
export interface Layers {
  labels?: boolean;
  grove?: boolean;
  groveAll?: boolean;
  gemma?: boolean;
}
type Box = number[];

function Rect({ b, color, dash, width = 3 }: { b: Box; color: string; dash?: string; width?: number }) {
  const [x1, y1, x2, y2] = b;
  const x = Math.min(x1, x2) * 1000, y = Math.min(y1, y2) * 1000, w = Math.abs(x2 - x1) * 1000, h = Math.abs(y2 - y1) * 1000;
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} fill="none" stroke="#000" strokeOpacity={0.6} strokeWidth={width + 2} vectorEffect="non-scaling-stroke" />
      <rect x={x} y={y} width={w} height={h} fill="none" stroke={color} strokeWidth={width} strokeDasharray={dash} vectorEffect="non-scaling-stroke" />
    </g>
  );
}
function Tag({ b, text, color, dark = false }: { b: Box; text: string; color: string; dark?: boolean }) {
  const left = Math.max(0, Math.min(b[0], b[2])) * 100, top = Math.max(0, Math.min(b[1], b[3])) * 100;
  return (
    <span
      className="pointer-events-none absolute -translate-y-full rounded-sm px-1 font-sans text-[11px] leading-4 font-semibold whitespace-nowrap"
      style={{ left: `${Math.min(left, 72)}%`, top: `${Math.max(top, 5)}%`, background: color === COLORS.grove ? "#1d5aa6" : color, color: dark ? "#111" : "#fff" }}
    >
      {text}
    </span>
  );
}

export function altText(img: GalleryImage): string {
  return `Development image ${img.id}, generated with Google Gemini` + (img.caption ? `. Dataset caption: ${img.caption}` : "");
}

export function ImageBoxes({
  img,
  base,
  layers,
  thumb = false,
  eager = false,
  className = "",
  cats = ["fall", "ppe"],
  showTags = true,
}: {
  img: GalleryImage;
  base: string;
  layers: Layers;
  thumb?: boolean;
  eager?: boolean;
  className?: string;
  cats?: string[];
  showTags?: boolean;
}) {
  const f = img.files;
  const w = thumb ? img.thumb_width : img.width,
    h = thumb ? img.thumb_height : img.height;
  const boxes: { b: Box; color: string; dash?: string; tag?: string; dark?: boolean; width?: number }[] = [];
  for (const c of cats) {
    if (layers.labels) for (const b of img.label_boxes[c] ?? []) boxes.push({ b, color: COLORS.label, dash: "6 4", tag: `label: ${CAT_SHORT[c]}`, dark: true, width: 2 });
    if (layers.grove && img.grove.decisions[c]) {
      const gb: Box[] = img.grove.boxes[c] ?? [];
      (layers.groveAll ? gb : gb.slice(0, 1)).forEach((b, k) =>
        boxes.push({ b, color: COLORS.grove, tag: k === 0 ? `GROVE: ${CAT_SHORT[c]}` : undefined, width: k === 0 ? 3 : 2, dash: k === 0 ? undefined : "8 4" }),
      );
    }
    if (layers.gemma && img.gemma.decisions[c] && img.gemma.box_drawn[c])
      boxes.push({ b: img.gemma.box_drawn[c], color: COLORS.gemma, dash: "2 3", tag: `gemma4:31b box as written: ${CAT_SHORT[c]}`, dark: true });
  }
  return (
    <div className={`relative overflow-hidden ${className}`}>
      <picture>
        <source type="image/webp" srcSet={base + (thumb ? f.thumb_webp : f.full_webp)} />
        <img
          src={base + (thumb ? f.thumb_jpg : f.full_jpg)}
          width={w}
          height={h}
          alt={thumb ? `Thumbnail of selected example ${img.id}` : altText(img)}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          className="m-0! block h-auto w-full rounded-none"
          draggable={false}
        />
      </picture>
      <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true">
        {boxes.map((x, k) => (
          <Rect key={k} b={x.b} color={x.color} dash={x.dash} width={thumb ? Math.max(1.5, (x.width ?? 3) - 1) : x.width} />
        ))}
      </svg>
      {showTags && !thumb && boxes.filter((x) => x.tag).map((x, k) => <Tag key={k} b={x.b} text={x.tag!} color={x.color} dark={x.dark} />)}
    </div>
  );
}
