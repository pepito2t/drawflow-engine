import { useMemo } from "react";
import { parseMarkdown, type Block, type Inline } from "../lib/markdown-lite";

interface MarkdownTextProps {
  source: string;
  /** Without it, links are shown as plain text: nothing opens from untrusted model output. */
  onLink?: (href: string) => void;
}

export function MarkdownText({ source, onLink }: MarkdownTextProps) {
  const blocks = useMemo(() => parseMarkdown(source), [source]);
  return (
    <div className="markdown">
      {blocks.map((block, index) => (
        <MarkdownBlock key={index} block={block} onLink={onLink} />
      ))}
    </div>
  );
}

interface BlockProps {
  block: Block;
  onLink: ((href: string) => void) | undefined;
}

function MarkdownBlock({ block, onLink }: BlockProps) {
  switch (block.kind) {
    case "paragraph":
      return (
        <p>
          <Inlines inlines={block.inlines} onLink={onLink} />
        </p>
      );
    case "heading":
      return (
        <p className="markdown-heading" id={block.id}>
          <Inlines inlines={block.inlines} onLink={onLink} />
        </p>
      );
    case "code":
      return <pre>{block.text}</pre>;
    case "table":
      return (
        <table>
          <thead>
            <tr>
              {block.header.map((cell, index) => (
                <th key={index}>
                  <Inlines inlines={cell} onLink={onLink} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, index) => (
                  <td key={index}>
                    <Inlines inlines={cell} onLink={onLink} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    case "list": {
      const items = block.items.map((item, index) => (
        <li key={index}>
          <Inlines inlines={item.inlines} onLink={onLink} />
          {item.children.length > 0 && (
            <ol className="markdown-sublist">
              {item.children.map((child, childIndex) => (
                <li key={childIndex}>
                  <Inlines inlines={child} onLink={onLink} />
                </li>
              ))}
            </ol>
          )}
        </li>
      ));
      return block.ordered ? <ol>{items}</ol> : <ul>{items}</ul>;
    }
  }
}

interface InlinesProps {
  inlines: Inline[];
  onLink: ((href: string) => void) | undefined;
}

function Inlines({ inlines, onLink }: InlinesProps) {
  return inlines.map((inline, index) => {
    switch (inline.kind) {
      case "strong":
        return <strong key={index}>{inline.text}</strong>;
      case "code":
        return <code key={index}>{inline.text}</code>;
      case "link":
        return onLink ? (
          <button
            key={index}
            type="button"
            className="link-button"
            onClick={() => {
              onLink(inline.href);
            }}
          >
            {inline.text}
          </button>
        ) : (
          <span key={index}>{inline.text}</span>
        );
      case "text":
        return <span key={index}>{inline.text}</span>;
    }
  });
}
