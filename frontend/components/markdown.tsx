import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Renders assistant answers as clean, readable Markdown. Element styles are
// set here (rather than a typography plugin) to keep the bundle small and the
// look consistent with the civic theme.
export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-sm leading-relaxed text-card-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => (
            <p className="mb-2 last:mb-0">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="my-2.5 space-y-2 last:mb-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 list-decimal space-y-1 pl-5 marker:text-muted-foreground last:mb-0">
              {children}
            </ol>
          ),
          // Records read as docket rows: a small gold tick, a mono field
          // label, then the value in body type.
          li: ({ children }) => (
            <li className="relative pl-4 before:absolute before:top-[0.5rem] before:left-0 before:size-1.5 before:rounded-[1px] before:bg-gold/80">
              {children}
            </li>
          ),
          strong: ({ children }) => (
            <strong className="font-mono text-[0.72rem] font-semibold tracking-wide text-foreground uppercase">
              {children}
            </strong>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-primary underline underline-offset-2"
            >
              {children}
            </a>
          ),
          h1: ({ children }) => (
            <h3 className="mt-1 mb-1.5 font-heading text-base font-semibold">
              {children}
            </h3>
          ),
          h2: ({ children }) => (
            <h3 className="mt-1 mb-1.5 font-heading text-base font-semibold">
              {children}
            </h3>
          ),
          h3: ({ children }) => (
            <h3 className="mt-1 mb-1.5 font-heading text-sm font-semibold">
              {children}
            </h3>
          ),
          code: ({ children }) => (
            <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
              {children}
            </code>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
