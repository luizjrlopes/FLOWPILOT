"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import PageHead from "@/components/PageHead";

const template = `id: approval-demo
version: '1.0'
trigger:
  manual: true
input_schema: generic
steps:
  - id: validate_input
    type: validate
  - id: human_approval
    type: approval
    required_role: approver
`;

export default function NewWorkflow() {
  const [name, setName] = useState("Workflow de aprovação");
  const [yaml, setYaml] = useState(template);
  const [error, setError] = useState("");
  const router = useRouter();

  async function save() {
    try {
      setError("");
      const workflow = await api("/workflows", {
        method: "POST",
        body: JSON.stringify({
          name,
          version: "v1.0",
          status: "Rascunho",
          trigger_mode: "manual",
          description: "Workflow criado para automação controlada.",
          yaml_text: yaml,
        }),
      });
      router.push(`/workflows/${workflow.id}`);
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Workflow authoring"
        title="Novo workflow"
        description="Criação textual por YAML validado com execução controlada."
      />
      <div className="grid2">
        <div className="card">
          <label>Nome</label>
          <input value={name} onChange={(event) => setName(event.target.value)} />
          <label>Definição YAML</label>
          <textarea
            className="yamlEditor"
            value={yaml}
            onChange={(event) => setYaml(event.target.value)}
          />
          <button className="btn primary" onClick={save}>
            Validar e criar
          </button>
          {error && <div className="alert danger">{error}</div>}
        </div>
        <div className="card">
          <h3>Contrato de execução</h3>
          <p>
            O backend valida a definição antes de persistir. Novos workflows entram como
            rascunho e só podem ser executados depois de ativados.
          </p>
        </div>
      </div>
    </>
  );
}
