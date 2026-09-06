# ImpactLens AI

<div align="center">

### AI-Powered Code Change Risk, Impact & Test Intelligence

**Understand the real impact of a code change before you merge it.**

[![Bengaluru Tech Week](https://img.shields.io/badge/Bengaluru%20Tech%20Week-2026-blue?style=flat-square)](#)
[![Track 2](https://img.shields.io/badge/Track-2-purple?style=flat-square)](#)
[![Entire Graph](https://img.shields.io/badge/Entire%20Graph-Evidence%20Layer-7c3aed?style=flat-square)](#)
[![Databricks](https://img.shields.io/badge/Databricks-Historical%20Intelligence-ff6b00?style=flat-square)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)](#)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=flat-square&logo=next.js&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3.x-3776ab?style=flat-square&logo=python&logoColor=white)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6?style=flat-square&logo=typescript&logoColor=white)](#)

<br/>

**Diff → Graph Evidence → Risk → Historical Intelligence → Test Ranking → Grounded Explanation → Verification**

</div>

---

## Overview

ImpactLens AI is an AI-powered developer intelligence platform that analyzes code changes and produces an **evidence-backed merge brief**.

A traditional diff answers:

> **What changed?**

ImpactLens answers:

> **What could this change affect, how risky is it, which tests should I run first, how reliable is the analysis, and what still needs verification?**

The product combines:

- **Entire Graph** for structural code evidence
- **Deterministic risk analysis** for reproducible risk scoring
- **Databricks** for historical test-failure intelligence
- **Evidence-ranked test recommendations**
- **Grounded AI explanations**
- **Explicit uncertainty and verification states**
- **Role-based access control**
- **GitHub authentication / demo fallback**
- **Audit-oriented workflows**

The central product principle is:

> **Entire Graph is the evidence layer. ImpactLens is the decision layer.**

---

# Why ImpactLens Exists

Code reviews commonly focus on the changed lines.

But the actual impact of a change can extend far beyond those lines:

```text
                         ┌──────────────────────┐
                         │    Changed Code      │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          Direct Callers      Transitive Users    Shared Types
                 │                  │                  │
                 ▼                  ▼                  ▼
             APIs              Workflows          Other Modules
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    │
                                    ▼
                              Affected Tests
                                    │
                                    ▼
                         Historical Failure Signals
                                    │
                                    ▼
                           Merge Risk / Action
```

A developer should not have to manually reconstruct this dependency chain for every important change.

ImpactLens automates that investigation while making the evidence and uncertainty visible.

---

# The Product in One Diagram

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           IMPACTLENS AI                                   │
│                                                                           │
│               CODE CHANGE RISK • IMPACT • TEST INTELLIGENCE               │
└───────────────────────────────────────────────────────────────────────────┘

                                  CODE CHANGE
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │      Entire Graph      │
                         │                        │
                         │ Search                 │
                         │ Definitions            │
                         │ Callers / Callees      │
                         │ Neighbors              │
                         │ Impact                 │
                         │ Semantic Diff          │
                         └────────────┬───────────┘
                                      │
                                      ▼
                            STRUCTURAL EVIDENCE
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │    Evidence Model      │
                         │                        │
                         │ Source                 │
                         │ Confidence             │
                         │ Completeness           │
                         │ Limitations            │
                         │ Status                 │
                         └────────────┬───────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
          ┌────────────────────┐              ┌────────────────────┐
          │  Deterministic     │              │     Databricks     │
          │    Risk Engine     │              │     Historical     │
          │                    │              │      Evidence      │
          │ Change Size        │              │                    │
          │ Dependency Depth   │              │ Test Runs          │
          │ Consumers          │              │ Failures           │
          │ API Exposure       │              │ Failure Rate       │
          │ Coverage Gap       │              │ Last Result        │
          │ Graph Confidence   │              │ Symbol History     │
          └─────────┬──────────┘              └─────────┬──────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │     Test Ranker        │
                         │                        │
                         │ Relevance              │
                         │ Structural evidence    │
                         │ Historical failures    │
                         │ Verification status    │
                         └────────────┬───────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │    Grounded AI         │
                         │     Explanation        │
                         │                        │
                         │ Explain evidence       │
                         │ Never invent evidence  │
                         └────────────┬───────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │      MERGE BRIEF       │
                         │                        │
                         │ Risk                   │
                         │ Impact                 │
                         │ Tests                  │
                         │ Confidence             │
                         │ Verification           │
                         └────────────────────────┘
```

---

# Core Differentiator

Most developer AI tools try to answer:

> "What does this code do?"

ImpactLens focuses on:

> **"What does this code change mean for the rest of the system?"**

The architecture deliberately separates evidence generation from decision making.

```text
             ENTIRE GRAPH
                  │
                  │ structural evidence
                  ▼
          ┌───────────────┐
          │  IMPACTLENS   │
          │   Evidence    │
          │    Model      │
          └───────┬───────┘
                  │
       ┌──────────┼───────────┐
       │          │           │
       ▼          ▼           ▼
      Risk       Tests      Explain
       │          │           │
       └──────────┼───────────┘
                  ▼
             ACTIONABLE
             MERGE BRIEF
```

This means AI is not allowed to become an ungrounded source of structural facts.

---

# Key Features

## 1. Change Impact Analysis

Identify:

* changed files
* changed symbols
* callers
* callees
* transitive consumers
* affected APIs
* type consumers
* dependency depth
* semantic changes
* file:line provenance

---

## 2. Deterministic Risk Scoring

ImpactLens calculates risk using structured signals rather than allowing an LLM to invent a score.

Example factors:

```text
┌─────────────────────────────────────────────┐
│              RISK SIGNALS                   │
├─────────────────────────────────────────────┤
│ Change Size                                 │
│ Dependency Depth                            │
│ Affected Consumers                           │
│ Public API Exposure                          │
│ Test Coverage Gap                            │
│ Historical Failure Rate                      │
│ Graph Confidence                             │
└─────────────────────────────────────────────┘
                         │
                         ▼
                DETERMINISTIC SCORE
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
            LOW        MEDIUM       HIGH
```

The same structured evidence produces the same risk calculation.

---

## 3. Evidence-Ranked Tests

Instead of recommending every test equally:

```text
                    CHANGE
                       │
                       ▼
                Affected Symbols
                       │
                       ▼
                Graph Relationships
                       │
                       ▼
                Historical Evidence
                       │
                       ▼
                 Test Relevance
                       │
                       ▼
                ┌───────────────┐
                │ TEST RANKING  │
                └───────┬───────┘
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
           HIGH       MEDIUM       LOW
          PRIORITY    PRIORITY    PRIORITY
```

Every recommended test can expose:

* test name
* affected symbol
* evidence chain
* file:line provenance
* graph source
* historical failure rate
* confidence
* completeness
* verification requirement

---

## 4. Historical Test Intelligence

Databricks adds a second dimension to structural analysis.

The graph tells us:

> **What is structurally related?**

Databricks tells us:

> **What has historically been fragile?**

Together:

```text
                 STRUCTURAL SIGNAL
                        │
                        │
                        ▼
                  ┌───────────┐
                  │           │
                  │  IMPACT   │
                  │   LENS    │
                  │           │
                  └─────┬─────┘
                        ▲
                        │
                 HISTORICAL SIGNAL
                        │
                        │
                   DATABRICKS
```

---

# Evidence Model

ImpactLens does not treat every graph result as absolute truth.

Every analysis carries evidence metadata:

```text
┌─────────────────────────────────────┐
│ Evidence                            │
├─────────────────────────────────────┤
│ Source                              │
│ Confidence                          │
│ Completeness                        │
│ Limitations                         │
│ Status                              │
└─────────────────────────────────────┘
```

## Evidence Status

### CONFIRMED

A sufficiently complete and confident structural relationship.

```text
CONFIRMED

compute_risk
     │
     ▼
_run_pipeline
```

The relationship can be presented as confirmed structural evidence.

---

### PARTIAL

The system has useful evidence, but static analysis may not represent the complete runtime relationship.

Examples:

* heuristic relationship
* incomplete dependency information
* parser limitations
* partial repository analysis

ImpactLens communicates caution instead of silently converting uncertainty into certainty.

---

### VERIFY REQUIRED

The relationship cannot be safely resolved.

Instead of fabricating:

```text
DynamicProvider
       │
       ▼
CurrencyService
```

ImpactLens reports:

```text
VERIFY REQUIRED

The structural relationship could not be resolved confidently.

Recommended verification:
    1. Inspect source
    2. Inspect confirmed callers/callees
    3. Run affected tests
    4. Exercise the runtime path
```

The fundamental rule is:

> **Unknown is better than invented.**

---

# Curveball Response

## Graph Is Evidence, Not an Oracle

The Buildathon Curveball invalidated a critical assumption:

> A static graph can always resolve the call chain needed for test ranking.

In real software systems, this can fail because of:

```text
Dynamic dispatch
Reflection
Generated code
Runtime registration
Incomplete dependencies
Parser limitations
```

ImpactLens explicitly models this uncertainty.

---

# Incomplete Analysis Fixture

The project includes:

```text
backend/app/demo_data.py
```

with:

```text
INCOMPLETE_ANALYSIS_FIXTURE
```

The fixture represents a dynamic pricing-provider dispatch where the expected runtime relationship is deliberately absent from the static graph.

The system must not fabricate the missing edge.

Instead:

```text
                Dynamic Provider
                       │
                 NO GRAPH EDGE
                       │
                       ▼
              ┌─────────────────┐
              │ UNKNOWN         │
              │                 │
              │ VERIFY REQUIRED │
              └────────┬────────┘
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Source      Tests     Runtime
         Inspection  Execution  Exercise
```

The regression test verifies that:

* no fabricated relationship is created
* incomplete analysis is explicitly represented
* risk/test output reflects the uncertainty
* verification is required
* fully resolved behavior continues to work

---

# Safe Verification Path

When Graph evidence is incomplete:

```text
1. Inspect changed source
          │
          ▼
2. Inspect confirmed callers / callees
          │
          ▼
3. Run the highest-ranked tests
          │
          ▼
4. Exercise the affected runtime path
          │
          ▼
5. Confirm behavior before merge
```

This makes the system useful even when static analysis cannot provide a complete answer.

---

# Semantic Diff

ImpactLens also uses Entire Graph's semantic diff to understand structural changes rather than relying only on raw text differences.

Example:

```text
backend/app/databricks_adapter.py

+ _real_mode
+ _connection
+ _history_table

~ get_historical_failures
~ get_test_failure_rate
~ get_symbol_failure_rate
~ rank_boost_from_history
~ seed_disclaimer
```

This helps distinguish:

```text
TEXTUAL CHANGE
      │
      ▼
SEMANTIC CHANGE
      │
      ▼
DEPENDENCY / IMPACT
      │
      ▼
RISK / TEST DECISION
```

---

# Real Graph Evidence

Entire Graph can resolve relationships such as:

```text
compute_risk
│
├── callers
│   └── _run_pipeline
│       └── analyze_change
│
├── callees
│   ├── _level_for
│   ├── _max_hop_distance
│   ├── _factor
│   ├── _build_rationale
│   └── get_symbol_failure_rate
│
└── type consumers
    ├── GraphQueryResult
    ├── ChangedFile
    └── RiskResult
```

This is important because the Graph is not merely visualized.

It is used to support actual product decisions.

---

# Databricks Integration

When enabled, ImpactLens uses the Databricks SQL connector to retrieve historical test intelligence.

The configurable history table is:

```text
impactlens_history
```

The data model includes:

```text
repository
symbol
test_name
runs
failures
failure_rate
last_result
```

Example historical evidence:

```text
┌───────────────────────────────────────────────────────────────┐
│ TEST: test_inventory_reservation                              │
├───────────────────────────────────────────────────────────────┤
│ Runs:             25                                          │
│ Failures:          8                                          │
│ Failure Rate:     32%                                         │
│ Last Result:      FAILED                                      │
│                                                               │
│ Recommendation:   HIGH PRIORITY                               │
└───────────────────────────────────────────────────────────────┘
```

Historical evidence is a signal, not proof.

---

# Databricks Fallback

Real Databricks configuration:

```env
USE_REAL_DATABRICKS=true
DATABRICKS_HOST=
DATABRICKS_HTTP_PATH=
DATABRICKS_TOKEN=
DATABRICKS_HISTORY_TABLE=impactlens_history
```

If Databricks is unavailable, ImpactLens falls back to bundled demo history.

The UI explicitly reports:

```text
Bundled demo history (fallback)
```

The application never presents fallback data as live Databricks evidence.

---

# AI Guardrails

AI is used for explanation, not for inventing system structure.

```text
               STRUCTURED EVIDENCE
                       │
                       ▼
              ┌─────────────────┐
              │       AI        │
              │                 │
              │ Summarize       │
              │ Explain         │
              │ Contextualize   │
              └────────┬────────┘
                       │
                       ▼
              GROUNDED RESPONSE
```

The AI layer cannot invent:

```text
❌ Graph edges
❌ Affected files
❌ Symbols
❌ Tests
❌ Failure rates
❌ Risk scores
❌ Historical facts
```

Instead:

```text
Graph → Evidence
Risk Engine → Score
Databricks → Historical Signal
Test Ranker → Priority
AI → Explanation
```

---

# Demo Flow

## Step 1 — Sign In

Use GitHub OAuth when configured.

Otherwise use the clearly labelled local demo fallback.

```text
Sign In
   │
   ├── GitHub OAuth
   │
   └── Local Demo Fallback
```

---

## Step 2 — Select Repository

Confirm:

```text
User
Repository
Role
```

---

## Step 3 — Analyze a Change

Example:

```text
Fix currency rounding in processPayment
```

ImpactLens analyzes the change through the evidence pipeline.

---

## Step 4 — Inspect Risk

The dashboard exposes:

```text
Risk Level
Risk Score
Risk Factors
Affected Consumers
Dependency Depth
API Exposure
Coverage Gap
Historical Failure Signal
Graph Confidence
```

---

## Step 5 — Inspect Dependency Graph

The developer can inspect:

```text
Changed Symbol
     │
     ├── Caller
     ├── Transitive Consumer
     ├── Callee
     ├── Type Consumer
     └── Evidence
```

---

## Step 6 — Inspect Ranked Tests

Review:

```text
Test
Symbol
Evidence Chain
Historical Failure Rate
Graph Source
Confidence
Verification Status
```

---

## Step 7 — Read AI Explanation

The AI explains the structured evidence:

```text
Why is this risky?
What is affected?
What is confirmed?
What is uncertain?
Which tests matter?
What should be verified?
```

---

## Step 8 — Make the Merge Decision

The final action becomes:

```text
REVIEW
  +
TEST
  +
VERIFY
  =
INFORMED MERGE DECISION
```

---

# Dashboard Experience

The application is organized around the engineering decision workflow.

```text
┌─────────────────────────────────────────────────────────────────┐
│ ImpactLens AI                                      User / Role  │
├─────────────────┬───────────────────────────────────────────────┤
│                 │                                               │
│ Overview        │              RISK REPORT                      │
│                 │                                               │
│ Change Analysis │      ┌──────────────────────────┐             │
│                 │      │        HIGH RISK         │             │
│ Dependency Graph│      │          52 / 100        │             │
│                 │      └──────────────────────────┘             │
│ Risk Report     │                                               │
│                 │      Risk Factors                             │
│ Tests           │      • Change size                            │
│                 │      • Dependency depth                       │
│ History         │      • Affected consumers                     │
│                 │      • Public API exposure                    │
│ AI Explanation  │      • Coverage gap                           │
│                 │      • Historical failure rate                │
│ Checkpoints     │      • Graph confidence                      │
│                 │                                               │
│ Settings        │      Ranked Tests                             │
│                 │      ─────────────────────────────────        │
│                 │      1. test_inventory_reservation            │
│                 │      2. test_payment_rounding                 │
│                 │      3. test_checkout_flow                    │
│                 │                                               │
└─────────────────┴───────────────────────────────────────────────┘
```

---

# Role-Based Access Control

ImpactLens supports role-aware workflows.

```text
                         USER
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         VIEWER         DEVELOPER       ADMIN
            │              │              │
            │              ├── Analyze    ├── Analyze
            │              ├── Review     ├── Review
            │              └── Tests      ├── Manage Roles
            │                             └── Audit Logs
            │
            └── Restricted Actions
```

Authorization is enforced by the backend rather than relying only on frontend visibility.

---

# System Architecture

```text
┌──────────────────────────── FRONTEND ────────────────────────────┐
│                                                                  │
│                         Next.js / TypeScript                     │
│                                                                  │
│  Login → Repository → Analysis → Graph → Risk → Tests → AI      │
│                                                                  │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                              HTTP API
                                │
                                ▼
┌──────────────────────────── BACKEND ─────────────────────────────┐
│                                                                  │
│                            FastAPI                               │
│                                                                  │
│  Authentication                                                  │
│  RBAC                                                             │
│  Repository Analysis                                              │
│  Risk Engine                                                      │
│  Test Ranker                                                      │
│  AI Explanation                                                   │
│  Entire Adapter                                                   │
│  Databricks Adapter                                               │
│  Audit / Settings                                                 │
│                                                                  │
└──────────────┬──────────────────────┬──────────────────────┬─────┘
               │                      │                      │
               ▼                      ▼                      ▼
       ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
       │ Entire Graph  │      │  Databricks   │      │   Database    │
       │               │      │               │      │               │
       │ Structural    │      │ Historical    │      │ App State     │
       │ Evidence      │      │ Evidence      │      │ / Demo Data   │
       └───────────────┘      └───────────────┘      └───────────────┘
```

---

# Technology Stack

| Layer                   | Technology                        | Purpose                       |
| ----------------------- | --------------------------------- | ----------------------------- |
| Frontend                | Next.js                           | Developer dashboard           |
| Frontend Language       | TypeScript                        | Type-safe UI                  |
| Styling                 | Tailwind CSS                      | Product UI                    |
| Backend                 | FastAPI                           | REST API                      |
| Backend Language        | Python                            | Analysis and orchestration    |
| Database                | SQLAlchemy / SQLite               | Application state             |
| Structural Intelligence | Entire Graph                      | Code relationships and impact |
| Historical Intelligence | Databricks SQL                    | Test history                  |
| AI                      | Grounded explanation layer        | Evidence explanation          |
| Authentication          | GitHub OAuth                      | Developer authentication      |
| Testing                 | Pytest                            | Backend verification          |
| Version Control         | GitHub                            | Source and submission         |
| Agent Integration       | Entire CLI / Claude configuration | Checkpoint and agent workflow |

---

# Project Structure

```text
ImpactLens/
│
├── .entire/
│   └── Entire configuration
│
├── .claude/
│   └── Agent configuration
│
├── AGENTS.md
├── CLAUDE.md
├── BUILDATHON.md
├── README.md
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── analyze.py
│   │   │   ├── auth.py
│   │   │   ├── repos.py
│   │   │   └── settings_router.py
│   │   │
│   │   ├── ai_explain.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── databricks_adapter.py
│   │   ├── db.py
│   │   ├── demo_data.py
│   │   ├── entire_adapter.py
│   │   ├── main.py
│   │   ├── ranker.py
│   │   ├── risk_engine.py
│   │   └── schemas.py
│   │
│   └── tests/
│       └── test_risk_engine.py
│
└── frontend/
    ├── app/
    │   ├── components/
    │   │   └── DependencyGraph.tsx
    │   ├── dashboard/
    │   │   └── page.tsx
    │   ├── lib/
    │   │   └── api.ts
    │   ├── layout.tsx
    │   └── page.tsx
    │
    └── package.json
```

---

# Quick Start

## Prerequisites

Recommended:

```text
Python 3.x
Node.js
npm
Git
```

For real Entire analysis:

```text
Entire CLI
Entire Graph plugin
```

For real historical intelligence:

```text
Databricks workspace
Databricks SQL endpoint
Databricks SQL connector
```

---

# Backend Setup

```bash
cd backend

python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment configuration:

```bash
copy .env.example .env
```

Start the backend:

```bash
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

---

# Frontend Setup

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# Environment Configuration

## GitHub OAuth

```env
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_OAUTH_REDIRECT_URI=
FRONTEND_URL=http://localhost:3000
```

If these are unavailable, the application can use the clearly labelled local demo authentication path.

---

## Entire

```env
USE_REAL_ENTIRE_CLI=true
ENTIRE_CLI_PATH=entire
```

---

## Databricks

```env
USE_REAL_DATABRICKS=true

DATABRICKS_HOST=
DATABRICKS_HTTP_PATH=
DATABRICKS_TOKEN=

DATABRICKS_HISTORY_TABLE=impactlens_history
```

Never commit credentials.

```text
.env
API keys
OAuth secrets
Databricks tokens
private credentials
```

---

# Entire Graph Workflow

ImpactLens was structured around the Entire workflow.

```text
                    REPOSITORY
                        │
                        ▼
                  ENTIRE LOGIN
                        │
                        ▼
                 ENTIRE MIRROR
                        │
                        ▼
                  ENTIRE CLONE
                        │
                        ▼
               ENABLE CHECKPOINTS
                        │
                        ▼
               INSTALL GRAPH
                        │
                        ▼
                  GRAPH SEARCH
                        │
                        ▼
                  GRAPH IMPACT
                        │
                        ▼
             SOURCE / TEST VERIFY
                        │
                        ▼
                SEMANTIC DIFF
                        │
                        ▼
                 PRODUCT DECISION
```

Useful commands:

```bash
entire status

entire graph version

entire graph search

entire graph def

entire graph neighbors

entire graph impact

entire graph diff

entire graph snapshot
```

The product treats Graph output as evidence rather than an oracle.

---

# Verification

## Backend Tests

```bash
cd backend
python -m pytest -q
```

## Frontend Build

```bash
cd frontend
npm run build
```

The finalized implementation includes automated tests covering:

* deterministic risk behavior
* dependency impact behavior
* historical intelligence integration
* incomplete-analysis behavior
* verification-required states
* Graph integration behavior

---

# Buildathon Track 2 Alignment

ImpactLens directly addresses the Track 2 objective of using Entire Graph's structural view to support a useful decision or action.

The Graph is used to drive:

```text
                    GRAPH
                     │
                     ▼
             AFFECTED SYMBOLS
                     │
                     ▼
            DEPENDENCY IMPACT
                     │
                     ▼
              RISK ANALYSIS
                     │
                     ▼
             TEST PRIORITY
                     │
                     ▼
          VERIFICATION ACTION
                     │
                     ▼
             MERGE DECISION
```

This is not a graph visualization project.

It is a **decision-support product powered by structural graph evidence**.

---

# Evidence Provenance

ImpactLens follows a provenance-first approach.

```text
┌─────────────────────────────────────────────┐
│                 CLAIM                       │
├─────────────────────────────────────────────┤
│ "This test is high priority."               │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             EVIDENCE CHAIN                  │
├─────────────────────────────────────────────┤
│ Changed symbol                              │
│      ↓                                      │
│ Entire Graph relationship                   │
│      ↓                                      │
│ file:line provenance                        │
│      ↓                                      │
│ Historical failure rate                     │
│      ↓                                      │
│ Deterministic ranking                       │
└─────────────────────────────────────────────┘
```

This allows developers to inspect not only the recommendation but also **why the recommendation exists**.

---

# Responsible Use

ImpactLens is a developer decision-support tool.

It does not replace:

* code review
* security review
* CI
* automated testing
* production validation
* runtime observability

Static analysis can miss dynamic behavior.

Historical test failure rates are retrospective signals and should not be used to evaluate individual developers.

The intended workflow is:

```text
              IMPACTLENS
                   │
                   ▼
             CODE REVIEW
                   │
                   ▼
                TESTS
                   │
                   ▼
                  CI
                   │
                   ▼
          RUNTIME VALIDATION
```

---

# Limitations

Known limitations include:

* static analysis may miss dynamic behavior
* generated code may not be fully represented
* reflection can hide relationships
* runtime registration can hide dependencies
* incomplete repositories can reduce graph completeness
* parser failures can degrade confidence
* historical data may be unavailable
* demo history is not production evidence
* risk scores prioritize review; they do not prove correctness

When the system cannot establish a relationship confidently, it prefers:

```text
UNKNOWN
```

over:

```text
FABRICATED CERTAINTY
```

---

# Security

Sensitive configuration must remain outside Git.

Never commit:

```text
.env
Databricks tokens
GitHub client secrets
API keys
private credentials
```

Generated dependencies and local environments should also remain outside the submission repository.

---

# Submission

## Project

**ImpactLens AI**

## Event

**Bengaluru Tech Week Buildathon 2026**

## Track

**Track 2 — Entire Graph**

## Final Git SHA

```text
fcae0b3
```

## Repository

```text
https://github.com/i-Anurag1/ImpactLens
```

## Final Submission Archive

```text
ImpactLens-FINAL.zip
```

---

# Checkpoints

The repository preserves the Entire configuration:

```text
.entire/
AGENTS.md
CLAUDE.md
.claude/
```

The final verification environment did not contain valid Entire checkpoint/session history, so **no checkpoint IDs are fabricated in this repository**.

The correct behavior is to report the actual checkpoint state rather than inventing evidence.

---

# Development Philosophy

ImpactLens is built around five principles:

```text
┌─────────────────────────────────────────────────────┐
│                  IMPACTLENS PRINCIPLES               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Evidence before explanation                     │
│                                                     │
│  2. Deterministic scoring before AI interpretation  │
│                                                     │
│  3. Provenance before confidence                    │
│                                                     │
│  4. Unknown before invented certainty               │
│                                                     │
│  5. Verification before merge                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

# The Decision Loop

```text
             ┌───────────────────┐
             │    CODE CHANGE    │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │  GRAPH EVIDENCE   │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │   RISK ANALYSIS   │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │  TEST PRIORITY    │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │    AI EXPLAINS    │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │     VERIFY        │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │   MERGE DECISION  │
             └───────────────────┘
```

---

# Final Takeaway

A code change is rarely isolated.

ImpactLens AI connects:

```text
CODE
 │
 ├── STRUCTURE
 │
 ├── DEPENDENCIES
 │
 ├── RISK
 │
 ├── HISTORY
 │
 ├── TESTS
 │
 ├── CONFIDENCE
 │
 └── VERIFICATION
```

The result is not another AI-generated code review.

It is an **evidence-backed engineering decision system**.

<div align="center">

## Entire Graph provides the evidence.

## ImpactLens turns evidence into decisions.

### Analyze the change.

### Understand the impact.

### Prioritize the tests.

### Know what is uncertain.

### Verify before you merge.

**ImpactLens AI**

*From code changes to confident engineering decisions.*

</div>
