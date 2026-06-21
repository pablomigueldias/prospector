import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeSlug from 'rehype-slug';
import remarkGfm from 'remark-gfm';

interface PostPreviewProps {
  title?: string;
  excerpt?: string | null;
  coverUrl?: string | null;
  bodyMd?: string | null;
}

// Marcadores {{IMG}} não gerados não entram na prévia (espelha o site público).
const MARCADOR = /\{\{\s*IMG:.*?\}\}/gis;

/**
 * Prévia do post como ele sai no site — renderiza o Markdown (com imagens,
 * código, tabelas) pra revisar antes de publicar, sem sair do editor.
 */
export function PostPreview({
  title,
  excerpt,
  coverUrl,
  bodyMd,
}: PostPreviewProps): JSX.Element {
  const corpo = (bodyMd ?? '').replace(MARCADOR, '').trim();
  return (
    <article className="max-w-none">
      {coverUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={coverUrl}
          alt={title ?? 'capa'}
          className="w-full rounded-lg border border-line mb-4 object-cover max-h-72"
        />
      ) : null}
      <h1 className="font-display font-bold text-2xl text-ink leading-tight mb-2">
        {title || 'Sem título'}
      </h1>
      {excerpt ? (
        <p className="text-ink-soft text-[15px] mb-5 leading-relaxed">{excerpt}</p>
      ) : null}
      <div className="flex flex-col gap-3 text-[15px] text-ink leading-relaxed">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSlug, rehypeHighlight]}
          components={{
            h2: (p) => (
              <h2 className="font-display font-semibold text-xl text-ink mt-4 mb-1" {...p} />
            ),
            h3: (p) => (
              <h3 className="font-display font-semibold text-lg text-ink mt-3 mb-1" {...p} />
            ),
            p: (p) => <p className="leading-relaxed" {...p} />,
            ul: (p) => <ul className="list-disc pl-6 flex flex-col gap-1" {...p} />,
            ol: (p) => <ol className="list-decimal pl-6 flex flex-col gap-1" {...p} />,
            a: (p) => <a className="text-brand underline" {...p} />,
            blockquote: (p) => (
              <blockquote
                className="border-l-3 border-brand/40 pl-4 italic text-ink-soft"
                {...p}
              />
            ),
            table: (p) => (
              <table className="w-full border-collapse text-[14px]" {...p} />
            ),
            th: (p) => (
              <th className="border border-line bg-bg-alt px-3 py-1.5 text-left" {...p} />
            ),
            td: (p) => <td className="border border-line px-3 py-1.5" {...p} />,
            // eslint-disable-next-line @next/next/no-img-element
            img: (p) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                className="w-full rounded-lg border border-line my-2"
                {...p}
                alt={p.alt ?? ''}
              />
            ),
          }}
        >
          {corpo}
        </ReactMarkdown>
      </div>
    </article>
  );
}
