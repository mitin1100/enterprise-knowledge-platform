import { EvaluationPanel } from "../components/evaluation/EvaluationPanel";

interface EvaluationPageProps {
  workspaceId: string;
}

export function EvaluationPage({ workspaceId }: EvaluationPageProps) {
  return <EvaluationPanel workspaceId={workspaceId} />;
}
