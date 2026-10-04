/** The few Markdown constructs local models use, rendered as React elements (never as HTML). */
export type Inline = { kind: "text" | "strong" | "code"; text: string };

export type Block =
  | { kind: "paragraph"; inlines: Inline[] }
  | { kind: "list"; ordered: boolean; items: Inline[][] }
  | { kind: "code"; text: string }
  | { kind: "heading"; inlines: Inline[] };

const FENCE = "```";
const BULLET = /^\s*[-*•]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;
const HEADING = /^#{1,6}\s+(.*)$/;
const INLINE_TOKEN = /(\*\*[^*]+\*\*|`[^`]+`)/g;

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
    } else if (BULLET.test(line) || NUMBERED.test(line)) {
      index = readList(lines, index, blocks);
    } else if (HEADING.test(line)) {
      blocks.push({ kind: "heading", inlines: parseInlines(line.replace(HEADING, "$1")) });
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
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return { kind: "strong", text: part.slice(2, -2) };
      }
      if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
        return { kind: "code", text: part.slice(1, -1) };
      }
      return { kind: "text", text: part };
    });
}

function findFenceEnd(lines: string[], start: number): number {
  const end = lines.findIndex((line, index) => index >= start && line.trim().startsWith(FENCE));
  return end === -1 ? lines.length : end;
}

function readList(lines: string[], start: number, blocks: Block[]): number {
  const ordered = NUMBERED.test(lines[start] ?? "");
  const pattern = ordered ? NUMBERED : BULLET;
  const items: Inline[][] = [];
  let index = start;
  for (let line = lines[index]; line !== undefined && pattern.test(line); line = lines[index]) {
    items.push(parseInlines(line.replace(pattern, "$1")));
    index += 1;
  }
  blocks.push({ kind: "list", ordered, items });
  return index;
}

function readParagraph(lines: string[], start: number, blocks: Block[]): number {
  const parts: string[] = [];
  let index = start;
  for (let line = lines[index]; line?.trim() && !startsBlock(line); line = lines[index]) {
    parts.push(line.trim());
    index += 1;
  }
  blocks.push({ kind: "paragraph", inlines: parseInlines(parts.join(" ")) });
  return index;
}

function startsBlock(line: string): boolean {
  return (
    line.trim().startsWith(FENCE) || BULLET.test(line) || NUMBERED.test(line) || HEADING.test(line)
  );
}
