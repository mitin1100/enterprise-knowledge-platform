import { useState, type FormEvent } from "react";

interface CreateWorkspaceFormProps {
  isCreating: boolean;
  onCreate: (name: string, description: string) => Promise<unknown>;
}

export function CreateWorkspaceForm({
  isCreating,
  onCreate,
}: CreateWorkspaceFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedName = name.trim();

    if (!trimmedName) {
      return;
    }

    const workspace = await onCreate(trimmedName, description.trim());

    if (workspace) {
      setName("");
      setDescription("");
    }
  };

  return (
    <form className="create-workspace-form" onSubmit={handleSubmit}>
      <input
        type="text"
        value={name}
        placeholder="Workspace name"
        onChange={(event) => setName(event.target.value)}
        disabled={isCreating}
      />

      <input
        type="text"
        value={description}
        placeholder="Description (optional)"
        onChange={(event) => setDescription(event.target.value)}
        disabled={isCreating}
      />

      <button type="submit" disabled={isCreating || !name.trim()}>
        {isCreating ? "Creating..." : "Create workspace"}
      </button>
    </form>
  );
}
