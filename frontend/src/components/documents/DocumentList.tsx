import type { DocumentItem } from "../../types/document";

interface DocumentListProps {
  documents: DocumentItem[];
}

export function DocumentList({
  documents,
}: DocumentListProps) {
  if (documents.length === 0) {
    return <p>No documents uploaded.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>File</th>
          <th>Type</th>
          <th>Size</th>
          <th>Status</th>
          <th>Uploaded at</th>
        </tr>
      </thead>

      <tbody>
        {documents.map((document) => (
          <tr key={document.id}>
            <td>{document.original_filename}</td>
            <td>{document.file_extension}</td>
            <td>{formatFileSize(document.file_size)}</td>
            <td>
              <span data-status={document.status}>
                {document.status}
              </span>

              {document.status === "failed" &&
                document.error_message && (
                  <p>{document.error_message}</p>
                )}
            </td>
            <td>
              {new Date(
                document.created_at,
              ).toLocaleString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}
