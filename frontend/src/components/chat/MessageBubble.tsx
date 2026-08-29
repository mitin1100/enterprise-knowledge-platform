import type { Citation, MessageItem } from "../../types/chat";

interface MessageBubbleProps {
  message: MessageItem;
  onSelectCitation: (citation: Citation) => void;
}

export function MessageBubble({
  message,
  onSelectCitation,
}: MessageBubbleProps) {
  const isAssistant = message.role === "ASSISTANT";

  return (
    <article
      className="message"
      data-role={message.role.toLowerCase()}
    >
      <p className="message__content">{message.content}</p>

      {isAssistant && message.citations.length > 0 && (
        <div className="message__sources">
          <span className="message__sources-label">Sources</span>

          <ol>
            {message.citations.map((citation, index) => (
              <li key={citation.chunk_id}>
                <button
                  type="button"
                  className="citation-badge"
                  onClick={() => onSelectCitation(citation)}
                >
                  <span className="citation-badge__ref">
                    [{index + 1}]{" "}
                    {citation.document_name ?? "Unknown document"}
                    {citation.page_number != null &&
                      `, page ${citation.page_number}`}
                  </span>

                  <span className="citation-badge__preview">
                    {citation.chunk_preview}
                  </span>

                  <span className="citation-badge__score">
                    Relevance {citation.score.toFixed(3)}
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </div>
      )}
    </article>
  );
}
