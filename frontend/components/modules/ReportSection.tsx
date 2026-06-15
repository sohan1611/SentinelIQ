import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

function flattenToString(node: React.ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(flattenToString).join("");
  if (React.isValidElement<{ children?: React.ReactNode }>(node)) {
    return flattenToString(node.props.children);
  }
  return "";
}

const components: Components = {
  h1: ({ children }) => (
    <div className="mt-10 first:mt-0">
      <div className="font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary mb-1">
        {flattenToString(children)}
      </div>
      <h1 className="font-sans text-[18px] font-semibold text-text-primary mb-3">{children}</h1>
    </div>
  ),
  h2: ({ children }) => (
    <div className="mt-10 first:mt-0">
      <div className="font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary mb-1">
        {flattenToString(children)}
      </div>
      <h2 className="font-sans text-[16px] font-semibold text-text-primary mb-3">{children}</h2>
    </div>
  ),
  h3: ({ children }) => (
    <h3 className="font-sans text-[14px] font-semibold text-text-primary mt-6 mb-2">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="font-sans text-[15px] text-text-primary leading-[1.8] mb-4">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-5 flex flex-col gap-2 font-sans text-[14px] text-text-primary leading-[1.75] mb-4">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-5 flex flex-col gap-2 font-sans text-[14px] text-text-primary leading-[1.75] mb-4">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="pl-1">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-text-primary">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  blockquote: ({ children }) => (
    <blockquote className="pl-4 border-l-2 border-border italic font-sans text-[14px] text-text-primary my-4">
      {children}
    </blockquote>
  ),
  hr: () => <div className="w-full h-px bg-border my-8" />,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-navy hover:underline">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="font-mono text-[13px] text-text-primary bg-canvas px-1 py-0.5 rounded-[3px]">
      {children}
    </code>
  ),
  table: ({ children }) => (
    <div className="w-full overflow-x-auto mb-4">
      <table className="w-full text-left border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="border-b border-border">{children}</thead>,
  th: ({ children }) => (
    <th className="py-2 pr-4 font-sans text-2xs font-medium uppercase tracking-[0.07em] text-text-secondary">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="py-2 pr-4 border-b border-border font-sans text-[13px] text-text-primary">{children}</td>
  ),
};

export interface ReportSectionProps {
  content: string;
}

export function ReportSection({ content }: ReportSectionProps) {
  return (
    <div className="flex flex-col">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
