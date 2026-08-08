import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-invert max-w-none prose-headings:font-display prose-headings:text-white prose-p:text-laap-text-secondary prose-a:text-laap-gold hover:prose-a:text-laap-gold-light prose-strong:text-white prose-code:text-laap-gold prose-code:bg-laap-bg-code prose-code:px-1 prose-code:rounded prose-pre:bg-laap-bg-code prose-pre:border prose-pre:border-laap-border prose-pre:rounded-sm prose-blockquote:border-l-laap-gold prose-blockquote:text-laap-text-secondary prose-li:text-laap-text-secondary prose-table:border-laap-border prose-th:bg-laap-bg-tertiary prose-th:text-white prose-td:border-laap-border prose-td:text-laap-text-secondary">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-3xl md:text-4xl font-bold mt-12 mb-6 first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="text-2xl md:text-3xl font-semibold mt-10 mb-4 border-b border-laap-border pb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-xl md:text-2xl font-medium mt-8 mb-3 text-laap-gold">{children}</h3>,
          hr: () => <hr className="border-laap-border my-10" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
