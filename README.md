# FlowPilot AI

**FlowPilot AI** é uma plataforma de automação de workflows orientada a execução controlada, rastreabilidade e aprovação humana. O sistema combina definições declarativas em YAML, processamento assíncrono, etapas determinísticas, integração com IA estruturada, políticas de retry, DLQ e trilha completa de evidências.

A arquitetura foi desenhada para manter decisões críticas sob controle da aplicação: a IA pode extrair, classificar e estruturar informações, mas não ignora contratos, não aprova etapas protegidas e não altera silenciosamente o estado de uma execução.

## Visão geral

O FlowPilot organiza automações operacionais em workflows versionados e auditáveis. Cada execução percorre etapas explícitas, registra eventos e pode ser interrompida por validação, aprovação humana, falha de conector ou política de recuperação.

Principais capacidades:

- catálogo de workflows com definições YAML versionadas;
- criação e atualização de workflows com validação de contrato;
- disparo manual e por webhook idempotente;
- validação de entrada antes da execução;
- etapas determinísticas de transformação e decisão;
- extração e classificação por IA com saída estruturada;
- validação Pydantic antes de qualquer transição dependente de IA;
- conectores desacoplados com política de retry;
- gates de aprovação humana com bloqueio real da execução;
- retomada segura após aprovação;
- rejeição terminal com motivo registrado;
- processamento assíncrono com RabbitMQ;
- Dead Letter Queue com reprocessamento explícito;
- criação de nova execução ao reprocessar itens da DLQ, preservando a original;
- idempotência para triggers externos;
- simulação controlada de falhas de conectores e de saída inválida de IA;
- trilha de eventos por execução e auditoria global.

## Arquitetura

```text
Browser / Next.js
        │ JWT
        ▼
FastAPI API
        │
        ├── Workflow definitions / JSON Schema
        ├── RBAC / idempotency / approvals
        ├── execution state + audit events
        │
        ├──────────────► PostgreSQL
        │
        └── publish ───► RabbitMQ
                            │
                            ▼
                       Python Worker
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
          deterministic   structured   connectors
             steps           AI        / retries
```

A API é responsável por autorização, contratos, criação das execuções, decisões humanas e persistência de estado. O worker executa etapas assíncronas e publica evidências de cada tentativa. RabbitMQ desacopla a execução do ciclo HTTP e mantém a fila operacional explícita.

## Stack

| Camada | Tecnologia |
|---|---|
| Web | Next.js 16.3, React 19, TypeScript, App Router |
| API | Python 3.13, FastAPI, SQLAlchemy 2 |
| Banco | PostgreSQL 18 |
| Mensageria | RabbitMQ 4, filas duráveis e DLQ |
| Workflows | YAML + JSON Schema Draft 2020-12 |
| IA estruturada | Provider boundary + Pydantic |
| Autenticação | JWT + RBAC server-side |
| Ambiente local | Docker Compose |
| CI | GitHub Actions |

## Modelo de execução

Uma execução típica percorre estados e etapas explícitos:

```text
TRIGGERED
   │
   ▼
INPUT_VALIDATION
   │
   ▼
PROCESSING
   │
   ├──► AI STRUCTURED STEP
   │          │
   │          └── saída inválida ──► FAILED_VALIDATION
   │
   ├──► CONNECTOR
   │          │
   │          ├── retry
   │          └── falha terminal ──► DLQ
   │
   ▼
WAITING_APPROVAL
   │
   ├── rejeitado ──► REJECTED
   │
   └── aprovado
          │
          ▼
       RESUMED
          │
          ▼
       COMPLETED
```

## Aprovação humana

Gates de aprovação são parte do contrato do workflow. Quando uma execução entra em `WAITING_APPROVAL`, o worker não avança até que um usuário com a permissão adequada registre uma decisão.

A decisão, o responsável, o motivo e o momento da aprovação ou rejeição permanecem associados à execução para auditoria.

## IA estruturada

A integração com IA segue uma fronteira de provider e exige resposta estruturada. A saída é validada antes de ser aceita pelo engine.

Isso permite que o workflow trate IA como um componente assistivo e verificável, em vez de entregar a ela o controle do processo. Saídas incompatíveis com o contrato terminam em `FAILED_VALIDATION` e não avançam silenciosamente.

## Retry e DLQ

Falhas transitórias de conectores seguem uma política explícita de novas tentativas. Quando a política é esgotada, a execução termina em `DLQ`.

O reprocessamento cria uma nova execução relacionada por `parent_run_id`. A execução original permanece preservada, permitindo reconstruir o histórico completo do incidente e da recuperação.

## Executar localmente

### Pré-requisitos

- Docker
- Docker Compose

### Inicialização

```bash
cp .env.example .env
docker compose up --build
```

Serviços:

- aplicação web: `http://localhost:3000`
- documentação da API: `http://localhost:8000/docs`
- RabbitMQ Management: `http://localhost:15672`

O ambiente local inicializa banco, API, worker, mensageria e dados necessários para exercitar os fluxos da aplicação sem depender de serviços pagos.

## Estrutura do repositório

```text
apps/
├── api/
│   ├── app/
│   │   ├── contracts/   # JSON Schemas
│   │   ├── engine.py    # execução dos workflows
│   │   ├── worker.py    # consumidor RabbitMQ
│   │   └── ...
│   └── tests/
│
└── web/
    └── src/
        └── app/

docs/                   # arquitetura e decisões técnicas
scripts/                # validações determinísticas
```

## Validação

Validação estrutural e testes do backend:

```bash
python scripts/validate_repo.py
python -m unittest discover apps/api/tests -v
```

Frontend:

```bash
cd apps/web
npm ci
npm run typecheck
npm run build
```

O GitHub Actions executa validação estrutural, testes do backend, instalação determinística das dependências web, auditoria de segurança, typecheck e build.

## Princípios do projeto

- **execução controlada:** nenhuma etapa crítica avança fora das regras do workflow;
- **human-in-the-loop:** aprovações protegidas pertencem a pessoas autorizadas;
- **contratos antes de automação:** entradas e saídas são validadas;
- **IA verificável:** respostas estruturadas são tratadas como dados sujeitos a validação;
- **recuperação explícita:** retries e DLQ fazem parte do modelo de execução;
- **idempotência:** triggers externos não devem duplicar efeitos;
- **auditabilidade:** eventos relevantes permanecem rastreáveis do início ao fim.
