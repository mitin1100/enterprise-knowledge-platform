import { ChangeEvent, FormEvent, useState } from "react";

import type { EvaluationDatasetItem, RetrievalLevel } from "../../types/evaluation";

interface DatasetUploaderProps {
  datasetItems: EvaluationDatasetItem[];
  isParsingDataset: boolean;
  isRunning: boolean;
  onFileSelected: (file: File) => void;
  onRun: (retrievalLevel: RetrievalLevel, name?: string) => void;
}

const RETRIEVAL_LEVELS: { value: RetrievalLevel; label: string }[] = [
  { value: 1, label: "Vector only" },
  { value: 2, label: "Hybrid" },
  { value: 3, label: "Hybrid + reranked" },
];

export function DatasetUploader({
  datasetItems,
  isParsingDataset,
  isRunning,
  onFileSelected,
  onRun,
}: DatasetUploaderProps) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [runName, setRunName] = useState("");
  const [retrievalLevel, setRetrievalLevel] =
    useState<RetrievalLevel>(3);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setFileName(file.name);
    onFileSelected(file);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onRun(retrievalLevel, runName.trim() || undefined);
  }

  return (
    <div className="evaluation-uploader">
      <label className="evaluation-uploader__file">
        Dataset file (JSON or CSV)
        <input
          type="file"
          accept=".json,.csv"
          onChange={handleFileChange}
          disabled={isParsingDataset || isRunning}
        />
      </label>

      {isParsingDataset && <p>Parsing {fileName}...</p>}

      {!isParsingDataset && datasetItems.length > 0 && (
        <>
          <p>
            Loaded <strong>{datasetItems.length}</strong> question
            {datasetItems.length === 1 ? "" : "s"} from {fileName}.
          </p>

          <div className="evaluation-uploader__preview">
            <table>
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Expected source(s)</th>
                </tr>
              </thead>
              <tbody>
                {datasetItems.map((item, index) => (
                  <tr key={index}>
                    <td>{item.question}</td>
                    <td>
                      {item.expected_source.length > 0
                        ? item.expected_source.join(", ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <form
            className="evaluation-uploader__form"
            onSubmit={handleSubmit}
          >
            <label>
              Run name (optional)
              <input
                type="text"
                value={runName}
                placeholder="e.g. baseline run"
                onChange={(event) => setRunName(event.target.value)}
                disabled={isRunning}
              />
            </label>

            <label>
              Retrieval level
              <select
                value={retrievalLevel}
                onChange={(event) =>
                  setRetrievalLevel(
                    Number(event.target.value) as RetrievalLevel,
                  )
                }
                disabled={isRunning}
              >
                {RETRIEVAL_LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </label>

            <button type="submit" disabled={isRunning}>
              {isRunning ? "Running evaluation..." : "Run evaluation"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
