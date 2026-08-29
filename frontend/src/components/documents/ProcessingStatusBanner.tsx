import type { DocumentItem } from "../../types/document";

interface ProcessingStatusBannerProps {
  documents: DocumentItem[];
}

export function ProcessingStatusBanner({
  documents,
}: ProcessingStatusBannerProps) {
  if (documents.length === 0) {
    return null;
  }

  const pending = documents.filter((d) => d.status === "pending").length;
  const processing = documents.filter((d) => d.status === "processing").length;
  const completed = documents.filter((d) => d.status === "completed").length;
  const failed = documents.filter((d) => d.status === "failed").length;

  const isBusy = pending + processing > 0;

  return (
    <p className={`status ${isBusy ? "loading" : "success"}`}>
      {isBusy
        ? `Processing ${pending + processing} document(s)...`
        : "All documents processed."}{" "}
      {completed} completed
      {failed > 0 ? `, ${failed} failed` : ""}.
    </p>
  );
}
