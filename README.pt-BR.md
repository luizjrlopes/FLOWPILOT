# FlowPilot AI

[English](README.md) | [Português](README.pt-BR.md)

**FlowPilot AI** é uma plataforma de automação de workflows orientada a execução controlada, rastreabilidade e aprovação humana. O sistema combina definições declarativas em YAML, processamento assíncrono, etapas determinísticas, integração com IA estruturada, políticas de retry, DLQ e trilha completa de evidências.

A arquitetura mantém decisões críticas sob controle da aplicação: a IA pode extrair, classificar e estruturar informações, mas não ignora contratos, não aprova etapas protegidas e não altera silenciosamente o estado de uma execução.

## Visão geral

Principais capacidades:

- catálogo de workflows com definições YAML versionadas;
- criação e atualização de workflows com validação de contrato;
- disparo manual e por webhook idempotente;
- validação de entrada antes da execução;
- etapas determinísticas de transformação e decisão;
- extração e classificação por IA com saída estruturada;
- validação Pydantic antes de transições dependentes de IA;
- conectores desacoplados com política de retry;
- gates de aprovação humana com bloqueio real da execução;
- retomada segura após aprovação;
- rejeição terminal com motivo registrado;
- processamento assíncrono com RabbitMQ;
- Dead Letter Queue com reprocessamento explícito;
- nova execução no reprocessamento da DLQ, preservando a original;
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

Quando uma execução entra em `WAITING_APPROVAL`, o worker não avança até que um usuário com a permissão adequada registre uma decisão. Responsável, motivo e momento da aprovação/rejeição permanecem associados à execução.

## IA estruturada

A integração com IA segue uma fronteira de provider e exige resposta estruturada. A saída é validada antes de ser aceita pelo engine. Saídas incompatíveis com o contrato terminam em `FAILED_VALIDATION`.

## Retry e DLQ

Falhas transitórias seguem política explícita de novas tentativas. Quando a política é esgotada, a execução termina em `DLQ`. O reprocessamento cria nova execução relacionada por `parent_run_id`, preservando a original.

## Executar localmente

```bash
cp .env.example .env
docker compose up --build
```

- Web: `http://localhost:3000`
- API: `http://localhost:8000/docs`
- RabbitMQ Management: `http://localhost:15672`

## Estrutura do repositório

```text
apps/
├── api/
│   ├── app/
│   │   ├── contracts/
│   │   ├── engine.py
│   │   ├── worker.py
│   │   └── ...
│   └── tests/
└── web/
    └── src/
        └── app/
docs/
scripts/
```

## Validação

```bash
python scripts/validate_repo.py
python -m unittest discover apps/api/tests -v
cd apps/web
npm ci
npm run typecheck
npm run build
```

O GitHub Actions executa validação estrutural, testes do backend, instalação determinística das dependências web, auditoria de segurança, typecheck e build.

## Princípios do projeto

- **execução controlada**;
- **human-in-the-loop**;
- **contratos antes de automação**;
- **IA verificável**;
- **recuperação explícita**;
- **idempotência**;
- **auditabilidade**.
