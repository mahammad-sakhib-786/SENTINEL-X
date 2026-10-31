# SENTINEL X

## Unified AI-Powered Cybersecurity and Legal Compliance Platform

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/Status-Working%20Development%20Build-brightgreen)](#project-status)
[![Tests](https://img.shields.io/badge/Tests-11%20passed-success)](#testing)

**SENTINEL X** is a Python and Streamlit application that brings two
complementary risk-analysis capabilities into one interface:

1.  **Cybersecurity Intelligence -- URL Scanner:** performs URL
    validation and heuristic analysis, checks URLhaus threat
    intelligence, and uses structured LLM-powered analysis to produce
    evidence-based investigation results.
2.  **Legal Intelligence -- Contract Compliance Checker:** accepts PDF
    contracts, extracts and splits their text, creates embeddings,
    stores searchable document vectors, retrieves relevant clauses, and
    supports preliminary compliance analysis and question answering.

The goal is to help users identify potential digital-security and
contractual risks, understand the evidence behind findings, and generate
reports. SENTINEL X is a decision-support tool; it does not replace
cybersecurity professionals, lawyers, or formal compliance audits.

> **Important:** A low heuristic score does not prove that a URL is
> safe. A URL not listed by URLhaus is not guaranteed safe. AI-generated
> contract findings are preliminary and should be reviewed by a
> qualified professional.

------------------------------------------------------------------------

## Table of contents

-   [Project overview](#project-overview)
-   [Why SENTINEL X?](#why-sentinel-x)
-   [Main application modules](#main-application-modules)
-   [How the system works](#how-the-system-works)
-   [Architecture](#architecture)
-   [AI models, agents, frameworks, and
    APIs](#ai-models-agents-frameworks-and-apis)
-   [Technology stack](#technology-stack)
-   [Project structure](#project-structure)
-   [Application workflow](#application-workflow)
-   [Installation and setup](#installation-and-setup)
-   [Environment variables and
    secrets](#environment-variables-and-secrets)
-   [Run the application](#run-the-application)
-   [Testing](#testing)
-   [Database and report management](#database-and-report-management)
-   [GitHub and deployment notes](#github-and-deployment-notes)
-   [Security, privacy, and responsible
    use](#security-privacy-and-responsible-use)
-   [Current project status](#current-project-status)
-   [Known limitations and future
    improvements](#known-limitations-and-future-improvements)
-   [Intended users and use cases](#intended-users-and-use-cases)
-   [Disclaimer](#disclaimer)

------------------------------------------------------------------------

## Project overview

Modern organizations face risks from suspicious links, malicious URLs,
phishing attempts, and contractual obligations that may be unclear or
incomplete. These risks are often assessed using separate tools and
workflows.

SENTINEL X brings two distinct workflows together in one Streamlit
application:

  ------------------------------------------------------------------------
  Module            Input             Main processing   Output
  ----------------- ----------------- ----------------- ------------------
  Cybersecurity     URL               URL validation,   Security findings,
  Intelligence                        heuristic checks, evidence review,
                                      URLhaus lookup,   risk assessment,
                                      structured AI     recommendations,
                                      analysis          investigation
                                                        report

  Legal Compliance  PDF contract and  PDF text          Compliance
  Intelligence      user question     extraction,       findings, relevant
                                      clause-aware      evidence, contract
                                      splitting,        Q&A and
                                      embeddings,       preliminary
                                      vector retrieval, analysis
                                      LLM analysis      
  ------------------------------------------------------------------------

The two modules share the application experience, but they use different
processing pipelines and AI configurations. They should not be described
as one model analyzing both types of input.

## Why SENTINEL X?

-   **Unified interface:** access URL investigation and contract review
    from one Streamlit application.
-   **Evidence-oriented analysis:** distinguish observed facts from
    unsupported conclusions.
-   **Threat-intelligence lookup:** enrich URL checks with URLhaus
    results.
-   **Document-grounded question answering:** retrieve relevant contract
    passages before generating answers.
-   **Persistent investigation history:** store and retrieve URL
    investigation records through MySQL.
-   **Report generation:** create downloadable PDF investigation
    reports.
-   **Local legal AI components:** the legal pipeline uses Ollama
    integrations for its language model and embeddings, according to the
    project configuration.

## Main application modules

### 1. Cybersecurity Intelligence -- URL Scanner

The URL Scanner performs a preliminary investigation of a submitted HTTP
or HTTPS URL.

**Processing stages**

1.  **URL validation:** checks whether the submitted value is a usable
    URL and stops invalid input before AI processing.
2.  **Local heuristic analysis:** examines URL characteristics and
    assigns a rule-based score, risk level, and findings.
3.  **Threat-intelligence lookup:** queries URLhaus and records whether
    the URL is listed, not listed, or the service is unavailable.
4.  **Evidence verification:** an AI stage reviews the supplied evidence
    and separates supported claims from unsupported claims.
5.  **Risk assessment:** an AI stage produces a separate risk
    assessment, rationale, and recommendations.
6.  **Security report generation:** an AI stage creates an executive
    summary, limitations, and suggested next steps.
7.  **Persistence and export:** the application can save investigation
    data to MySQL, display it in the interface/history, and generate a
    PDF report.

**Examples of heuristic indicators**

The project's URL analyzer has been described as checking
characteristics such as:

-   IP address used as the hostname
-   Punycode hostname
-   `@` user-information marker
-   unusually many hostname labels
-   suspicious terms in the URL
-   unusually long URLs
-   HTTP rather than HTTPS

These are indicators, not proof of malicious activity. Common words such
as `login` can appear in legitimate URLs.

**Threat-intelligence interpretation**

URLhaus is an external threat-intelligence source used by this project.
Its result is one input to the investigation:

-   `listed`: URLhaus returned a listing.
-   `not_listed`: URLhaus did not return a listing for the lookup.
-   `unavailable`: the lookup could not be completed.

`not_listed` must not be interpreted as a guarantee that a website is
safe.

**Structured AI stages**

The URL analysis workflow uses three structured result types:

-   `EvidenceReview` -- supported claims, unsupported claims, and
    confidence.
-   `RiskAssessment` -- risk score, risk level, rationale, and
    recommendations.
-   `SecurityReport` -- executive summary, limitations, and next steps.

Pydantic schemas are used to validate structured AI outputs. The
heuristic score and AI risk score are separate values and should be
labelled separately in reports.

### 2. Legal Intelligence -- Contract Compliance Checker

The Legal Compliance module is designed to help users inspect PDF
contracts and ask questions about their contents.

**Processing stages**

1.  Upload a contract PDF through the Streamlit interface.
2.  `PyPDFLoader` extracts document text.
3.  The clause splitter creates smaller, clause-aware document chunks.
4.  The configured Ollama embedding model converts text chunks into
    vector representations.
5.  ChromaDB stores the vectors and associated document information.
6.  A retriever searches for relevant chunks when the user asks a
    question or requests analysis.
7.  The configured Ollama chat model processes the retrieved context and
    generates a response.
8.  The application displays compliance-review findings and allows the
    user to ask follow-up questions about the uploaded contract.

**RAG -- Retrieval-Augmented Generation**

The legal question-answering workflow follows the RAG pattern:

-   **Retrieval:** search the vector store for contract passages
    relevant to the user's question.
-   **Augmentation:** provide the retrieved passages as context to the
    language model.
-   **Generation:** generate an answer grounded in the available
    document context.

This approach helps the model refer to the uploaded contract rather than
relying only on general language-model knowledge. Retrieval quality
still depends on PDF text extraction, chunking, embeddings, and the
user's question.

The application also includes compliance-checking logic and evidence
presentation. The exact checklist wording and coverage should be
confirmed against the current `legal_ai/compliance_checker.py`
implementation before being treated as a legal standard.

------------------------------------------------------------------------

## How the system works

### URL investigation flow

``` text
User enters URL
      |
      v
Streamlit URL Investigation page
      |
      v
URL validation and local heuristic analysis
      |
      v
URLhaus threat-intelligence lookup
      |
      v
Investigation orchestrator
      |
      +--> EvidenceReview
      |
      +--> RiskAssessment
      |
      +--> SecurityReport
      |
      v
Pydantic structured-output validation
      |
      +--> Streamlit findings and results
      +--> MySQL investigation history
      +--> ReportLab PDF export
```

The Groq provider is configured as the primary provider in
`agents/provider_client.py`. Gemini is imported as a fallback when the
handled Groq failure conditions occur. The fallback is not a second
analysis stage; it is an alternative model provider for the structured
generation call.

### Contract analysis flow

``` text
User uploads PDF contract
      |
      v
Streamlit Legal Compliance page
      |
      v
PyPDFLoader text extraction
      |
      v
Clause-aware document splitting
      |
      v
Ollama embeddings
      |
      v
ChromaDB vector store
      |
      v
Retriever selects relevant contract chunks
      |
      v
Ollama chat model / LangChain pipeline or agent
      |
      +--> Compliance findings and evidence
      |
      +--> Answers to contract questions
```

### Shared application services

The two workflows are presented through the same Streamlit application.
MySQL is used for URL investigation records and history in the known
implementation. ReportLab is used for PDF report creation in the URL
investigation interface. The legal module uses ChromaDB for
document-vector storage.

Do not assume that MySQL and ChromaDB store the same data: they serve
different purposes.

## Architecture

``` text
                         USER / ANALYST
                               |
                               v
                     STREAMLIT WEB APPLICATION
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
      CYBERSECURITY MODULE              LEGAL COMPLIANCE MODULE
              |                                 |
         URL input                         PDF contract upload
              |                                 |
              v                                 v
       URL validation                    PyPDFLoader
              |                                 |
              v                                 v
      Python URL heuristics              Clause-aware splitter
              |                                 |
              v                                 v
        URLhaus API                       Ollama embeddings
              |                                 |
              v                                 v
     AI investigation orchestrator          ChromaDB
              |                                 |
       +------+------+                          v
       |      |      |                       Retriever
       v      v      v                          |
    Evidence Risk  Security                     v
    Review  Assessment Report              Ollama LLM
       |      |      |                          |
       +------+------+                          v
              |                         Compliance findings
              v                         and contract Q&A
       Pydantic validation
              |
       +------+------------------+
       |                         |
       v                         v
   MySQL history             PDF report export
   and retrieval              (ReportLab)
```

The diagram is a conceptual view of the implemented modules. It does not
imply that every service is shared by both pipelines.

## AI models, agents, frameworks, and APIs

  -----------------------------------------------------------------------
  Component               Where used              Responsibility
  ----------------------- ----------------------- -----------------------
  Groq-hosted LLM         URL Scanner             Primary provider for
                                                  structured AI
                                                  investigation outputs

  Gemini                  URL Scanner             Fallback provider for
                                                  handled Groq failures

  Ollama chat model       Legal Compliance        Local language-model
                                                  processing for contract
                                                  analysis and question
                                                  answering

  Ollama embedding model  Legal Compliance        Converts contract
                                                  chunks and queries into
                                                  vector representations

  ChromaDB                Legal Compliance        Stores and retrieves
                                                  document vectors

  LangChain               Legal Compliance        Connects document
                                                  processing, retrieval,
                                                  prompts, models, and
                                                  agent/tool workflows

  Pydantic                URL Scanner             Validates the shape and
                                                  fields of structured AI
                                                  responses

  URLhaus API             URL Scanner             Supplies external URL
                                                  threat-intelligence
                                                  lookup results

  Streamlit               Whole application       Provides the
                                                  interactive web
                                                  interface
  -----------------------------------------------------------------------

**Model identifier notes**

-   The Groq provider code sets `GROQ_MODEL` from the environment and
    uses `openai/gpt-oss-20b` as its code-level default.
-   The project handoff notes previously reported
    `GEMINI_MODEL=gemini-3.8-flash`; confirm that identifier and its
    current availability before relying on it.
-   The legal project configuration uses `ChatOllama` and
    `OllamaEmbeddings`. The previously reported local model names were
    `llama3.2:3b` and `nomic-embed-text`; verify the actual names in
    `legal_ai/config.py`, `legal_ai/embeddings.py`, and the local Ollama
    installation before changing them.

An LLM is the language model. An agent or orchestrator coordinates tasks
and tool use. An API connects the application to an external service. An
embedding model creates vectors. A vector database stores and searches
those vectors. These are different components, not interchangeable names
for the same technology.

## Technology stack

  -----------------------------------------------------------------------
  Area                                Technology
  ----------------------------------- -----------------------------------
  Programming language                Python

  Web interface                       Streamlit

  URL parsing and heuristics          Python standard library and project
                                      security modules

  Threat intelligence                 URLhaus

  URL AI provider                     Groq, with Gemini fallback

  Structured data validation          Pydantic

  Legal document loading              LangChain community PDF loader /
                                      PyPDF

  Legal orchestration and RAG         LangChain

  Local LLM runtime                   Ollama

  Embeddings                          Ollama embedding integration

  Vector database                     ChromaDB through `langchain-chroma`

  Relational database                 MySQL

  MySQL connector                     `mysql-connector-python`

  PDF generation                      ReportLab

  Environment configuration           `python-dotenv`

  Automated tests                     pytest
  -----------------------------------------------------------------------

Versions observed in the development environment included Streamlit
1.65.0, LangChain 1.4.7, langchain-community 0.4.2, langchain-chroma
1.1.0, ChromaDB 1.5.9, pypdf 6.21.4, sentence-transformers 6.2.0,
FastMCP 4.1.4, google-genai 2.29.0, Groq 1.7.0, mysql-connector-python
26.10.0, python-dotenv 1.2.4, langchain-ollama 1.1.0, and ReportLab
5.1.0. These are observed environment versions, not a promise that every
version is pinned in the repository.

## Project structure

The following structure is based on the project paths and imports shown
during development. Your local repository may contain additional files,
test utilities, or backup files.

``` text
SENTINEL-X/
|
|-- app.py
|-- database.py
|-- requirements.txt
|-- .gitignore
|-- .env.example              # recommended safe template; create if absent
|
|-- agents/
|   |-- __init__.py
|   |-- schemas.py
|   |-- provider_client.py
|   |-- gemini_client.py
|   |-- orchestrator.py
|
|-- security/
|   |-- __init__.py
|   |-- url_analyzer.py
|   |-- urlhaus_client.py
|
|-- legal_ai/
|   |-- agent.py
|   |-- config.py
|   |-- embeddings.py
|   |-- document_loader.py
|   |-- clause_splitter.py
|   |-- vector_store.py
|   |-- retriever.py
|   |-- compliance_checker.py
|   |-- rag_pipeline.py
|   |-- tools.py
|
|-- tests/
|   |-- test_agents.py
|   |-- test_compliance_checker.py
|   |-- test_rag_pipeline.py
|   |-- test_retriever.py
|   |-- test_splitter.py
|
|-- .streamlit/
|   |-- config.toml
|
|-- data/
    |-- chroma_db/             # local vector-store data; do not commit
    |-- legal_documents/       # local uploaded documents; do not commit private files
```

Some paths in the tree are generated or local runtime paths and may not
be tracked by Git. Keep private documents, local databases, model
caches, and credentials out of the public repository.

### Important source files

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `app.py`                            Main Streamlit interface,
                                      navigation, URL investigation UI,
                                      legal compliance UI, history,
                                      status, and PDF report presentation

  `database.py`                       MySQL connection and investigation
                                      persistence/retrieval/deletion

  `agents/orchestrator.py`            Coordinates URL analysis, URLhaus
                                      lookup, and the sequential AI
                                      stages

  `agents/provider_client.py`         Groq primary structured-generation
                                      provider and Gemini fallback

  `agents/gemini_client.py`           Gemini structured-generation client

  `agents/schemas.py`                 Pydantic schemas for structured
                                      URL-analysis results

  `security/url_analyzer.py`          URL validation and local heuristic
                                      analysis

  `security/urlhaus_client.py`        URLhaus API integration

  `legal_ai/document_loader.py`       PDF document loading

  `legal_ai/clause_splitter.py`       Clause-aware text splitting

  `legal_ai/embeddings.py`            Embedding model configuration

  `legal_ai/vector_store.py`          Chroma vector-store creation and
                                      access

  `legal_ai/retriever.py`             Retrieval of relevant document
                                      chunks

  `legal_ai/rag_pipeline.py`          Contract question-answering
                                      pipeline

  `legal_ai/agent.py`                 Legal agent setup

  `legal_ai/tools.py`                 Tools available to the legal agent

  `legal_ai/compliance_checker.py`    Contract compliance checking logic
  -----------------------------------------------------------------------

## Application workflow

The Streamlit application has been observed to include these main
sections:

1.  **Overview / Security Command Center:** displays a dashboard and
    recent investigation information.
2.  **URL Investigation:** accepts a URL, runs the security workflow,
    and displays local findings, threat intelligence, AI findings,
    evidence verification, executive summary, and report download.
3.  **Legal Compliance Agent:** accepts a PDF contract, processes it,
    displays compliance review results, and supports questions about the
    document.
4.  **Investigation History:** lists stored URL investigations and
    provides individual or bulk deletion controls.
5.  **System Status:** displays database, retention, report-export,
    URLhaus, and AI-provider configuration status.

The exact labels and navigation order should be checked in the current
`app.py`, as the interface can change during development.

## Installation and setup

### Prerequisites

Install or configure:

-   Windows, macOS, or Linux
-   Python version compatible with the installed project dependencies
    (Python 3.14.9 was reported in the development environment)
-   Git
-   MySQL server and a database account with permissions to create/use
    the project database
-   Ollama installed and running for the legal AI workflow
-   The required local Ollama chat and embedding models
-   API credentials for Groq, Gemini fallback, and URLhaus, as
    configured by the project

### 1. Clone the repository

``` bash
git clone https://github.com/mahammad-sakhib-786/SENTINEL-X.git
cd SENTINEL-X
```

### 2. Create and activate a virtual environment

Windows PowerShell:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you already maintain a working virtual environment outside the
repository, activate that environment instead of creating another one.

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Dependency-file note:** the `requirements.txt` content shown during
development listed only `langchain`, `langchain-community`,
`langchain-chroma`, `chromadb`, `pypdf`, `sentence-transformers`, and
`fastmcp`. The application imports additional packages, including
Streamlit, ReportLab, MySQL Connector, python-dotenv, Groq, Google
GenAI, Requests, and LangChain Ollama/text-splitter integrations. Make
sure the committed requirements file includes every package imported by
the current code. A successful installation from the short list alone
has not been established.

A possible additional installation command, if these dependencies are
missing, is:

``` powershell
python -m pip install streamlit reportlab mysql-connector-python python-dotenv groq google-genai requests langchain-ollama langchain-text-splitters pytest
```

Review the project's actual imports and pin tested versions before using
this as a production dependency lock.

### 4. Configure MySQL

Start the MySQL server and create the database expected by the
application. The development configuration used the database name
`sentinel_x`.

Example SQL:

``` sql
CREATE DATABASE sentinel_x;
```

Configure the database host, port, username, password, and database name
using the variable names expected by `database.py`. Do not assume the
example names below match the current implementation; inspect
`database.py` and use its actual environment-variable names.

### 5. Configure Ollama for the legal module

Start Ollama and make sure the model names configured in
`legal_ai/config.py` and `legal_ai/embeddings.py` are available locally.

Example commands for the model names previously reported in the project
environment:

``` powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama list
```

These commands are examples based on previously reported model names. If
the Python configuration specifies different model identifiers, pull
those exact models instead.

### 6. Configure environment variables

Create a local `.env` file in the project root. Add the exact variable
names read by:

-   `agents/provider_client.py`
-   `agents/gemini_client.py`
-   `security/urlhaus_client.py`
-   `database.py`

The URL AI provider code explicitly reads `GROQ_API_KEY` and
`GROQ_MODEL`. The project also uses Gemini, URLhaus, and MySQL
configuration. Check the source files for their exact variable names.

Example template only --- replace or extend names to match the code:

``` dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_gemini_model_name

# Add the exact URLhaus and MySQL variable names
# expected by security/urlhaus_client.py and database.py.
```

Never commit `.env`. Commit a redacted `.env.example` containing
placeholders only, if useful.

## Environment variables and secrets

Keep all of the following out of Git:

-   `.env` and files containing real credentials
-   Groq, Gemini, and URLhaus API keys
-   MySQL passwords and private connection strings
-   Streamlit secrets
-   Uploaded contracts and confidential documents
-   ChromaDB local persistence files
-   Local database files and generated reports containing private
    information

The repository `.gitignore` should exclude `.env`, virtual environments,
Python caches, Streamlit secrets, local ChromaDB data, uploaded contract
PDFs, and generated/private reports. If a secret was ever committed,
removing it from the latest commit is not sufficient: rotate the
credential and follow GitHub's guidance for removing exposed secrets
from repository history.

## Run the application

Activate the environment, make sure MySQL and Ollama are available where
required, then run:

``` powershell
python -m streamlit run app.py
```

Streamlit prints a local address, usually:

``` text
http://localhost:8501
```

Open that address in a browser.

### Suggested demonstration sequence

1.  Open the Overview dashboard.
2.  Navigate to URL Investigation and submit a test URL you are
    authorized to assess.
3.  Review local heuristic findings and URLhaus status.
4.  Review the AI evidence verification, risk assessment,
    recommendations, and executive summary.
5.  Download and inspect the generated PDF report.
6.  Open Legal Compliance Agent and upload a non-confidential sample
    contract.
7.  Wait for document extraction, chunking, embedding, and vector-store
    creation to complete.
8.  Review the compliance findings and evidence displayed by the
    application.
9.  Ask a question whose answer can be found in the uploaded contract.
10. Open Investigation History and inspect saved URL investigation
    records.
11. Test individual or bulk deletion only with disposable test records.
12. Open System Status and review the reported service configuration.

Use sample or synthetic data for demonstrations. Do not upload
confidential contracts or investigate URLs without authorization.

## Testing

Run the test suite from the project root:

``` powershell
python -m pytest -q
```

For verbose output:

``` powershell
python -m pytest -v
```

A development terminal output shared on **31 October 2026** showed:

``` text
11 passed, 15 warnings
```

The warnings included deprecation notices from LangSmith,
`langchain-community`, and ChromaDB dependencies. This confirms that the
tests present in that workspace passed at that checkpoint. It does not
prove production readiness, complete UI coverage, provider availability,
or the correctness of every possible URL and contract.

Compile-check example:

``` powershell
python -m compileall .
```

## Database and report management

### MySQL investigation history

The known database configuration uses:

-   Database: `sentinel_x`
-   Table: `investigations`
-   Retention setting: newest 30 reports
-   Operations exposed by `database.py`: connection, initialization,
    save, retrieve, individual delete, and bulk delete

The URL investigation history is intended to make previous reports
accessible from the Streamlit interface.

### ChromaDB legal document storage

ChromaDB is used by the legal RAG pipeline to store and retrieve
document embeddings. Treat its local persistence directory as generated
application data. Do not commit it to Git, and do not assume that it is
backed up merely because the source code is in GitHub.

### PDF reports

ReportLab is used to create downloadable PDF investigation reports. A
PDF generation test was successful in the development history. A prior
PDF review identified typography/encoding issues affecting some hyphens
and punctuation, so inspect exported PDFs before presenting them as
final deliverables.

## GitHub and deployment notes

GitHub repository:

**https://github.com/mahammad-sakhib-786/SENTINEL-X**

To publish later source changes:

``` powershell
git status
git add .
git commit -m "Describe your changes"
git push origin main
```

Before staging, review `git status` and confirm that `.env`,
credentials, private PDFs, uploaded contracts, local vector-store data,
and generated reports are ignored.

### Local access versus public deployment

Running Streamlit locally makes the app available on the local machine.
A temporary tunnel such as ngrok can expose a development server for a
demonstration, but it is not a production deployment strategy. Before
exposing the application publicly, implement authentication,
authorization, rate limiting, secure secret handling, upload validation,
network restrictions, logging controls, and a secure hosting/database
configuration.

Do not expose a development instance containing private contracts, API
credentials, or an unrestricted database.

## Security, privacy, and responsible use

-   Only investigate URLs when you have authorization or a legitimate
    security purpose.
-   Do not treat heuristic scores as probabilities.
-   Do not treat a URLhaus `not_listed` response as proof of safety.
-   Review AI-supported claims against the underlying evidence.
-   Do not use AI-generated contract analysis as legal advice or as a
    substitute for a lawyer.
-   Do not upload confidential, personal, privileged, or regulated
    documents unless the deployment and data-handling arrangements have
    been approved for that information.
-   Keep credentials in environment variables or a suitable secrets
    manager.
-   Restrict access to reports and uploaded documents.
-   Apply retention and deletion policies appropriate to the data.
-   Test provider failures and unavailable external services.

## Current project status

The status below reflects the source paths, terminal output, dependency
information, and development notes shared during the project
conversation. It is not a fresh inspection of the developer's Windows
computer or GitHub repository.

### Implemented or demonstrated

-   [x] Streamlit application with dashboard and multiple workspaces.
-   [x] URL input validation and local heuristic analysis.
-   [x] URLhaus threat-intelligence integration.
-   [x] Structured URL AI workflow with evidence review, risk
    assessment, and report generation stages.
-   [x] Groq primary provider and Gemini fallback logic in the URL AI
    provider layer.
-   [x] Pydantic schemas for structured AI outputs.
-   [x] MySQL-backed URL investigation persistence and history.
-   [x] Individual and bulk investigation deletion controls in the
    interface.
-   [x] PDF report generation with ReportLab.
-   [x] Legal PDF loading and clause-aware splitting modules.
-   [x] Legal vector-store and retrieval modules using ChromaDB.
-   [x] Ollama integration imports/configuration for legal chat and
    embeddings.
-   [x] Legal compliance checking and contract question-answering
    modules.
-   [x] Automated test suite: 11 tests passed in the latest test output
    shared in the conversation.
-   [x] `.gitignore` configured to exclude secrets, local data, and
    private/generated PDF files.
-   [x] Git commits created and the `origin` remote configured; a push
    was later rejected by GitHub email privacy protection. The user then
    configured a GitHub noreply email, but a successful final push after
    that change was not shown in the latest shared terminal output.

### Requires confirmation or further work

-   [ ] Confirm the final GitHub push succeeded after the noreply email
    change.
-   [ ] Verify the complete repository tree and ensure every runtime
    dependency is declared in `requirements.txt`.
-   [ ] Verify exact model identifiers and local Ollama model
    availability.
-   [ ] Re-test Groq-to-Gemini fallback using controlled failure tests.
-   [ ] Test MySQL schema migrations, CRUD operations, and 30-report
    retention.
-   [ ] Confirm whether report limitations and next steps are stored for
    historical records; a prior project checkpoint identified a possible
    database-schema gap.
-   [ ] Review and correct PDF font/encoding issues.
-   [ ] Expand tests for URL heuristic edge cases, URLhaus failures,
    provider fallback, database operations, PDF output, and Streamlit
    workflows.
-   [ ] Perform security review before exposing the app outside a
    trusted development environment.
-   [ ] Validate legal analysis against expert-reviewed sample contracts
    and clearly document its limits.
-   [ ] Add production authentication, authorization, monitoring,
    backups, and deployment configuration if required.

**Project maturity:** SENTINEL X is a working development project with
two implemented application modules and a passing test suite at the
reported checkpoint. It should not yet be described as a fully audited,
production-certified cybersecurity or legal-compliance platform.

## Intended users and use cases

  -----------------------------------------------------------------------
  User / sector                       Potential use
  ----------------------------------- -----------------------------------
  Security analysts                   Preliminary URL triage and
                                      evidence-oriented investigation
                                      reports

  IT teams                            Initial review of suspicious links
                                      reported by staff

  Small and medium businesses         A single interface for basic URL
                                      checks and preliminary contract
                                      review

  Legal and procurement teams         Locate relevant contract passages
                                      and flag areas for human review

  Compliance teams                    Support document review workflows
                                      and organize findings

  Educational institutions            Demonstrate URL analysis, LLM
                                      orchestration, RAG, embeddings, and
                                      vector databases

  Researchers and students            Study the integration of
                                      cybersecurity and legal-document AI
                                      workflows
  -----------------------------------------------------------------------

These are potential applications, not claims that the project has been
independently validated for regulated or enterprise production use.

## Known limitations and future improvements

1.  **Threat-intelligence coverage:** URLhaus is the known integrated
    source. Additional reputable sources could be considered after
    reliability and licensing review.
2.  **Risk-score calibration:** heuristic and AI scores are not
    demonstrated to be calibrated probabilities. Explain their methods
    and keep them separate.
3.  **Provider resilience:** add automated tests for timeouts, rate
    limits, malformed model output, and fallback behavior.
4.  **Legal evaluation:** test PDF extraction, clause splitting,
    retrieval relevance, answer grounding, and compliance findings
    against expert-reviewed examples.
5.  **Database completeness:** confirm historical storage of all report
    fields, including limitations and next steps, and apply safe
    migrations if needed.
6.  **PDF quality:** use fonts with appropriate Unicode coverage and
    test punctuation, line wrapping, and page breaks.
7.  **Dependency management:** complete and pin the requirements file;
    consider a reproducible lock file.
8.  **Application security:** add authentication, role-based access,
    upload limits, safe file handling, and production secret management.
9.  **Observability:** add structured, secret-safe logs and clear health
    checks for MySQL, Ollama, and external providers.
10. **Deployment:** define a secure deployment environment, backups,
    monitoring, and a documented update process.

## Disclaimer

SENTINEL X provides preliminary, AI-assisted security investigation and
contract-document analysis. It may produce incomplete, incorrect, or
misleading results. A URL that is not listed by a threat-intelligence
source is not necessarily safe, and a low heuristic score is not proof
that a website is benign. Contract analysis is not legal advice, a legal
opinion, or a certification of compliance. Users must verify findings
and consult qualified cybersecurity, legal, and compliance professionals
before making consequential decisions.

------------------------------------------------------------------------

**Maintained by:** https://github.com/mahammad-sakhib-786/
**Repository:** https://github.com/mahammad-sakhib-786/SENTINEL-X
