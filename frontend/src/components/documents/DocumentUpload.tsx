import { ChangeEvent, FormEvent, useState } from "react";

import { uploadDocument } from "../../api/documents";
import type { DocumentItem } from "../../types/document";

interface DocumentUploadProps {
  workspaceId: string;
  onUploaded: (document: DocumentItem) => void;
}

const ALLOWED_EXTENSIONS = [
  ".pdf",
  ".docx",
  ".txt",
  ".md",
  ".csv",
];

const MAX_FILE_SIZE = 20 * 1024 * 1024;

export function DocumentUpload({
  workspaceId,
  onUploaded,
}: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    setError(null);

    const file = event.target.files?.[0];

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const extension =
      "." +
      file.name.split(".").pop()?.toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError(
        "Only PDF, DOCX, TXT, MD and CSV files are supported.",
      );
      setSelectedFile(null);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size must not exceed 20 MB.");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!selectedFile) {
      setError("Please select a file.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setProgress(0);

      const document = await uploadDocument(
        workspaceId,
        selectedFile,
        setProgress,
      );

      onUploaded(document);
      setSelectedFile(null);
      setProgress(0);
    } catch (uploadError) {
      setError("Unable to upload document.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept=".pdf,.docx,.txt,.md,.csv"
        onChange={handleFileChange}
        disabled={isUploading}
      />

      {selectedFile && (
        <p>
          Selected: {selectedFile.name}
        </p>
      )}

      {isUploading && (
        <progress
          value={progress}
          max={100}
        >
          {progress}%
        </progress>
      )}

      {error && (
        <p role="alert">{error}</p>
      )}

      <button
        type="submit"
        disabled={!selectedFile || isUploading}
      >
        {isUploading
          ? "Uploading..."
          : "Upload document"}
      </button>
    </form>
  );
}
