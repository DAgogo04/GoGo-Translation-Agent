<div align="center">

# 🪿 GoGo-Translation-Agent

**An agentic translation agent that lives inside your office tools and writes back to the multilingual system.**

**入口在办公软件，输出直接回流多语言系统 —— 前端与技术同学都可直接调用。**

<br/>

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-2f6bff)
![PRs](https://img.shields.io/badge/PRs-welcome-12b5a5)
[![Built with Reflection](https://img.shields.io/badge/built%20with-reflection-7c6cff)](#-agentic-reflection)

[English](#) | [简体中文](#-简体中文)

</div>

---

## 📑 Table of Contents

- [Why GoGo](#-why-gogo)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Architecture](#-architecture)
- [Agentic Reflection](#-agentic-reflection)
- [Terminology Governance](#-terminology-governance)
- [Tech Stack](#-tech-stack)
- [Reference Demo](#-reference-demo)
- [Call It As An API](#-call-it-as-an-api)
- [Evaluation](#-evaluation)
- [FAQ](#-faq)
- [Repository Status](#-repository-status)
- [License](#-license)

---

## 🤔 Why GoGo

Localization in a product team is usually a fragmented, human-heavy loop:

> A term shows up in a chat, a Jira ticket, a Confluence page, or a UI screenshot → someone manually copies it, normalizes the English, generates a key, checks for duplicates, files a task, waits for a translator, then pastes the result back.

The end-to-end cycle can take **about a week**; the model layer alone starts around **70% accuracy** and still needs heavy human review.

**GoGo-Translation-Agent collapses this into a single agentic loop.** You talk to it inside your office tool; it does the intake, translation, and terminology governance — and **writes the result straight back into the multilingual system (TMS)**. Frontend developers and tooling can call the same flow as an API.

> **Result (internal pilot):** end-to-end delivery **~1 week → ~1 day**; model-layer accuracy **70% → 96%** on the offline annotated set.
> *(口径：准确率为离线标注评测集上术语/语义正确率；具体数字以实测为准。)*

---

> ### 📦 Repository Status（先读我）
>
> 本仓库是该项目的**设计与技术文档 + 一个可独立运行的参考实现**。
>
> - **生产系统运行在公司内部基础设施上**：钉钉机器人、内部模型网关、TMS 多语言系统与内部模型均为公司专有资产，**无法公开**，因此仓库**不含**可直接对接生产的完整工程代码。
> - **[`reference/`](#-reference-demo) 提供一个简化但可运行的参考实现**，演示核心的 `translate → reflect → improve` 反思循环；只需一个 OpenAI 兼容的 API key 即可运行。
> - 因此本仓库**不能 `clone` 后直接接入生产环境**；但参考实现可直接运行，整套架构可据此复现。
>
> 参考实现仅用于说明思路，**不是**完整生产系统：它使用单一模型，没有状态机、术语库治理、多模型网关、格式保护、钉钉入口与 TMS 写回。

---

## ✨ Key Features

### 🤖 Agentic Intake, Inside Office Tools

- **Entry via office software** (e.g. DingTalk) and other sources — Jira, Confluence, PRD/UI screenshots (OCR).
- **Identity gate** — enterprise email + verification code before any action.
- Recognizes the four common requests right inside the chat:
  1. **新增词条提单** — send a term or a Confluence/Jira link
  2. **补语种** — add translations for an existing key
  3. **单语种修订** — fix one language's translation
  4. **修改默认提单选项** — adjust translation style, deadline, etc.
- Intent recognition → slot filling → English normalization → key generation → duplicate check → task creation.

### 🔁 Agentic Reflection with Self-Optimization

- **Translate → Reflect → Improve** cycle (inspired by Andrew Ng's reflection workflow).
- **Four-dimensional quality evaluation:** accuracy · fluency · style consistency · terminology consistency.
- Dual-model cross-validation; the best result is kept; a quality gate routes to **auto-pass / sample review / forced human review**.
- *Trade-off:* multiple model calls per batch in exchange for significantly higher quality — optimized with caching and small-model routing.

### 📚 Terminology Governance & Data Flywheel

- Standard term base + exception tickets + special-case rules + review highlights.
- **Conflict priority:** official > human-confirmed > latest > most-recent-in-context.
- Human post-edits are automatically written back into term rules and few-shot examples — a **produce → correct → feed back** flywheel.

### 🔒 Format Protection

Automatically protects:

- **Placeholders / variables:** `{variable}`, `{{count}}`, `%s`, `%(name)d`
- **HTML tags:** `<b>`, `<span class="x">`, `<a href="...">`
- **URLs** and **Markdown:** `**bold**`, `*italic*`, `[link](url)`

### 🔌 Writes Back & Callable by Engineers

- Output is written **directly back into TMS / the multilingual system** — no manual copy-paste.
- Frontend developers and tooling can call the **same flow via API** and receive structured results.

---

## ⚙️ How It Works

A state-machine-driven agent — **deterministic skeleton + probabilistic intelligence**:

```
identity verify
      ↓
  ROUTER  (intent + confidence)
      ↓
  PLANNER (slots + steps, ask if missing)
      ↓
  EXECUTOR (normalize → key → dedup → retrieve terms → translate)
      ↓
  CHECKER (4-dim score + cross validation)
      ↓
 auto-pass? ── no ──→ REPLANNER / human review
      ↓ yes
 write back to TMS → update memory & term base
```

The state machine defines legal transitions; the **model cannot skip stages**. Low confidence at any stage triggers clarification or a fallback instead of a guess.

---

## 🏗️ Architecture

The LLM is a **stateless, probabilistic brain**; the **harness** is everything built around it — the runtime loop, tools, context, memory, knowledge, guardrails and observability — that turns it into a reliable agent. Inside the harness the runtime is a **Graph (deterministic state machine)**: the model supplies intelligence, while the state machine decides which stage runs next and prevents skipping.

```mermaid
flowchart TB
  subgraph Input["📥 Entry layer"]
    Chat["Office chat (DingTalk)"]
    Jira["Jira / Confluence"]
    OCR["UI / PRD screenshot (OCR)"]
  end

  subgraph Agent["🧠 Agent layer (state machine)"]
    Router["Router · intent"]
    Planner["Planner · slots"]
    Executor["Executor · tools & translation"]
    Checker["Checker · 4-dim score"]
    Replanner["Replanner / human"]
  end

  subgraph Services["🔧 Supporting services"]
    Terms["Term base / special rules"]
    RAG["RAG · style & glossary"]
    Gateway["Model gateway · multi-model"]
    Mem["Memory · SQLite"]
  end

  subgraph Obs["🔍 Observability & eval"]
    Langfuse["Langfuse · Trace / Eval / Prompt"]
  end

  subgraph Output["📤 Output"]
    TMS["Multilingual system (TMS)"]
    API["Structured API for frontend / tooling"]
  end

  Input --> Router --> Planner --> Executor --> Checker
  Checker -->|pass| TMS
  Checker -->|not pass| Replanner --> Executor
  Executor --> Terms
  Executor --> RAG
  Executor --> Gateway
  Executor --> Mem
  TMS --> API
  Router -. trace .-> Langfuse
  Executor -. trace .-> Langfuse
  Checker -. eval .-> Langfuse
```

### Layer responsibilities

| Layer | Responsibility |
|---|---|
| **Entry** | Collect fragmented text from chat / tickets / pages / OCR; identity verification |
| **Intake Agent** | Intent, slot filling, normalization, key generation & dedup |
| **Translation** | Cross validation, reflection-improvement, 4-dim scoring, human fallback |
| **Terminology** | Term base, exceptions, special rules, conflict priority, write-back |
| **Gateway** | Multi-model routing, rate limiting, retry, fallback, trace logging |
| **Output** | Write back to TMS; expose a structured API |

> **Honesty note — real vs planned.**
> **Implemented (real):** office/Jira/Confluence/OCR entry, intent router, cross-validation, translate→reflect→improve, 4-dim scoring, format protection, term/style retrieval, normalization/key/dedup, write-back to TMS, COMET/BLEU/MQM offline evaluation.
> **Planned / to be added (the complete industry form):** a dedicated Langfuse trace/eval layer, explicit hybrid retrieval + rerank, instruction templates and long-term memory. These are marked as roadmap rather than shipped.

---

## 🔄 Agentic Reflection

The model acts as both translator and reviewer:

**Step 1 — Translate (1× call)**
```
Source: "Welcome to {app_name}"
Initial: "欢迎使用 {app_name}"
```

**Step 2 — Reflect (1× call)**
```
Review across 4 dimensions — accuracy / fluency / style / terminology.
"准确，但'欢迎来到'比'欢迎使用'更贴合 welcoming 的语气。"
```

**Step 3 — Improve (1× call)**
```
Improved: "欢迎来到 {app_name}"
```

Why it works: the same model that translated understands the context, so it can catch subtle fluency and tone issues that a single-pass translation misses.

---

## 📚 Terminology Governance

**Conflict priority:** official > human-confirmed > latest > most-recent-in-context.

Human post-edits become term rules and few-shot examples automatically; exception tickets route to admins for a decision, then flow back to the term base.

---

## 🧰 Tech Stack

| Area | Stack |
|---|---|
| **Agent** | Python, state machine (Router–Planner–Executor–Checker–Replanner), Function Calling |
| **POC** | Low-code / no-code platform for fast validation |
| **RAG** | Document parsing, embedding, hybrid retrieval (vector + BM25), rerank |
| **Models** | Multi-model via gateway; small models for classification, stronger models for planning/generation |
| **Storage** | SQLite (tasks, terms, memory) |
| **Gateway** | Auth, rate limiting, retry, fallback/failover, full-trace logging |
| **Quality** | Offline eval set, regression, human-in-the-loop |
| **Evaluation** | COMET, BLEU / chrF / TER, MQM / DQF (offline labeled set), human sampling |
| **Observability** *(planned)* | Langfuse — full-trace spans, online/offline eval, prompt management |

---

## 🧪 Reference Demo（可运行的参考实现）

`reference/translation_reflection.py` is a self-contained single-file demo of the core **Translate → Reflect → Improve** loop used by the production system.

```bash
# 1. Clone
git clone https://github.com/DAgogo04/GoGo-Translation-Agent.git
cd GoGo-Translation-Agent

# 2. Install
pip install -r reference/requirements.txt

# 3. Point at any OpenAI-compatible endpoint
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional: your gateway
export GOGO_MODEL="gpt-4o-mini"                     # optional

# 4. Run
python reference/translation_reflection.py
```

It prints the first draft, the reflection's findings, and the improved final translation.

> ⚠️ This demo uses a **single model** and only shows the reflection loop. It does **not** include the state machine, managed glossary, format protection, multi-model gateway, DingTalk entry, or TMS write-back — those run on proprietary infrastructure and are documented in [Architecture](#-architecture).

Talking to the production agent in your office tool:
> **你：** 我要新增一个词条 "Welcome to {app_name}"
> **Agent：** 识别意图 → 归一化 → 生成 key 并查重 → 翻译并评分 → 写回 TMS → 回执

---

## 🔌 Call It As An API

Frontend developers and tooling can call the same flow:

```http
POST /api/translate
Content-Type: application/json

{
  "intent": "add_term",
  "source_text": "Welcome to {app_name}",
  "target_languages": ["zh", "ja", "ko"],
  "style": "product_ui"
}
```

Response:

```json
{
  "key": "welcome.to_app_name",
  "translations": {
    "zh": "欢迎来到 {app_name}",
    "ja": "{app_name}へようこそ",
    "ko": "{app_name}에 오신 것을 환영합니다"
  },
  "quality_score": 0.96,
  "written_back": true
}
```

---

## 📊 Evaluation

- **Offline:** gold-standard set across language × content type × difficulty; **COMET** as the primary metric, with BLEU / chrF / TER; MQM/DQF for human classification.
- **Online:** canary release, A/B, behavioral instrumentation, human spot-check.
- **Guardrails:** auto-pass rate, human takeover rate, single-task cost, hallucination rate.
- If offline gains but online doesn't, the eval set is out of distribution — rebuild it from real traffic.

---

## ❓ FAQ

**Why not just let the model decide the next step?**
A pure autonomous loop is probabilistic — it skips steps, loops, and can't be reproduced or audited. A production localization flow needs determinism, so the state machine owns transitions and the model handles semantics.

**Why not end-to-end generation?**
Localization must preserve keys, variables, and formatting. Parameter/tool control keeps changes interpretable and protects structure; end-to-end generation risks corrupting it.

**How do you prevent fake efficiency?**
We report cycle time **together with** first-pass rate and rework rate. Faster output with more rework is not efficiency.

---

## 📦 Repository Status

Production code is proprietary and runs on internal company infrastructure (DingTalk, internal model gateway, TMS, and internal models). This repository ships the design/architecture document above plus the runnable [Reference Demo](#-reference-demo); it cannot be cloned and connected to production directly.

---

## 📄 License

[MIT](LICENSE)

<div align="center">
<b>GoGo-Translation-Agent</b> · office-tool-in, multilingual-system-out · an illustrative agentic project
</div>
