import { useMemo } from "react";
import { parseMarkdown, type Block, type Inline } from "../lib/markdown-lite";

export function MarkdownText({ source }: { source: string }) {
  const blocks = useMemo(() => parseMarkdown(source), [source]);
  return (
    <div className="markdown">
      {blocks.map((block, index) => (
        <MarkdownBlock key={index} block={block} />
      ))}
    </div>
  );
}

function MarkdownBlock({ block }: { block: Block }) {
  switch (block.kind) {
    case "paragraph":
      return (
        <p>
          <Inlines inlines={block.inlines} />
        </p>
      );
    case "heading":
      return (
        <p className="markdown-heading">
          <Inlines inlines={block.inlines} />
        </p>
      );
    case "code":
      return <pre>{block.text}</pre>;
    case "list": {
      const items = block.items.map((item, index) => (
        <li key={index}>
          <Inlines inlines={item} />
        </li>
      ));
      return block.ordered ? <ol>{items}</ol> : <ul>{items}</ul>;
    }
  }
}

function Inlines({ inlines }: { inlines: Inline[] }) {
  return inlines.map((inline, index) => {
    if (inline.kind === "strong") {
      return <strong key={index}>{inline.text}</strong>;
    }
    if (inline.kind === "code") {
      return <code key={index}>{inline.text}</code>;
    }
    return <span key={index}>{inline.text}</span>;
  });
}
