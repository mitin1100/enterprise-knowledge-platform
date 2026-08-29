import { useEffect, useState } from "react";

import { getChunkContext } from "../../api/chunks";
import type { Citation } from "../../types/chat";
import type { ChunkContext } from "../../types/chunk";

interface CitationViewerProps {
  citation: Citation;
  onClose: () => void;
}

export function CitationViewer({
  citation,
  onClose,
}: CitationViewerProps) {
  const [context, setContext] = useState<ChunkContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    setIsLoading(true);
    setError(null);
    setContext(null);

    getChunkContext(citation.document_id, citation.chunk_index)
      .then((result) => {
        if (!cancelled) {
          setContext(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Unable to load the source passage.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [citation.document_id, citation.chunk_index]);

  return (
    <div
      className="citation-viewer-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="citation-viewer"
        role="dialog"
        aria-modal="true"
        aria-label="Source passage"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="citation-viewer__header">
          <div>
            <h3>{citation.document_name ?? "Unknown document"}</h3>

            {citation.page_number != null && (
              <span className="citation-viewer__page">
                Page {citation.page_number}
              </span>
            )}
          </div>

          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
          >
            &times;
          </button>
        </header>

        {isLoading && <p>Loading source...</p>}
        {error && <p role="alert">{error}</p>}

        {context && (
          <div className="citation-viewer__body">
            {context.previous && (
              <p className="citation-viewer__context">
                {context.previous.content}
              </p>
            )}

            <p className="citation-viewer__highlight">
              {context.chunk.content}
            </p>

            {context.next && (
              <p className="citation-viewer__context">
                {context.next.content}
              </p>
            )}
          </div>
        )}

        <footer className="citation-viewer__footer">
          Relevance score: {citation.score.toFixed(3)}
        </footer>
      </div>
    </div>
  );
}
