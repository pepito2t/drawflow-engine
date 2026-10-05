/** The few Markdown constructs local models and the user guide use, rendered as React elements. */
export type Inline =
  { kind: "text" | "strong" | "code"; text: string } | { kind: "link"; text: string; href: string };

export interface ListItem {
  inlines: Inline[];
  children: Inline[][];
}

export type Block =
  | { kind: "paragraph"; inlines: Inline[] }
  | { kind: "list"; ordered: boolean; items: ListItem[] }
  | { kind: "code"; text: string }
  | { kind: "heading"; id: string; inlines: Inline[] }
  | { kind: "table"; header: Inline[][]; rows: Inline[][][] };

const FENCE = "```";
const BULLET = /^(\s*)[-*•]\s+(.*)$/;
const NUMBERED = /^(\s*)\d+[.)]\s+(.*)$/;
const HEADING = /^#{1,6}\s+(.*)$/;
const TABLE_ROW = /^\s*\|.*\|\s*$/;
const TABLE_SEPARATOR = /^\s*\|?\s*:?-{3,}/;
const NESTED_INDENT = 2;
const INLINE_TOKEN = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;
const LINK = /^\[([^\]]+)\]\(([^)\s]+)\)$/;
const SLUG_DROPPED = /[^\p{L}\p{N}_\- ]/gu;

export function parseMarkdown(source: string): Block[] {
  const blocks: Block[] = [];
  const lines = source.trim().split(/\r?\n/);
  let index = 0;
  while (index < lines.length) {
    const line = lines[index] ?? "";
    if (line.trim().startsWith(FENCE)) {
      const end = findFenceEnd(lines, index + 1);
      blocks.push({ kind: "code", text: lines.slice(index + 1, end).join("\n") });
      index = end + 1;
    } else if (isTableStart(lines, index)) {
      index = readTable(lines, index, blocks);
    } else if (BULLET.test(line) || NUMBERED.test(line)) {
      index = readList(lines, index, blocks);
    } else if (HEADING.test(line)) {
      const title = line.replace(HEADING, "$1");
      blocks.push({ kind: "heading", id: slug(title), inlines: parseInlines(title) });
      index += 1;
    } else if (line.trim()) {
      index = readParagraph(lines, index, blocks);
    } else {
      index += 1;
    }
  }
  return blocks;
}

export function parseInlines(text: string): Inline[] {
  return text
    .split(INLINE_TOKEN)
    .filter((part) => part !== "")
    .map((part): Inline => {
      const link = LINK.exec(part);
      if (link) {
        return { kind: "link", text: link[1] ?? "", href: link[2] ?? "" };
      }
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return { kind: "strong", text: part.slice(2, -2) };
      }
      if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
        return { kind: "code", text: part.slice(1, -1) };
      }
      return { kind: "text", text: part };
    });
}

/** Same anchors as GitHub and the engine, so the guide's links work everywhere. */
export function slug(title: string): string {
  return title.trim().toLowerCase().replace(SLUG_DROPPED, "").replaceAll(" ", "-");
}

function findFenceEnd(lines: string[], start: number): number {
  const end = lines.findIndex((line, index) => index >= start && line.trim().startsWith(FENCE));
  return end === -1 ? lines.length : end;
}

function readList(lines: string[], start: number, blocks: Block[]): number {
  const ordered = NUMBERED.test(lines[start] ?? "");
  const items: ListItem[] = [];
  let index = start;
  for (let line = lines[index]; line !== undefined; line = lines[index]) {
    const match = BULLET.exec(line) ?? NUMBERED.exec(line);
    if (!match) {
      break;
    }
    const indent = match[1]?.length ?? 0;
    const inlines = parseInlines(match[2] ?? "");
    const parent = items.at(-1);
    if (indent >= NESTED_INDENT && parent) {
      parent.children.push(inlines);
    } else {
      items.push({ inlines, children: [] });
    }
    index += 1;
  }
  blocks.push({ kind: "list", ordered, items });
  return index;
}

function isTableStart(lines: string[], index: number): boolean {
  return TABLE_ROW.test(lines[index] ?? "") && TABLE_SEPARATOR.test(lines[index + 1] ?? "");
}

function readTable(lines: string[], start: number, blocks: Block[]): number {
  const header = cells(lines[start] ?? "");
  const rows: Inline[][][] = [];
  let index = start + 2;
  for (let line = lines[index]; line !== undefined && TABLE_ROW.test(line); line = lines[index]) {
    rows.push(cells(line));
    index += 1;
  }
  blocks.push({ kind: "table", header, rows });
  return index;
}

function cells(row: string): Inline[][] {
  return row
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => parseInlines(cell.trim()));
}

function readParagraph(lines: string[], start: number, blocks: Block[]): number {
  const parts: string[] = [];
  let index = start;
  for (let line = lines[index]; line?.trim() && !startsBlock(lines, index); line = lines[index]) {
    parts.push(line.trim());
    index += 1;
  }
  blocks.push({ kind: "paragraph", inlines: parseInlines(parts.join(" ")) });
  return index;
}

function startsBlock(lines: string[], index: number): boolean {
  const line = lines[index] ?? "";
  return (
    line.trim().startsWith(FENCE) ||
    BULLET.test(line) ||
    NUMBERED.test(line) ||
    HEADING.test(line) ||
    isTableStart(lines, index)
  );
}
