import { createContext, useContext } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * `react-markdown` renders a fenced code block as `<pre><code>`, and inline code as a
 * bare `<code>`. For a fenced block *without* a language tag, the `code` component
 * receives exactly the same props as for inline code (`className === undefined`), so
 * `className` cannot discriminate the two cases. The surrounding `pre` element is the
 * only reliable signal: it flags its own subtree through this context instead of
 * guessing from the props.
 */
const InsideCodeBlockContext = createContext(false)

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
  code: ({ className, children }) => {
    const insideCodeBlock = useContext(InsideCodeBlockContext)
    if (insideCodeBlock) {
      // The `pre` wrapper owns the block visuals (background, border radius, padding);
      // the `code` element must not add its own, or the block gets a visible inner box.
      // The language class is preserved for future highlighting.
      return (
        <code className={`${className ? `${className} ` : ''}block font-mono text-sm`}>{children}</code>
      )
    }
    return <code className="rounded-[6px] bg-[var(--surface)] px-1 font-mono text-sm">{children}</code>
  },
  pre: ({ children }) => (
    <InsideCodeBlockContext.Provider value={true}>
      <pre className="my-3 overflow-x-auto rounded-[12px] bg-[var(--background)] p-4">{children}</pre>
    </InsideCodeBlockContext.Provider>
  ),
}

export default function ChatMarkdown({ content }: ChatMarkdownProps) {
  return <ReactMarkdown components={components} remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
}