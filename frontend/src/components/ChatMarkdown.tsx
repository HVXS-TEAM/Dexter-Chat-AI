import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface ChatMarkdownProps {
  content: string
}

const components: Components = {
  p: ({ children }) => <p className="leading-6">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-[var(--text-primary)]">{children}</strong>,
  h1: ({ children }) => <h1 className="mb-1 mt-4 text-base font-semibold leading-6">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-1 mt-4 text-base font-semibold leading-6">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1 mt-4 text-base font-semibold leading-6">{children}</h3>,
  h4: ({ children }) => <h4 className="mb-1 mt-3 text-sm font-semibold leading-5">{children}</h4>,
  ul: ({ children }) => <ul className="my-1 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-1 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="my-1">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 rounded-[12px] border-l-[3px] border-[var(--primary)] bg-[var(--surface)] p-4">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto">
      <table className="min-w-full border-collapse border border-[var(--border-default)] text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => <th className="border border-[var(--border-default)] bg-[var(--surface)] px-3 py-2 text-left font-semibold">{children}</th>,
  td: ({ children }) => <td className="border border-[var(--border-default)] px-3 py-2">{children}</td>,
  code: ({ className, children }) => (
    <code
      className={className
        ? 'block overflow-x-auto font-mono text-sm'
        : 'rounded-[6px] bg-[var(--surface)] px-1 font-mono text-sm'}
    >
      {children}
    </code>
  ),
  pre: ({ children }) => <pre className="my-3 overflow-x-auto rounded-[12px] bg-[var(--background)] p-4">{children}</pre>,
}

export default function ChatMarkdown({ content }: ChatMarkdownProps) {
  return <ReactMarkdown components={components} remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
}