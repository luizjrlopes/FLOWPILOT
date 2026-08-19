"use client";import {useState} from "react";import {api} from "@/lib/api";import PageHead from "@/components/PageHead";import {useRouter} from "next/navigation";const template=`id: approval-demo
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
`;export default function NewWorkflow(){const [name,setName]=useState("Workflow de aprovação"),[yaml,setYaml]=useState(template),[error,setError]=useState("");const router=useRouter();async function save(){try{const w=await api("/workflows",{method:"POST",body:JSON.stringify({name,version:"v1.0",status:"Rascunho",trigger_mode:"manual",description:"Workflow criado no ambiente demonstrativo.",yaml_text:yaml})});router.push(`/workflows/${w.id}`)}catch(e){setError(String(e))}}return <><PageHead eyebrow="Workflow authoring" title="Novo workflow" description="Criação textual por YAML validado. O editor visual complexo continua fora do escopo."/><div className="grid2"><div className="card"><label>Nome</label><input value={name} onChange={e=>setName(e.target.value)}/><label>Definição YAML</label><textarea className="yamlEditor" value={yaml} onChange={e=>setYaml(e.target.value)}/><button className="btn primary" onClick={save}>Validar e criar</button>{error&&<div className="alert danger">{error}</div>}</div><div className="card"><h3>Contrato</h3><p>O backend valida a estrutura antes de persistir. Workflows novos entram como rascunho e não podem ser disparados até serem ativados.</p></div></div></>