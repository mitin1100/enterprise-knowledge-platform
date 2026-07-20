import { DocumentList } from "../components/documents/DocumentList";
import { DocumentUpload } from "../components/documents/DocumentUpload";
import { useDocuments } from "../hooks/useDocuments";

interface WorkspacePageProps {
  workspaceId: string;
}

export function WorkspacePage({
  workspaceId,
}: WorkspacePageProps) {
  const {
    documents,
    isLoading,
    error,
    addDocument,
  } = useDocuments(workspaceId);

  return (
    <main>
      <header>
        <h1>Workspace documents</h1>
        <p>
          Upload PDF, DOCX, TXT, MD or CSV files.
        </p>
      </header>

      <section>
        <h2>Upload document</h2>

        <DocumentUpload
          workspaceId={workspaceId}
          onUploaded={addDocument}
        />
      </section>

      <section>
        <h2>Documents</h2>

        {isLoading && <p>Loading documents...</p>}
        {error && <p role="alert">{error}</p>}

        {!isLoading && (
          <DocumentList documents={documents} />
        )}
      </section>
    </main>
  );
}
