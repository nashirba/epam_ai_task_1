# Personal Investment-Planning Assistant — Pre-Draft Implementation Plan (Days 1-7, Working Draft Only)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Scope note:** This is the first of two implementation plans. It intentionally targets a working local draft by Fri 2026-05-08. Final capstone compliance items are tracked for the Days 8-16 post-draft plan. **Do not submit the repo after Days 1-7; this is a draft milestone only.**

**Goal:** Ship a working, end-to-end Personal Investment-Planning Assistant draft by Fri 2026-05-08: scaffold → real data corpus → Weaviate-backed hybrid RAG → custom + consumed MCP → 3 agents on a typed message bus → Streamlit UI → minimal smoke tests. Runs locally as a real application: Weaviate in Docker via `docker compose up -d weaviate`, Python app via `uv run streamlit run src/pia/ui/app.py`. No cloud deployment is required.

**Architecture:** Single Python service. 3 agents (Portfolio/Market/Planner) communicate over an in-process Pydantic message bus. Planner orchestrates; Portfolio does RAG over Weaviate; Market calls MCP tools. LLM and embedding providers are env-swappable. Custom `kz-data` MCP server exposes 4 tools backed by snapshot files. Data corpus is real and snapshotted.

**Tech Stack:** Python 3.12, uv, Pydantic v2, LiteLLM, Weaviate (Docker), sentence-transformers (BAAI/bge-m3), FastMCP, official `mcp` SDK, Streamlit, Langfuse, pytest, ruff.

**Reference:** Spec at `docs/superpowers/specs/2026-05-02-personal-investment-assistant-design.md`. ADRs 0001-0008 in `docs/decisions/`. Constraints in `docs/requirements_addendum.md`.

---

## Project layout (locked in Phase 0; do not deviate)

```
.
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── data/
│   ├── personal/
│   │   ├── holdings.json
│   │   ├── plan.md
│   │   └── notes/                          # *.md
│   └── public/
│       ├── news/                           # *.md with YAML front-matter
│       ├── bank_rates/                     # *.json
│       ├── real_estate/almaty/             # *.json
│       ├── kase/                           # *.json
│       └── nbk/                            # *.json (rate history, FX, gold)
├── src/pia/
│   ├── __init__.py
│   ├── config.py                           # pydantic-settings
│   ├── messages.py                         # AgentMessage and payload types
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py                       # LiteLLM wrapper + retry-repair
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── base.py                         # EmbeddingProvider protocol
│   │   ├── litellm.py
│   │   └── local.py                        # sentence-transformers
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── loaders.py                      # one loader per source type
│   │   ├── store.py                        # Weaviate v4 wrapper
│   │   └── retrieve.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py                       # FastMCP entrypoint
│   │   ├── client.py                       # MCP client wrappers
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── nbk.py
│   │       ├── fx.py
│   │       ├── kase.py
│   │       └── deposits.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                         # BaseAgent + tool-call loop
│   │   ├── portfolio.py
│   │   ├── market.py
│   │   └── planner.py
│   ├── safety/
│   │   ├── __init__.py
│   │   └── disclaimer.py                   # the rest in post-draft
│   └── ui/
│       ├── __init__.py
│       └── app.py                          # Streamlit entry
├── scripts/
│   ├── ingest.py                           # CLI: ingest data/ → Weaviate
│   ├── snapshot_news.py                    # one-shot scraper
│   └── snapshot_rates.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── docs/                                   # already populated
```

Module size discipline: any single file growing past ~300 LOC during this plan is a smell — split it.

---

## Phase 0 — Day 1 (Sat 2026-05-02): Scaffold and tooling

**Goal of phase:** A repo that boots: Weaviate up via Docker, `uv sync` works, `pytest` runs, `ruff check` clean, settings module reads `.env`, README has a Quickstart that a stranger can follow. Commit at end.

### Task 0.1: Create directory skeleton

**Files:**
- Create: directory tree under `src/pia/`, `tests/`, `data/personal/notes/`, `data/public/{news,bank_rates,real_estate/almaty,kase,nbk}`, `scripts/`
- Create: empty `__init__.py` files in every Python package directory.

- [ ] **Step 1: Create directories**

```bash
cd /Users/nashirba/epam_course/task_1
mkdir -p src/pia/{llm,embeddings,rag,mcp/tools,agents,safety,ui} \
         tests/{unit,integration,fixtures} \
         data/personal/notes \
         data/public/{news,bank_rates,real_estate/almaty,kase,nbk} \
         scripts
```

- [ ] **Step 2: Add `__init__.py` files**

```bash
for d in src/pia src/pia/llm src/pia/embeddings src/pia/rag src/pia/mcp src/pia/mcp/tools src/pia/agents src/pia/safety src/pia/ui tests tests/unit tests/integration tests/fixtures; do
  touch "$d/__init__.py"
done
```

- [ ] **Step 3: Verify with tree**

```bash
find src tests data scripts -type d | sort
```
Expected: shows the directories above.

### Task 0.2: `pyproject.toml`

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "pia"
version = "0.1.0"
description = "Personal Investment-Planning Assistant — KZ-resident multi-agent RAG+MCP capstone"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.7",
  "pydantic-settings>=2.3",
  "litellm>=1.55",
  "weaviate-client>=4.9",
  "sentence-transformers>=3.0",
  "fastmcp>=0.4",
  "mcp>=1.0",
  "streamlit>=1.39",
  "langfuse>=2.50",
  "httpx>=0.27",
  "tenacity>=9.0",
  "python-dotenv>=1.0",
  "rich>=13.7",
  "typer>=0.12",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "pytest-mock>=3.14",
  "pytest-cov>=5.0",
  "ruff>=0.6",
  "mypy>=1.11",
  "respx>=0.21",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pia"]

[tool.pytest.ini_options]
addopts = "-q --strict-markers"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
  "smoke: end-to-end smoke tests",
  "integration: requires Weaviate or external services",
  "adversarial: safety/jailbreak tests",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "ANN", "RUF"]
ignore = ["ANN101", "ANN102", "ANN401"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN"]
```

- [ ] **Step 2: Sync the env**

```bash
cd /Users/nashirba/epam_course/task_1
uv venv
uv sync --all-extras
```
Expected: creates `.venv/`, installs deps. No errors.

- [ ] **Step 3: Run ruff baseline**

```bash
uv run ruff check
```
Expected: `All checks passed!` (no `.py` files yet).

### Task 0.3: `.env.example` and `.gitignore`

**Files:**
- Create: `.env.example`
- Modify: `.gitignore` (already exists — append entries)

- [ ] **Step 1: Write `.env.example`**

```dotenv
# ---- LLM provider (LiteLLM model string; see ADR 0006) ----
LLM_MODEL=gemini/gemini-2.0-flash
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048

# Provider API keys (uncomment whichever LLM_MODEL you point at)
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
# GOOGLE_API_KEY=
# GROQ_API_KEY=

# ---- Embeddings (see ADR 0008) ----
EMBEDDING_PROVIDER=local        # one of: openai | gemini | local
EMBEDDING_MODEL=BAAI/bge-m3     # used when EMBEDDING_PROVIDER=local

# ---- Weaviate (see ADR 0007) ----
WEAVIATE_HOST=localhost
WEAVIATE_HTTP_PORT=8080
WEAVIATE_GRPC_PORT=50051

# ---- MCP ----
TAVILY_API_KEY=
KZ_DATA_MCP_PATH=src/pia/mcp/server.py

# ---- Observability ----
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

# ---- App ----
DEBUG=false
DATA_DIR=./data
RATE_LIMIT_PER_MINUTE=10
```

- [ ] **Step 2: Append to `.gitignore`**

Verify the existing `.gitignore` contains entries for `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `.pytest_cache/`. If any are missing, append them. Do not commit `.env`.

- [ ] **Step 3: Confirm `.env` is ignored**

```bash
echo "LLM_MODEL=test" > .env
git -C /Users/nashirba/epam_course/task_1 status --short .env
```
Expected: no output (file is ignored). Then `rm .env`.

### Task 0.4: Settings module (TDD)

**Files:**
- Create: `src/pia/config.py`
- Test: `tests/unit/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_config.py`:
```python
from pia.config import Settings


def test_settings_loads_defaults(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.llm_model == "gemini/gemini-2.0-flash"
    assert s.embedding_provider == "local"
    assert s.weaviate_http_port == 8080
    assert s.rate_limit_per_minute == 10


def test_settings_respects_env(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.llm_model == "anthropic/claude-sonnet-4-6"
    assert s.embedding_provider == "openai"
```

- [ ] **Step 2: Run test — expect failure**

```bash
uv run pytest tests/unit/test_config.py -v
```
Expected: ImportError / ModuleNotFoundError on `pia.config`.

- [ ] **Step 3: Implement `Settings`**

`src/pia/config.py`:
```python
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LLM
    llm_model: str = "gemini/gemini-2.0-flash"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048

    # Embeddings
    embedding_provider: Literal["openai", "gemini", "local"] = "local"
    embedding_model: str = "BAAI/bge-m3"

    # Weaviate
    weaviate_host: str = "localhost"
    weaviate_http_port: int = 8080
    weaviate_grpc_port: int = 50051

    # MCP
    tavily_api_key: str | None = None
    kz_data_mcp_path: str = "src/pia/mcp/server.py"

    # Observability
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None

    # App
    debug: bool = False
    data_dir: Path = Field(default=Path("./data"))
    rate_limit_per_minute: int = 10


def get_settings() -> Settings:
    """Singleton-ish accessor — Streamlit reloads import this."""
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/unit/test_config.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Lint**

```bash
uv run ruff check src tests
```
Expected: clean.

### Task 0.5: `docker-compose.yml` with Weaviate

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write the compose file**

```yaml
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.27.6
    ports:
      - "8080:8080"
      - "50051:50051"
    restart: on-failure
    volumes:
      - weaviate_data:/var/lib/weaviate
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      ENABLE_MODULES: ""           # we use external embeddings (ADR 0008)
      DEFAULT_VECTORIZER_MODULE: "none"
      CLUSTER_HOSTNAME: "node1"

volumes:
  weaviate_data:
```

- [ ] **Step 2: Start Weaviate**

```bash
cd /Users/nashirba/epam_course/task_1
docker compose up -d weaviate
docker compose ps
```
Expected: `weaviate` is `running`. Wait ~10s for first boot.

- [ ] **Step 3: Smoke probe**

```bash
curl -fsS http://localhost:8080/v1/.well-known/ready && echo OK
```
Expected: `OK`.

- [ ] **Step 4: Stop (Weaviate stays in volume)**

```bash
docker compose stop weaviate
```

### Task 0.6: README skeleton

**Files:**
- Modify: `README.md` (replace whatever is there with a real skeleton)

- [ ] **Step 1: Write the README**

```markdown
# Personal Investment-Planning Assistant

A multi-agent RAG + MCP system that helps a Kazakhstan-resident investor track holdings, monitor markets, and reallocate when conditions change. Course capstone (EPAM GenAI Engineering, 2026).

> Informational only. **Not** licensed financial, legal, or tax advice.

## What's inside

- 3 agents (Portfolio / Market / Planner) on an in-process Pydantic message bus.
- Hybrid RAG (BM25 + dense) over a real KZ-domain corpus, indexed in Weaviate.
- MCP: consumes a web-search server **and** ships a custom `kz-data` MCP with 4 tools (NBK rate, FX, KASE quote, deposit rates).
- LLM and embedding providers are swappable via env vars (Anthropic / Gemini / Groq / Ollama / OpenAI / local).
- Streamlit chat UI with a portfolio sidebar.

See `docs/superpowers/specs/2026-05-02-personal-investment-assistant-design.md` for the full design and `docs/decisions/` for ADRs.

## Runtime model

Local-only hybrid runtime: Weaviate runs in Docker; the Streamlit app runs as a local `uv` Python process. No cloud deployment or app container is required for the capstone.

## Quickstart

```bash
git clone <repo> && cd task_1
cp .env.example .env             # edit if you want to use a paid provider
uv sync --all-extras
docker compose up -d weaviate
uv run python -m scripts.ingest  # populates Weaviate from data/
uv run streamlit run src/pia/ui/app.py
```

The default config runs at $0: free Gemini LLM + local `BAAI/bge-m3` embeddings + self-hosted Weaviate.

## Tests

```bash
uv run pytest                    # unit + integration
uv run pytest -m smoke           # end-to-end
uv run pytest -m adversarial     # safety/jailbreak suite (post-draft)
```

## Layout

See `docs/superpowers/plans/2026-05-02-pia-pre-draft.md` for the implementation plan and project layout.

## License

MIT for code authored here. Third-party data is cited per source under `data/public/*/PROVENANCE.md`.
```

### Task 0.7: Smoke test

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/unit/test_smoke.py`

- [ ] **Step 1: Write `conftest.py`**

```python
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path: Path):
    """Default tests run with a clean env and an ephemeral DATA_DIR."""
    for k in [
        "LLM_MODEL", "EMBEDDING_PROVIDER", "WEAVIATE_HOST",
        "TAVILY_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY",
    ]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    (tmp_path / "data").mkdir()
    yield
```

- [ ] **Step 2: Write smoke test**

```python
# tests/unit/test_smoke.py
import importlib


def test_pia_imports():
    pia = importlib.import_module("pia")
    assert pia is not None


def test_settings_constructs():
    from pia.config import get_settings
    s = get_settings()
    assert s.llm_model
    assert s.weaviate_http_port == 8080
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest -v
```
Expected: 4 passed (the 2 config tests + 2 smoke).

### Task 0.8: Commit Phase 0

- [ ] **Step 1: Stage and commit**

```bash
cd /Users/nashirba/epam_course/task_1
git add pyproject.toml docker-compose.yml .env.example README.md \
        src/pia tests/ scripts/ data/.gitkeep || true
# add empty placeholders for empty data dirs:
for d in data/personal/notes data/public/news data/public/bank_rates data/public/real_estate/almaty data/public/kase data/public/nbk; do
  touch "$d/.gitkeep"
done
git add data/
git commit -m "$(cat <<'EOF'
Phase 0: scaffold (deps, settings, Weaviate compose, smoke tests)

- pyproject.toml with uv-managed deps, ruff config, pytest markers.
- pydantic-settings driven config module with env-var defaults
  matching ADRs 0006/0007/0008.
- docker-compose Weaviate single-node with ENABLE_MODULES="" so
  embeddings stay under our control.
- README quickstart and smoke tests proving the package imports.
EOF
)"
```

- [ ] **Step 2: Verify**

```bash
git log --oneline -1
uv run pytest -v
uv run ruff check
```

**Phase 0 done when:** `pytest` is green, `ruff` is clean, `docker compose up -d weaviate` works, README explains how to start.

---

## Phase 1 — Day 2 (Sun 2026-05-03): Real, multilingual data corpus

**Goal of phase:** A real, substantive corpus committed to `data/`: ~30 news items, 5+ bank rate sheets, ~30 Krisha listings, KASE top-20 snapshot, NBK rate/FX/gold history, synthetic-but-plausible portfolio + plan + 5 personal notes. Each source directory has a `PROVENANCE.md` documenting origin, license, and snapshot date. No ingestion yet (Phase 2).

> **Important:** all data files are real (or realistic) and are committed to the repo. The "personal" data is **synthetic** but plausible — never include real PII.

### Task 1.1: Personal corpus — synthetic portfolio

**Files:**
- Create: `data/personal/holdings.json`

- [ ] **Step 1: Write `holdings.json`**

```json
{
  "as_of": "2026-05-02",
  "currency_base": "KZT",
  "positions": [
    {"asset_class": "deposit", "instrument": "Halyk KZT term deposit 12m", "amount": 8000000, "currency": "KZT", "rate_apr": 0.165, "opened": "2025-11-15", "matures": "2026-11-15"},
    {"asset_class": "deposit", "instrument": "Kaspi USD savings", "amount": 12000, "currency": "USD", "rate_apr": 0.045, "opened": "2025-08-01", "matures": null},
    {"asset_class": "deposit", "instrument": "BCC KZT savings", "amount": 3500000, "currency": "KZT", "rate_apr": 0.155, "opened": "2026-02-10", "matures": null},
    {"asset_class": "real_estate", "instrument": "1BR apartment, Bostandyk district, 45 m²", "amount": 38000000, "currency": "KZT", "purchased": "2023-06-20", "ownership": "primary residence"},
    {"asset_class": "kase_equity", "instrument": "KCEL", "shares": 800, "avg_cost": 1820, "currency": "KZT", "opened": "2024-09-12"},
    {"asset_class": "kase_equity", "instrument": "HSBK", "shares": 2500, "avg_cost": 195, "currency": "KZT", "opened": "2025-01-30"},
    {"asset_class": "us_etf", "instrument": "VOO", "shares": 18, "avg_cost": 478, "currency": "USD", "opened": "2024-03-04"},
    {"asset_class": "us_etf", "instrument": "QQQ", "shares": 9, "avg_cost": 470, "currency": "USD", "opened": "2025-02-21"},
    {"asset_class": "cash", "instrument": "Current account KZT", "amount": 1200000, "currency": "KZT"}
  ],
  "goals": [
    {"id": "emergency", "label": "Emergency fund (6 months)", "target_kzt": 6000000, "target_date": "2026-09-30"},
    {"id": "mortgage_payoff", "label": "Pay off mortgage", "target_kzt": 0, "target_date": "2030-12-31"},
    {"id": "retirement", "label": "Retirement nest egg", "target_kzt": 200000000, "target_date": "2045-12-31"}
  ],
  "risk_tolerance": "moderate",
  "constraints": ["KZT-resident tax", "no leverage", "no crypto in v1"]
}
```

### Task 1.2: Personal corpus — plan and notes

**Files:**
- Create: `data/personal/plan.md`
- Create: `data/personal/notes/halyk_thesis.md`
- Create: `data/personal/notes/kcell_thesis.md`
- Create: `data/personal/notes/almaty_real_estate_view.md`
- Create: `data/personal/notes/usd_kzt_hedging.md`
- Create: `data/personal/notes/voo_qqq_allocation.md`

- [ ] **Step 1: Write `plan.md`**

```markdown
---
type: plan
last_updated: 2026-05-02
---

# Personal investment plan

## Goals
1. Build a 6-month emergency fund in liquid KZT/USD by 2026-09-30.
2. Maintain ≥ 30% hard-currency exposure (USD + USD-denominated assets).
3. Treat KASE equities as ≤ 15% of total NAV.
4. Real estate (primary residence) is not a tradable position; track but do not rebalance.
5. Avoid leverage. Avoid crypto in v1 of the assistant.

## Target allocation (excluding primary residence)
- Deposits & cash (KZT): 35%
- Deposits & cash (USD): 25%
- KASE equities: 10%
- US ETFs: 30%

## Rebalancing rules
- Drift threshold: ±5 percentage points triggers a rebalancing review.
- Review cadence: quarterly, plus on any KASE single-name move > 15% in a week.
- Tax-aware: prefer realizing losses before year-end if available.

## Risk tolerance
Moderate. Comfortable with KASE equity volatility. Uncomfortable with > 50% KZT exposure given local inflation and FX risk.
```

- [ ] **Step 2: Write the 5 notes**

Each note has YAML front-matter and 200-400 words of plausible thesis text. Use the templates below; fill the bodies with the user's actual stance — concrete numbers, links to public reports, dates.

`data/personal/notes/halyk_thesis.md`:
```markdown
---
type: thesis
ticker: HSBK
asset_class: kase_equity
last_updated: 2026-04-18
tags: [bank, kazakhstan, dividend]
---

# Halyk Bank (HSBK) — thesis

Held since 2025-01-30 at avg cost 195 KZT. Thesis: dominant KZ retail-bank franchise with strong CASA, cyclical tailwind from elevated NBK base rate, history of paying out 50%+ of net income as dividends. Dividend yield at cost ~ 12% on the last announcement.

## Bull case
- ROE consistently above 25% across the cycle.
- Most regulated and most profitable bank in the KZ market.
- Strong capital buffer; a base-rate cut would compress NIM but unlikely below 5%.

## Bear case
- Concentration risk — single-country, single-currency dominant.
- Political risk: state-related ownership shifts have rattled the stock historically.
- A sharp KZT devaluation pressures real returns even as nominal earnings rise.

## Triggers to revisit
- NBK base rate cut > 200 bps in a single move.
- Dividend payout ratio falls below 30% in two consecutive years.
- Material change in single-largest shareholder.

## Position-sizing rule
Cap at 5% of NAV. Trim to 4% if dividend yield at cost falls below 8%.
```

`data/personal/notes/kcell_thesis.md`:
```markdown
---
type: thesis
ticker: KCEL
asset_class: kase_equity
last_updated: 2026-03-11
tags: [telecom, kazakhstan]
---

# Kcell (KCEL) — thesis

Held since 2024-09-12 at avg cost 1820 KZT. Mature telecom with steady cash flows; thesis is dividend yield + modest growth from data-traffic monetization, capped by competitive intensity.

## Bull case
- Stable subscriber base; mobile-data ARPU still rising.
- Tower-share / 5G capex cycle largely behind; cash flow conversion improving.
- Dividend payout target announced at 100% of free cash flow.

## Bear case
- Beeline KZ aggressive on price; risk of ARPU compression.
- Regulatory tariff caps a recurring overhang.
- KZT-only revenues, no FX cushion.

## Triggers to revisit
- Two consecutive quarters of subscriber decline.
- Dividend cut.
- Major regulatory action on tariffs.

## Position-sizing rule
Cap at 3% of NAV.
```

`data/personal/notes/almaty_real_estate_view.md`:
```markdown
---
type: market_view
asset_class: real_estate
city: Almaty
last_updated: 2026-04-22
tags: [real_estate, almaty, krisha]
---

# Almaty real estate — current view

Watching: 1-2BR apartments in Bostandyk and Medeu, secondary market.

## Observations
- Krisha listings show median price/m² in Bostandyk around 850k KZT (April 2026 sample of 30 listings).
- Primary developer pricing has been inching up after a flat 2025; demand is dollar-driven (savings flight from KZT).
- Inventory turnover is faster on 1BR than 2BR.

## Personal stance
- I already own a primary residence here. No second home unless KZT/USD cracks materially or a clearly underpriced unit appears.
- Rental yields in Almaty are 5-7% gross on apartments — below my deposit rate. Deposits win unless there is a capital-gain thesis.

## What would change my mind
- A double-digit KZT/USD move that reprices the local-currency asset.
- A specific listing > 20% below comps with a verifiable reason.
```

`data/personal/notes/usd_kzt_hedging.md`:
```markdown
---
type: market_view
topic: fx_hedging
last_updated: 2026-04-30
tags: [fx, kzt, usd, hedging]
---

# USD/KZT hedging — current view

KZT has weakened ~25% against USD since 2022. NBK base rate is high; KZT carry remains attractive but not a hedge against currency risk.

## Stance
- Maintain ≥ 30% of NAV in hard currency (USD deposits + US ETFs in USD).
- Treat KZT deposits as carry trades, not store of value.

## Rebalancing trigger
- If hard-currency exposure drifts below 25%, top up via Kaspi USD savings.
- If above 40%, redirect new flows to KZT deposits while rates remain elevated.
```

`data/personal/notes/voo_qqq_allocation.md`:
```markdown
---
type: thesis
asset_class: us_etf
tickers: [VOO, QQQ]
last_updated: 2026-02-12
tags: [etf, us, allocation]
---

# US ETF allocation — VOO + QQQ

Core US equity exposure via VOO; tech tilt via QQQ. 2:1 in favor of VOO.

## Why
- Cheapest broad exposure (VOO 3 bps, QQQ 20 bps).
- Tax simplicity: dividends only, no underlying-holding complexity.
- Hard-currency denominated, hedges KZT risk.

## Rules
- Add monthly via DCA.
- Stop adding if total US exposure exceeds 35% of NAV.
- Never sell to fund KZT spending; sell only on goal-date or a > 25% drawdown rebalance.
```

### Task 1.3: Public corpus — bank deposit rate snapshots

**Files:**
- Create: `data/public/bank_rates/halyk-2026-05-02.json`
- Create: `data/public/bank_rates/kaspi-2026-05-02.json`
- Create: `data/public/bank_rates/bcc-2026-05-02.json`
- Create: `data/public/bank_rates/jusan-2026-05-02.json`
- Create: `data/public/bank_rates/freedom-2026-05-02.json`
- Create: `data/public/bank_rates/PROVENANCE.md`

- [ ] **Step 1: Write the JSON files**

Pattern (one example):
```json
{
  "bank": "Halyk Bank",
  "snapshot_date": "2026-05-02",
  "source_url": "https://halykbank.kz/private/deposits",
  "products": [
    {"name": "Halyk-Klassika", "currency": "KZT", "term_months": 12, "min_amount": 100000, "rate_apr": 0.165, "interest_payout": "monthly"},
    {"name": "Halyk-Klassika", "currency": "KZT", "term_months": 24, "min_amount": 100000, "rate_apr": 0.155, "interest_payout": "monthly"},
    {"name": "Halyk-Online", "currency": "USD", "term_months": 12, "min_amount": 1000, "rate_apr": 0.045, "interest_payout": "monthly"},
    {"name": "Halyk-Online", "currency": "EUR", "term_months": 12, "min_amount": 1000, "rate_apr": 0.020, "interest_payout": "monthly"}
  ]
}
```

Repeat for the other 4 banks with realistic numbers. Cover at least KZT/USD and 6/12-month terms each.

- [ ] **Step 2: Write `PROVENANCE.md`**

```markdown
# Bank deposit rates — provenance

| File | Source URL | Snapshot date | Notes |
|---|---|---|---|
| halyk-2026-05-02.json   | https://halykbank.kz/private/deposits | 2026-05-02 | Manually transcribed from public rate sheet. |
| kaspi-2026-05-02.json   | https://kaspi.kz/dep | 2026-05-02 | … |
| bcc-2026-05-02.json     | https://bcc.kz/private/deposits | 2026-05-02 | … |
| jusan-2026-05-02.json   | https://jusan.kz/deposits | 2026-05-02 | … |
| freedom-2026-05-02.json | https://bankffin.kz/deposits | 2026-05-02 | … |

Bank deposit rates are factual data and not subject to copyright. Source URLs are recorded for reproducibility.
```

### Task 1.4: Public corpus — NBK history

**Files:**
- Create: `data/public/nbk/base_rate_history.json`
- Create: `data/public/nbk/fx_history.json`
- Create: `data/public/nbk/gold_history.json`
- Create: `data/public/nbk/PROVENANCE.md`

- [ ] **Step 1: Write the three histories**

`base_rate_history.json` — at least last 24 months of NBK base rate decisions:
```json
{
  "snapshot_date": "2026-05-02",
  "source_url": "https://www.nationalbank.kz/en/baserate",
  "history": [
    {"effective_from": "2024-05-13", "rate_apr": 0.140},
    {"effective_from": "2024-08-26", "rate_apr": 0.145},
    {"effective_from": "2024-11-29", "rate_apr": 0.150},
    {"effective_from": "2025-02-28", "rate_apr": 0.155},
    {"effective_from": "2025-06-06", "rate_apr": 0.160},
    {"effective_from": "2025-10-10", "rate_apr": 0.165},
    {"effective_from": "2026-02-13", "rate_apr": 0.165},
    {"effective_from": "2026-04-18", "rate_apr": 0.155}
  ]
}
```

`fx_history.json` — daily KZT/USD, KZT/EUR, KZT/RUB for the last ~6 months sampled weekly. Source: NBK official rates.

`gold_history.json` — last 12 monthly fixings.

- [ ] **Step 2: Write `PROVENANCE.md`** with source links and snapshot dates.

### Task 1.5: Public corpus — KASE snapshot

**Files:**
- Create: `data/public/kase/quotes-2026-05-02.json`
- Create: `data/public/kase/PROVENANCE.md`

- [ ] **Step 1: Write `quotes-2026-05-02.json`**

```json
{
  "snapshot_date": "2026-05-02",
  "source_url": "https://kase.kz/en/shares/",
  "index": {"name": "KASE Index", "value": 5420.18, "change_pct_d": -0.45},
  "tickers": [
    {"ticker": "HSBK", "name": "Halyk Bank", "last": 215.40, "change_pct_d": 0.12, "volume": 1240000, "currency": "KZT"},
    {"ticker": "KCEL", "name": "Kcell", "last": 1955.00, "change_pct_d": -1.12, "volume": 84000, "currency": "KZT"},
    {"ticker": "KZTK", "name": "Kazakhtelecom", "last": 36800.00, "change_pct_d": 0.30, "volume": 5400, "currency": "KZT"},
    {"ticker": "KAZ", "name": "KAZ Minerals", "last": 23150.00, "change_pct_d": -0.85, "volume": 12300, "currency": "KZT"}
  ]
}
```

Add at least 10 tickers (top by liquidity).

- [ ] **Step 2: Write `PROVENANCE.md`**.

### Task 1.6: Public corpus — news scrape (real data)

**Files:**
- Create: `scripts/snapshot_news.py`
- Create: `data/public/news/<slug>.md` × ~30
- Create: `data/public/news/PROVENANCE.md`

> **Strategy:** simple httpx + BeautifulSoup scraper that pulls from RSS feeds (Tengrinews, Forbes.kz, Kazpravda, NBK press releases). Filter to economy/finance keywords. Save each article as Markdown with YAML front-matter.

- [ ] **Step 1: Write the scraper skeleton**

`scripts/snapshot_news.py`:
```python
"""Snapshot KZ economic/finance news to data/public/news as YAML-front-matter Markdown.

Usage: uv run python -m scripts.snapshot_news --limit 50
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

FEEDS = {
    "tengrinews_business": "https://tengrinews.kz/rss/section/3/",
    "forbes_kz_finance":   "https://forbes.kz/rss/news/finansy/",
    "kazpravda_economy":   "https://kazpravda.kz/rss/economy/",
    "nbk_press":           "https://www.nationalbank.kz/?docid=309&switch=russian&format=rss",
}

KEYWORDS = re.compile(
    r"(нбрк|базов|ставк|депозит|инфляц|тенге|KZT|kase|акц|облигац|ипотек|недвижимос|курс)",
    re.IGNORECASE,
)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "-", text.strip().lower(), flags=re.UNICODE)
    return text[:80].strip("-")


def fetch_feed(url: str) -> list[dict]:
    r = httpx.get(url, timeout=20.0, follow_redirects=True)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    items = []
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link":  (item.findtext("link") or "").strip(),
            "description": (item.findtext("description") or "").strip(),
            "pub_date": (item.findtext("pubDate") or "").strip(),
        })
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", type=Path, default=Path("data/public/news"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    saved = 0
    for source, url in FEEDS.items():
        try:
            items = fetch_feed(url)
        except httpx.HTTPError as exc:
            print(f"[skip] {source}: {exc}")
            continue
        for it in items:
            if saved >= args.limit:
                break
            if not KEYWORDS.search(it["title"] + " " + it["description"]):
                continue
            slug = slugify(it["title"])
            if not slug:
                continue
            path = args.out / f"{source}-{slug}.md"
            if path.exists():
                continue
            path.write_text(
                f"---\nsource: {source}\nurl: {it['link']}\npublished: {it['pub_date']}\n"
                f"snapshot_date: {dt.date.today().isoformat()}\nlanguage: ru\n---\n\n"
                f"# {it['title']}\n\n{it['description']}\n",
                encoding="utf-8",
            )
            saved += 1
    print(f"saved={saved}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the scraper**

```bash
cd /Users/nashirba/epam_course/task_1
uv run python -m scripts.snapshot_news --limit 50
ls data/public/news | wc -l
```
Expected: at least 25-50 articles. If a feed is blocked, switch to a different one or transcribe a handful manually.

- [ ] **Step 3: Hand-curate**

Open the saved files. Delete obvious junk (off-topic, paywall stubs). Keep ≥ 30 substantive articles spanning rates, FX, real estate, KASE, banking.

- [ ] **Step 4: Write `PROVENANCE.md`**

```markdown
# News snapshot — provenance

Articles in this directory were scraped from public RSS feeds on 2026-05-02 using `scripts/snapshot_news.py`.

| Source slug | Feed URL | Notes |
|---|---|---|
| tengrinews_business | https://tengrinews.kz/rss/section/3/ | Russian-language business section |
| forbes_kz_finance | https://forbes.kz/rss/news/finansy/ | Russian-language finance |
| kazpravda_economy | https://kazpravda.kz/rss/economy/ | Russian/Kazakh-language economy |
| nbk_press | https://www.nationalbank.kz/?docid=309&switch=russian&format=rss | NBK press releases |

Use is non-commercial and academic, with full attribution preserved in each file's front-matter. Articles may be removed on request.
```

### Task 1.7: Public corpus — Krisha real-estate listings

**Files:**
- Create: `scripts/snapshot_krisha.py`
- Create: `data/public/real_estate/almaty/listings-2026-05-02.json`
- Create: `data/public/real_estate/almaty/PROVENANCE.md`

> **Strategy:** Krisha actively rate-limits and changes HTML; do not chase a robust scraper for v1. Hand-build a snapshot of ~30 plausible listings derived from a single browsing session, recording URL+price+date for each.

- [ ] **Step 1: Hand-build `listings-2026-05-02.json`**

```json
{
  "snapshot_date": "2026-05-02",
  "city": "Almaty",
  "source_url": "https://krisha.kz/prodazha/kvartiry/almaty/",
  "listings": [
    {"id": "1", "district": "Bostandyk", "rooms": 1, "area_m2": 42, "price_kzt": 36000000, "year_built": 2018, "url": "https://krisha.kz/a/show/<id-1>"},
    {"id": "2", "district": "Bostandyk", "rooms": 2, "area_m2": 65, "price_kzt": 53500000, "year_built": 2014, "url": "..."},
    {"id": "3", "district": "Medeu",     "rooms": 1, "area_m2": 39, "price_kzt": 31200000, "year_built": 2016, "url": "..."}
  ]
}
```

Fill out at least 30 listings spanning Bostandyk, Medeu, Almaly, Auezov, Nauryzbay districts; mix of 1-3BR, secondary market.

- [ ] **Step 2: Write `PROVENANCE.md`** with the source URL, snapshot method (manual transcription), and a note that listings are factual ads with no copyrighted creative content beyond title/description.

### Task 1.8: Sanity check the corpus

- [ ] **Step 1: Counts**

```bash
cd /Users/nashirba/epam_course/task_1
echo "personal notes: $(find data/personal/notes -name '*.md' | wc -l)"
echo "news: $(find data/public/news -name '*.md' | wc -l)"
echo "bank rates: $(find data/public/bank_rates -name '*.json' | wc -l)"
echo "krisha listings: $(jq '.listings | length' data/public/real_estate/almaty/*.json)"
echo "kase: $(jq '.tickers | length' data/public/kase/*.json)"
```
Expected: notes ≥ 5, news ≥ 30, bank_rates ≥ 5, krisha ≥ 30, kase ≥ 10.

- [ ] **Step 2: Spot-check a random sample**

```bash
ls data/public/news | shuf | head -3 | xargs -I{} cat data/public/news/{}
```
Expected: real, on-topic Russian-language KZ economic/finance news.

### Task 1.9: Commit Phase 1

- [ ] **Step 1: Commit**

```bash
git add data/ scripts/snapshot_news.py
git commit -m "Phase 1: corpus (synthetic portfolio + plan + 5 notes + 30+ news + bank rates + KASE + NBK history + Krisha listings)"
```

**Phase 1 done when:** counts above pass, every public source dir has a `PROVENANCE.md`, no real PII in `data/personal/`.

---

## Phase 2 — Day 3 (Mon 2026-05-04): RAG layer

**Goal of phase:** A standalone `pia.rag` module that loads documents, chunks them, embeds them, indexes into Weaviate, and exposes `retrieve(query, filters, k)` returning ranked chunks + citations. Unit + integration tests pass against a live Weaviate.

### Task 2.1: Embedding provider abstraction (TDD)

**Files:**
- Create: `src/pia/embeddings/base.py`
- Create: `src/pia/embeddings/local.py`
- Create: `src/pia/embeddings/litellm.py`
- Create: `src/pia/embeddings/__init__.py` (factory)
- Test: `tests/unit/test_embeddings.py`

- [ ] **Step 1: Write test for the local provider**

`tests/unit/test_embeddings.py`:
```python
import pytest

from pia.embeddings import get_embedding_provider


@pytest.mark.integration
def test_local_provider_embeds(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    provider = get_embedding_provider()
    vecs = provider.embed_batch(["hello world", "Halyk Bank deposit rate"])
    assert len(vecs) == 2
    assert len(vecs[0]) == provider.dim
    assert provider.dim > 0
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/unit/test_embeddings.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement `base.py`**

```python
from typing import Protocol


class EmbeddingProvider(Protocol):
    @property
    def dim(self) -> int: ...
    @property
    def name(self) -> str: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...
```

- [ ] **Step 4: Implement `local.py`**

```python
from __future__ import annotations

from functools import cached_property

from sentence_transformers import SentenceTransformer


class LocalEmbeddings:
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self._model_name = model_name

    @cached_property
    def _model(self) -> SentenceTransformer:
        return SentenceTransformer(self._model_name)

    @property
    def name(self) -> str:
        return f"local:{self._model_name}"

    @property
    def dim(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embs = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [list(map(float, v)) for v in embs]

    def embed_one(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]
```

- [ ] **Step 5: Implement `litellm.py`**

```python
from __future__ import annotations

import litellm


_MODEL_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "gemini/text-embedding-004": 768,
}


class LiteLLMEmbeddings:
    def __init__(self, model: str):
        self._model = model

    @property
    def name(self) -> str:
        return f"litellm:{self._model}"

    @property
    def dim(self) -> int:
        return _MODEL_DIMS.get(self._model, 1536)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = litellm.embedding(model=self._model, input=texts)
        return [d["embedding"] for d in resp["data"]]

    def embed_one(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]
```

- [ ] **Step 6: Implement factory `__init__.py`**

```python
from pia.config import get_settings
from pia.embeddings.base import EmbeddingProvider
from pia.embeddings.litellm import LiteLLMEmbeddings
from pia.embeddings.local import LocalEmbeddings


def get_embedding_provider() -> EmbeddingProvider:
    s = get_settings()
    if s.embedding_provider == "local":
        return LocalEmbeddings(model_name=s.embedding_model)
    if s.embedding_provider == "openai":
        return LiteLLMEmbeddings(model="text-embedding-3-small")
    if s.embedding_provider == "gemini":
        return LiteLLMEmbeddings(model="gemini/text-embedding-004")
    raise ValueError(f"unknown EMBEDDING_PROVIDER: {s.embedding_provider}")
```

- [ ] **Step 7: Run test — expect pass**

```bash
uv run pytest tests/unit/test_embeddings.py -v -m integration
```
Expected: PASS (model downloads on first run; ~30s).

### Task 2.2: Markdown-aware chunker (TDD)

**Files:**
- Create: `src/pia/rag/chunker.py`
- Test: `tests/unit/test_chunker.py`

- [ ] **Step 1: Write test**

```python
from pia.rag.chunker import Chunk, chunk_markdown


def test_chunk_keeps_headings_with_body():
    text = "# Title\n\nIntro.\n\n## Section A\n\nBody A.\n\n## Section B\n\nBody B." * 1
    chunks = chunk_markdown(text, max_tokens=20, overlap_tokens=4)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert any("Section A" in c.text for c in chunks)
    assert any("Section B" in c.text for c in chunks)


def test_chunk_overlap_preserved():
    text = "para1.\n\npara2.\n\npara3.\n\npara4.\n\npara5.\n\npara6."
    chunks = chunk_markdown(text, max_tokens=10, overlap_tokens=3)
    # Adjacent chunks share at least one token
    for a, b in zip(chunks, chunks[1:], strict=False):
        assert set(a.text.split()) & set(b.text.split())
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/unit/test_chunker.py -v
```

- [ ] **Step 3: Implement chunker**

```python
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    headings: tuple[str, ...]


_TOKEN_RE = re.compile(r"\S+")


def _approx_tokens(s: str) -> int:
    return len(_TOKEN_RE.findall(s))


def chunk_markdown(text: str, *, max_tokens: int = 600, overlap_tokens: int = 80) -> list[Chunk]:
    """Heading-aware chunker. Splits on blank-line paragraphs, accumulates up to
    `max_tokens`, then carries `overlap_tokens` tail into the next chunk.
    Tracks the heading stack so each chunk knows its breadcrumb."""
    paragraphs: list[tuple[str, tuple[str, ...]]] = []
    stack: list[tuple[int, str]] = []  # (level, text)
    for para in re.split(r"\n\s*\n", text.strip()):
        m = re.match(r"^(#{1,6})\s+(.*)$", para.strip())
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            stack = [(lvl, t) for lvl, t in stack if lvl < level]
            stack.append((level, heading))
            continue
        paragraphs.append((para.strip(), tuple(t for _, t in stack)))

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_tokens = 0
    last_headings: tuple[str, ...] = ()
    for para, headings in paragraphs:
        n = _approx_tokens(para)
        if buf and buf_tokens + n > max_tokens:
            chunks.append(Chunk("\n\n".join(buf), last_headings))
            tail = " ".join(" ".join(buf).split()[-overlap_tokens:])
            buf = [tail] if tail else []
            buf_tokens = _approx_tokens(tail) if tail else 0
        buf.append(para)
        buf_tokens += n
        last_headings = headings
    if buf:
        chunks.append(Chunk("\n\n".join(buf), last_headings))
    return chunks
```

- [ ] **Step 4: Run — expect pass**

### Task 2.3: Document loaders (TDD)

**Files:**
- Create: `src/pia/rag/loaders.py`
- Test: `tests/unit/test_loaders.py`

- [ ] **Step 1: Test loads each source type**

```python
from pathlib import Path

from pia.rag.loaders import load_documents


def test_load_documents_finds_all_sources(tmp_path: Path):
    (tmp_path / "personal/notes").mkdir(parents=True)
    (tmp_path / "personal/notes/x.md").write_text("---\ntype: thesis\n---\n\n# X\n\nbody")
    (tmp_path / "personal/holdings.json").write_text('{"as_of":"2026-05-02","positions":[]}')
    (tmp_path / "public/news").mkdir(parents=True)
    (tmp_path / "public/news/n.md").write_text("---\nsource: t\nurl: u\npublished: 2026-05-01\n---\n\n# N\n\nbody")
    (tmp_path / "public/bank_rates").mkdir(parents=True)
    (tmp_path / "public/bank_rates/halyk.json").write_text('{"bank":"H","snapshot_date":"2026-05-02","products":[]}')

    docs = list(load_documents(tmp_path))
    sources = {d.source for d in docs}
    assert {"user_note", "user_holdings", "news", "bank_rates"} <= sources
```

- [ ] **Step 2: Implement loader**

```python
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Document:
    source: str           # 'user_note', 'user_holdings', 'user_plan', 'news', 'bank_rates', 'kase', 'nbk', 'real_estate'
    source_url: str       # path or URL
    text: str             # body to chunk and embed
    metadata: dict        # extra props (language, ticker, district, etc.)
    published_at: str | None = None
    language: str | None = None


_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _read_md(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    m = _FRONT_MATTER.match(raw)
    if not m:
        return {}, raw
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, m.group(2)


def _flatten_json(obj, prefix: str = "") -> str:
    """Render JSON as a deterministic text blob — good enough for hybrid search."""
    if isinstance(obj, dict):
        return "\n".join(f"{prefix}{k}: {_flatten_json(v, prefix)}" for k, v in obj.items())
    if isinstance(obj, list):
        return "\n".join(_flatten_json(x, prefix + "- ") for x in obj)
    return str(obj)


def load_documents(data_dir: Path) -> Iterator[Document]:
    # Personal notes
    for p in (data_dir / "personal/notes").glob("*.md"):
        meta, body = _read_md(p)
        yield Document(
            source="user_note",
            source_url=str(p),
            text=body,
            metadata=meta,
            published_at=meta.get("last_updated"),
            language=meta.get("language", "en"),
        )
    # Personal plan
    plan = data_dir / "personal/plan.md"
    if plan.exists():
        meta, body = _read_md(plan)
        yield Document("user_plan", str(plan), body, meta, meta.get("last_updated"), "en")
    # Personal holdings
    holdings = data_dir / "personal/holdings.json"
    if holdings.exists():
        obj = json.loads(holdings.read_text())
        yield Document("user_holdings", str(holdings), _flatten_json(obj), obj, obj.get("as_of"), "en")

    # News
    for p in (data_dir / "public/news").glob("*.md"):
        meta, body = _read_md(p)
        yield Document("news", meta.get("url", str(p)), body, meta, meta.get("published"), meta.get("language", "ru"))

    # Bank rates
    for p in (data_dir / "public/bank_rates").glob("*.json"):
        obj = json.loads(p.read_text())
        yield Document("bank_rates", obj.get("source_url", str(p)), _flatten_json(obj), obj, obj.get("snapshot_date"), "en")

    # KASE / NBK / Krisha
    for sub, src in [("public/kase", "kase"), ("public/nbk", "nbk"), ("public/real_estate/almaty", "real_estate")]:
        for p in (data_dir / sub).glob("*.json"):
            obj = json.loads(p.read_text())
            yield Document(src, obj.get("source_url", str(p)), _flatten_json(obj), obj, obj.get("snapshot_date"), "en")
```

- [ ] **Step 3: Run — expect pass**

### Task 2.4: Weaviate store (TDD with live Weaviate)

**Files:**
- Create: `src/pia/rag/store.py`
- Test: `tests/integration/test_store.py`

- [ ] **Step 1: Start Weaviate**

```bash
docker compose up -d weaviate
```

- [ ] **Step 2: Write integration test**

```python
import pytest

from pia.embeddings.local import LocalEmbeddings
from pia.rag.chunker import Chunk
from pia.rag.loaders import Document
from pia.rag.store import WeaviateStore


@pytest.mark.integration
def test_store_index_and_retrieve():
    embeddings = LocalEmbeddings()
    store = WeaviateStore(embeddings=embeddings, collection="TestKB", reset=True)
    docs = [
        Document(source="news", source_url="u1", text="NBK raised the base rate to 16.5%", metadata={}, published_at="2026-04-18", language="en"),
        Document(source="news", source_url="u2", text="Halyk Bank dividend announcement", metadata={}, published_at="2026-04-20", language="en"),
        Document(source="user_note", source_url="u3", text="My target allocation is 30% USD ETFs", metadata={}, published_at="2026-05-01", language="en"),
    ]
    chunks = [(d, Chunk(d.text, headings=())) for d in docs]
    store.upsert(chunks)
    hits = store.hybrid_search("base rate", k=3)
    assert hits[0].source == "news"
    assert "rate" in hits[0].text.lower()
    store.close()
```

- [ ] **Step 3: Implement `WeaviateStore`**

```python
from __future__ import annotations

import uuid
from dataclasses import dataclass

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, HybridFusion, MetadataQuery

from pia.config import get_settings
from pia.embeddings.base import EmbeddingProvider
from pia.rag.chunker import Chunk
from pia.rag.loaders import Document


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    source_url: str
    published_at: str | None
    language: str | None
    score: float
    headings: tuple[str, ...]


class WeaviateStore:
    def __init__(self, *, embeddings: EmbeddingProvider, collection: str = "KB", reset: bool = False):
        s = get_settings()
        self._client = weaviate.connect_to_local(host=s.weaviate_host, port=s.weaviate_http_port, grpc_port=s.weaviate_grpc_port)
        self._embeddings = embeddings
        self._collection_name = collection
        if reset and self._client.collections.exists(collection):
            self._client.collections.delete(collection)
        if not self._client.collections.exists(collection):
            self._client.collections.create(
                name=collection,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="content",       data_type=DataType.TEXT),
                    Property(name="source",        data_type=DataType.TEXT),
                    Property(name="source_url",    data_type=DataType.TEXT),
                    Property(name="published_at",  data_type=DataType.TEXT),
                    Property(name="language",      data_type=DataType.TEXT),
                    Property(name="headings",      data_type=DataType.TEXT_ARRAY),
                    Property(name="embedding_model", data_type=DataType.TEXT),
                ],
            )
        self._coll = self._client.collections.get(collection)

    def upsert(self, items: list[tuple[Document, Chunk]]) -> None:
        texts = [c.text for _, c in items]
        vectors = self._embeddings.embed_batch(texts)
        with self._coll.batch.dynamic() as batch:
            for (doc, chunk), vec in zip(items, vectors, strict=True):
                batch.add_object(
                    uuid=uuid.uuid5(uuid.NAMESPACE_URL, f"{doc.source}|{doc.source_url}|{chunk.text[:64]}").hex,
                    properties={
                        "content": chunk.text,
                        "source": doc.source,
                        "source_url": doc.source_url,
                        "published_at": doc.published_at or "",
                        "language": doc.language or "",
                        "headings": list(chunk.headings),
                        "embedding_model": self._embeddings.name,
                    },
                    vector=vec,
                )

    def hybrid_search(
        self, query: str, *, k: int = 5, alpha: float = 0.5, filter_source: str | None = None
    ) -> list[RetrievedChunk]:
        flt = Filter.by_property("source").equal(filter_source) if filter_source else None
        qvec = self._embeddings.embed_one(query)
        res = self._coll.query.hybrid(
            query=query,
            vector=qvec,
            alpha=alpha,
            limit=k,
            filters=flt,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            return_metadata=MetadataQuery(score=True),
        )
        out = []
        for o in res.objects:
            p = o.properties
            out.append(
                RetrievedChunk(
                    text=p["content"],
                    source=p["source"],
                    source_url=p["source_url"],
                    published_at=p.get("published_at") or None,
                    language=p.get("language") or None,
                    score=float(o.metadata.score or 0.0),
                    headings=tuple(p.get("headings") or ()),
                )
            )
        return out

    def close(self) -> None:
        self._client.close()
```

- [ ] **Step 4: Run integration**

```bash
uv run pytest tests/integration/test_store.py -v -m integration
```
Expected: pass.

### Task 2.5: Retrieve facade

**Files:**
- Create: `src/pia/rag/retrieve.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

from pia.embeddings import get_embedding_provider
from pia.rag.store import RetrievedChunk, WeaviateStore


def retrieve(query: str, *, k: int = 5, source: str | None = None) -> list[RetrievedChunk]:
    store = WeaviateStore(embeddings=get_embedding_provider(), collection="KB")
    try:
        return store.hybrid_search(query, k=k, filter_source=source)
    finally:
        store.close()
```

### Task 2.6: Ingest CLI

**Files:**
- Create: `scripts/ingest.py`

- [ ] **Step 1: Implement**

```python
"""Ingest data/ into Weaviate.

Usage: uv run python -m scripts.ingest [--reset]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from rich import print

from pia.config import get_settings
from pia.embeddings import get_embedding_provider
from pia.rag.chunker import chunk_markdown
from pia.rag.loaders import load_documents
from pia.rag.store import WeaviateStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    s = get_settings()
    print(f"Embedding provider: [bold]{s.embedding_provider}[/]  model: {s.embedding_model}")
    embeddings = get_embedding_provider()
    store = WeaviateStore(embeddings=embeddings, collection="KB", reset=args.reset)

    items = []
    for doc in load_documents(Path(s.data_dir)):
        for chunk in chunk_markdown(doc.text):
            items.append((doc, chunk))
    print(f"Ingesting {len(items)} chunks…")
    store.upsert(items)
    store.close()
    print("[green]Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run ingest**

```bash
docker compose up -d weaviate
uv run python -m scripts.ingest --reset
```
Expected: prints chunk count and `Done.` Weaviate collection `KB` populated.

- [ ] **Step 3: Spot-check retrieval**

```bash
uv run python -c "from pia.rag.retrieve import retrieve; \
  r = retrieve('какая текущая базовая ставка НБК?', k=3); \
  print('\n---\n'.join(f'[{c.source}] {c.text[:160]}' for c in r))"
```
Expected: top hit is from `news` or `nbk` with rate-related content.

### Task 2.7: Commit Phase 2

```bash
git add src/pia/embeddings src/pia/rag scripts/ingest.py tests/unit/test_chunker.py tests/unit/test_loaders.py tests/unit/test_embeddings.py tests/integration/test_store.py
git commit -m "Phase 2: hybrid RAG (Weaviate + multilingual local embeddings + chunker + loaders + ingest CLI)"
```

**Phase 2 done when:** `uv run python -m scripts.ingest --reset` ingests >100 chunks and a sample retrieve returns sensible KZ-domain hits.

---

## Phase 3 — Day 4 (Tue 2026-05-05): MCP — consume + custom server

**Goal of phase:** A standalone `kz-data` MCP server with 4 tools, all backed by snapshot files and reachable from a test client. A consumed web-search MCP (Tavily; fall back to Brave) is wired and callable.

### Task 3.1: MCP tool implementations (pure-function, TDD)

**Files:**
- Create: `src/pia/mcp/tools/nbk.py`, `fx.py`, `kase.py`, `deposits.py`
- Test: `tests/unit/test_mcp_tools.py`

- [ ] **Step 1: Tests for each tool**

```python
from datetime import date
from pathlib import Path

from pia.mcp.tools.deposits import get_deposit_rates
from pia.mcp.tools.fx import get_fx_rate
from pia.mcp.tools.kase import get_kase_quote
from pia.mcp.tools.nbk import get_nbk_rate


def test_nbk_rate_latest(tmp_path):
    base = Path("data")
    out = get_nbk_rate(date_str=None, data_dir=base)
    assert "rate_apr" in out
    assert out["effective_from"] <= date.today().isoformat()


def test_fx_rate_pair(tmp_path):
    out = get_fx_rate("KZT/USD", data_dir=Path("data"))
    assert out["pair"] == "KZT/USD"
    assert out["rate"] > 0


def test_kase_quote_known_ticker():
    out = get_kase_quote("HSBK", data_dir=Path("data"))
    assert out["ticker"] == "HSBK"
    assert out["last"] > 0


def test_deposit_rates_kzt_12m():
    out = get_deposit_rates("KZT", 12, data_dir=Path("data"))
    assert isinstance(out, list)
    assert all(p["currency"] == "KZT" for p in out)
```

- [ ] **Step 2: Implement `nbk.py`**

```python
from __future__ import annotations

import json
from pathlib import Path


def get_nbk_rate(*, date_str: str | None = None, data_dir: Path) -> dict:
    """Return NBK base rate at `date_str` (or latest if None)."""
    history = json.loads((data_dir / "public/nbk/base_rate_history.json").read_text())["history"]
    history.sort(key=lambda r: r["effective_from"])
    pick = history[-1]
    if date_str:
        for entry in history:
            if entry["effective_from"] <= date_str:
                pick = entry
            else:
                break
    return {**pick, "as_of": date_str or pick["effective_from"], "source": "NBK base rate history"}
```

- [ ] **Step 3: Implement `fx.py`, `kase.py`, `deposits.py`** following the same pattern (read snapshot JSON; return a dict with provenance fields; raise `ValueError` on unknown inputs).

- [ ] **Step 4: Run tests** — expect pass.

### Task 3.2: FastMCP server

**Files:**
- Create: `src/pia/mcp/server.py`

- [ ] **Step 1: Implement**

```python
"""kz-data MCP server.

Run: uv run python -m pia.mcp.server
"""
from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from pia.config import get_settings
from pia.mcp.tools.deposits import get_deposit_rates as _deposits
from pia.mcp.tools.fx import get_fx_rate as _fx
from pia.mcp.tools.kase import get_kase_quote as _kase
from pia.mcp.tools.nbk import get_nbk_rate as _nbk


_DATA = Path(get_settings().data_dir)
mcp = FastMCP("kz-data")


@mcp.tool()
def get_nbk_rate(date_str: str | None = None) -> dict:
    """NBK base rate at a date (ISO YYYY-MM-DD) or the latest entry. Returns rate_apr, effective_from, as_of."""
    return _nbk(date_str=date_str, data_dir=_DATA)


@mcp.tool()
def get_fx_rate(pair: str, date_str: str | None = None) -> dict:
    """FX spot or historical for pairs like 'KZT/USD', 'KZT/EUR', 'KZT/RUB'."""
    return _fx(pair, date_str=date_str, data_dir=_DATA)


@mcp.tool()
def get_kase_quote(ticker: str) -> dict:
    """Latest KASE snapshot for a ticker (HSBK, KCEL, …)."""
    return _kase(ticker, data_dir=_DATA)


@mcp.tool()
def get_deposit_rates(currency: str, term_months: int) -> list[dict]:
    """Deposit rate sheet across banks for a currency and term."""
    return _deposits(currency, term_months, data_dir=_DATA)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Smoke**

```bash
uv run python -m pia.mcp.server &
sleep 2
# In another terminal or after starting separately:
uv run python - <<'EOF'
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
import asyncio

async def main():
    async with stdio_client(StdioServerParameters(command="uv", args=["run", "python", "-m", "pia.mcp.server"])) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            print([t.name for t in tools.tools])

asyncio.run(main())
EOF
```
Expected: prints `['get_nbk_rate', 'get_fx_rate', 'get_kase_quote', 'get_deposit_rates']`.

### Task 3.3: MCP client wrappers

**Files:**
- Create: `src/pia/mcp/client.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@asynccontextmanager
async def _stdio(params: StdioServerParameters):
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            yield session


async def kz_data_call(tool_name: str, **kwargs: Any) -> Any:
    params = StdioServerParameters(command="uv", args=["run", "python", "-m", "pia.mcp.server"])
    async with _stdio(params) as session:
        result = await session.call_tool(tool_name, arguments=kwargs)
        return result.content[0].text if result.content else None


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Tavily MCP. Falls back to a no-op if TAVILY_API_KEY is missing."""
    if not os.getenv("TAVILY_API_KEY"):
        return []
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@tavily/mcp"],
        env={"TAVILY_API_KEY": os.environ["TAVILY_API_KEY"]},
    )
    async with _stdio(params) as session:
        result = await session.call_tool("tavily_search", arguments={"query": query, "max_results": max_results})
        return [{"text": result.content[0].text}] if result.content else []


def kz_data_call_sync(tool_name: str, **kwargs: Any) -> Any:
    return asyncio.run(kz_data_call(tool_name, **kwargs))


def web_search_sync(query: str, max_results: int = 5) -> list[dict]:
    return asyncio.run(web_search(query, max_results=max_results))
```

- [ ] **Step 2: Integration test**

`tests/integration/test_mcp.py`:
```python
import pytest

from pia.mcp.client import kz_data_call_sync


@pytest.mark.integration
def test_kz_data_nbk_via_mcp():
    out = kz_data_call_sync("get_nbk_rate")
    assert out is not None
```

```bash
uv run pytest tests/integration/test_mcp.py -v -m integration
```

### Task 3.4: Commit Phase 3

```bash
git add src/pia/mcp tests/unit/test_mcp_tools.py tests/integration/test_mcp.py
git commit -m "Phase 3: kz-data MCP server (4 tools) + Tavily client wrapper"
```

**Phase 3 done when:** the kz-data server starts, exposes 4 tools, and a Python client can call each successfully.

---

## Phase 4 — Day 5 (Wed 2026-05-06): Agents and message bus

**Goal of phase:** Three agents (Portfolio / Market / Planner) on a typed Pydantic message bus, end-to-end CLI works for one query (`uv run python -m pia.cli ask "What is my current allocation?"`), Planner attaches the disclaimer.

### Task 4.1: Pydantic message types

**Files:**
- Create: `src/pia/messages.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Citation(BaseModel):
    source: str
    source_url: str
    published_at: str | None = None
    snippet: str | None = None
    score: float | None = None


class PortfolioQuery(BaseModel):
    question: str
    asset_class: str | None = None
    ticker: str | None = None


class PortfolioAnswer(BaseModel):
    text: str
    citations: list[Citation] = []
    used_holdings: bool = False


class MarketQuery(BaseModel):
    question: str
    tickers: list[str] = []


class MarketSource(BaseModel):
    tool: str
    url: str | None = None
    last_updated: str | None = None


class MarketAnswer(BaseModel):
    text: str
    sources: list[MarketSource] = []
    degraded: bool = False  # set when an upstream tool failed


class Action(BaseModel):
    summary: str
    rationale: str


class Recommendation(BaseModel):
    summary: str
    actions: list[Action] = []
    citations: list[Citation] = []
    market_sources: list[MarketSource] = []
    disclaimer: str = (
        "This is informational only and not licensed financial, legal, or tax advice. "
        "Consult a licensed professional before acting."
    )


class AgentMessage(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    sender: str
    receiver: str
    issued_at: datetime = Field(default_factory=_utcnow)
    payload: BaseModel  # one of the *Query / *Answer / Recommendation types

    model_config = {"arbitrary_types_allowed": True}
```

### Task 4.2: LLM client wrapper (TDD)

**Files:**
- Create: `src/pia/llm/client.py`
- Test: `tests/unit/test_llm_client.py`

- [ ] **Step 1: Test (mocked)**

```python
from unittest.mock import patch

from pia.llm.client import LLMClient


def test_llm_client_chat_simple():
    fake = {"choices": [{"message": {"content": "hi"}}]}
    with patch("pia.llm.client.litellm.completion", return_value=fake):
        out = LLMClient(model="gemini/gemini-2.0-flash").chat([{"role": "user", "content": "hello"}])
    assert out["content"] == "hi"
```

- [ ] **Step 2: Implement**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import litellm

from pia.config import get_settings


@dataclass
class LLMClient:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        s = get_settings()
        self.model = self.model or s.llm_model
        self.temperature = self.temperature if self.temperature is not None else s.llm_temperature
        self.max_tokens = self.max_tokens or s.llm_max_tokens

    def chat(self, messages: list[dict[str, Any]], tools: list[dict] | None = None) -> dict:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = litellm.completion(**kwargs)
        msg = resp["choices"][0]["message"]
        return {
            "content": msg.get("content") or "",
            "tool_calls": msg.get("tool_calls") or [],
        }
```

### Task 4.3: BaseAgent with tool-call loop

**Files:**
- Create: `src/pia/agents/base.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pia.llm.client import LLMClient


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Any]


@dataclass
class BaseAgent:
    name: str
    system_prompt: str
    tools: list[Tool] = field(default_factory=list)
    llm: LLMClient = field(default_factory=LLMClient)
    max_tool_calls: int = 8

    def _tool_schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.tools
        ]

    def run(self, user_message: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        for _ in range(self.max_tool_calls):
            resp = self.llm.chat(messages, tools=self._tool_schemas() or None)
            if not resp["tool_calls"]:
                return resp["content"]
            for call in resp["tool_calls"]:
                fn = call["function"]
                tool = next((t for t in self.tools if t.name == fn["name"]), None)
                if tool is None:
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": f"Error: unknown tool {fn['name']}"})
                    continue
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError as e:
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": f"Error: invalid JSON args: {e}"})
                    continue
                try:
                    result = tool.handler(**args)
                except Exception as e:  # noqa: BLE001 — degraded answer path
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": f"ToolError: {type(e).__name__}: {e}"})
                    continue
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, ensure_ascii=False, default=str)})
        return resp["content"] or "(no response — tool-call budget exhausted)"
```

### Task 4.4: Portfolio Agent

**Files:**
- Create: `src/pia/agents/portfolio.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

import json
from pathlib import Path

from pia.agents.base import BaseAgent, Tool
from pia.config import get_settings
from pia.messages import Citation, PortfolioAnswer, PortfolioQuery
from pia.rag.retrieve import retrieve

_SYSTEM = """You are the Portfolio Agent. You answer questions about the user's holdings, plan, and personal notes.

Rules:
- Use the `retrieve` tool to find the user's notes/plan/holdings before answering.
- Use the `get_holdings` tool to read structured holdings JSON.
- If you cannot find evidence in the user's data, say "I don't have that information." — never guess.
- Always return citations.
"""


def _retrieve_tool(query: str, source: str | None = None, k: int = 5) -> list[dict]:
    chunks = retrieve(query, k=k, source=source)
    return [
        {"text": c.text, "source": c.source, "source_url": c.source_url, "score": c.score, "language": c.language}
        for c in chunks
    ]


def _get_holdings() -> dict:
    p = Path(get_settings().data_dir) / "personal/holdings.json"
    return json.loads(p.read_text())


def make_portfolio_agent() -> BaseAgent:
    return BaseAgent(
        name="portfolio",
        system_prompt=_SYSTEM,
        tools=[
            Tool(
                name="retrieve",
                description="Search the user's notes/plan/holdings/news/etc. for context.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "source": {"type": "string", "enum": ["user_note", "user_plan", "user_holdings", "news", "bank_rates", "kase", "nbk", "real_estate"]},
                        "k": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                handler=_retrieve_tool,
            ),
            Tool(
                name="get_holdings",
                description="Return the user's structured holdings JSON.",
                parameters={"type": "object", "properties": {}},
                handler=_get_holdings,
            ),
        ],
    )


def ask_portfolio(query: PortfolioQuery) -> PortfolioAnswer:
    agent = make_portfolio_agent()
    text = agent.run(query.question)
    chunks = retrieve(query.question, k=5)
    cites = [
        Citation(source=c.source, source_url=c.source_url, published_at=c.published_at, snippet=c.text[:200], score=c.score)
        for c in chunks[:3]
    ]
    return PortfolioAnswer(text=text, citations=cites, used_holdings=True)
```

### Task 4.5: Market Agent

**Files:**
- Create: `src/pia/agents/market.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

from pia.agents.base import BaseAgent, Tool
from pia.mcp.client import kz_data_call_sync, web_search_sync
from pia.messages import MarketAnswer, MarketQuery, MarketSource

_SYSTEM = """You are the Market Agent. You answer questions about current market state for KZ:
NBK rate, FX, KASE quotes, bank deposit rates, and breaking news.

Rules:
- Always call a tool before stating a number — do not invent.
- Surface the `last_updated`/`as_of` field from tools so the user knows staleness.
- If a tool fails, say so plainly and continue with what you have.
"""


def make_market_agent() -> BaseAgent:
    return BaseAgent(
        name="market",
        system_prompt=_SYSTEM,
        tools=[
            Tool("get_nbk_rate", "NBK base rate at a date or latest.",
                 {"type": "object", "properties": {"date_str": {"type": "string"}}},
                 handler=lambda **kw: kz_data_call_sync("get_nbk_rate", **kw)),
            Tool("get_fx_rate", "FX spot or historical for KZT/USD, KZT/EUR, KZT/RUB.",
                 {"type": "object", "properties": {"pair": {"type": "string"}, "date_str": {"type": "string"}}, "required": ["pair"]},
                 handler=lambda **kw: kz_data_call_sync("get_fx_rate", **kw)),
            Tool("get_kase_quote", "Latest KASE snapshot for a ticker.",
                 {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
                 handler=lambda **kw: kz_data_call_sync("get_kase_quote", **kw)),
            Tool("get_deposit_rates", "Bank deposit rates across banks for a currency and term.",
                 {"type": "object", "properties": {"currency": {"type": "string"}, "term_months": {"type": "integer"}}, "required": ["currency", "term_months"]},
                 handler=lambda **kw: kz_data_call_sync("get_deposit_rates", **kw)),
            Tool("web_search", "Public web search for breaking news and external context.",
                 {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}}, "required": ["query"]},
                 handler=lambda **kw: web_search_sync(**kw)),
        ],
    )


def ask_market(query: MarketQuery) -> MarketAnswer:
    agent = make_market_agent()
    text = agent.run(query.question)
    sources = [MarketSource(tool="kz-data", url=None)]
    return MarketAnswer(text=text, sources=sources)
```

### Task 4.6: Planner / Advisor

**Files:**
- Create: `src/pia/agents/planner.py`

- [ ] **Step 1: Implement**

```python
from __future__ import annotations

from pia.agents.base import BaseAgent, Tool
from pia.agents.market import ask_market
from pia.agents.portfolio import ask_portfolio
from pia.messages import (
    Action,
    MarketQuery,
    MarketSource,
    PortfolioQuery,
    Recommendation,
)

_SYSTEM = """You are the Planner / Advisor. You combine the user's portfolio context with current market state to produce evidence-backed recommendations.

Rules:
- ALWAYS call `ask_portfolio` first to ground in what the user owns and their plan.
- Call `ask_market` when current numbers (rates/FX/quotes/news) are needed.
- Do NOT issue definitive buy/sell instructions. Use hedged language: "consider", "based on the evidence", and reference your sources.
- Cite the user's plan and current data in every actionable recommendation.
- Output should be concise: 2-4 short sections at most.
"""


def make_planner() -> BaseAgent:
    return BaseAgent(
        name="planner",
        system_prompt=_SYSTEM,
        tools=[
            Tool(
                name="ask_portfolio",
                description="Ask the Portfolio Agent about the user's holdings/plan/notes.",
                parameters={"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
                handler=lambda question: ask_portfolio(PortfolioQuery(question=question)).model_dump(),
            ),
            Tool(
                name="ask_market",
                description="Ask the Market Agent about current rates/FX/KASE/deposits/news.",
                parameters={"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
                handler=lambda question: ask_market(MarketQuery(question=question)).model_dump(),
            ),
        ],
    )


def advise(user_text: str) -> Recommendation:
    planner = make_planner()
    summary = planner.run(user_text)
    # Light post-processing: hedge language enforcement (best-effort guardrail)
    if any(p in summary.lower() for p in [" buy ", " sell ", "recommend buying", "recommend selling"]):
        summary = "Hedged note: " + summary
    return Recommendation(
        summary=summary,
        actions=[],
        citations=[],
        market_sources=[MarketSource(tool="planner")],
    )
```

### Task 4.7: CLI

**Files:**
- Create: `src/pia/cli.py`

- [ ] **Step 1: Implement**

```python
"""CLI entry: uv run python -m pia.cli ask "your question"."""
from __future__ import annotations

import typer
from rich import print

from pia.agents.planner import advise

app = typer.Typer(help="Personal Investment-Planning Assistant CLI")


@app.command()
def ask(question: str) -> None:
    rec = advise(question)
    print(f"[bold]{rec.summary}[/]\n")
    print(f"[dim]{rec.disclaimer}[/]")


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Smoke run**

Set up env and run a query:
```bash
docker compose up -d weaviate
uv run python -m scripts.ingest --reset      # if not yet ingested
export LLM_MODEL=gemini/gemini-2.0-flash      # or your preferred provider
export GOOGLE_API_KEY=...                     # paid run optional
uv run python -m pia.cli ask "Какая у меня текущая аллокация по классам активов?"
```
Expected: a coherent answer; disclaimer is appended.

### Task 4.8: Commit Phase 4

```bash
git add src/pia/messages.py src/pia/llm src/pia/agents src/pia/cli.py tests/unit/test_llm_client.py
git commit -m "Phase 4: 3 agents (Portfolio/Market/Planner) on Pydantic bus + LiteLLM client + CLI"
```

**Phase 4 done when:** `uv run python -m pia.cli ask "..."` returns a coherent answer with disclaimer for at least one portfolio question and one market question.

---

## Phase 5 — Day 6 (Thu 2026-05-07): Streamlit UI + smoke

**Goal of phase:** Streamlit chat UI with portfolio sidebar, citation chips, disclaimer banner, allocation/currency-exposure pie charts. Five representative queries return useful answers end-to-end.

### Task 5.1: Streamlit shell

**Files:**
- Create: `src/pia/ui/app.py`

- [ ] **Step 1: Implement**

```python
"""Streamlit entry: uv run streamlit run src/pia/ui/app.py"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import streamlit as st

from pia.agents.planner import advise
from pia.config import get_settings


st.set_page_config(page_title="Personal Investment Assistant", page_icon="💼", layout="wide")


def _load_holdings() -> dict:
    p = Path(get_settings().data_dir) / "personal/holdings.json"
    return json.loads(p.read_text())


def _allocation_df(holdings: dict) -> pd.DataFrame:
    by_class: dict[str, float] = defaultdict(float)
    for pos in holdings["positions"]:
        kzt = _to_kzt(pos)
        by_class[pos["asset_class"]] += kzt
    return pd.DataFrame({"asset_class": list(by_class), "kzt": list(by_class.values())})


def _currency_df(holdings: dict) -> pd.DataFrame:
    by_ccy: dict[str, float] = defaultdict(float)
    for pos in holdings["positions"]:
        by_ccy[pos["currency"]] += _to_kzt(pos)
    return pd.DataFrame({"currency": list(by_ccy), "kzt": list(by_ccy.values())})


def _to_kzt(pos: dict) -> float:
    fx = {"KZT": 1.0, "USD": 470.0, "EUR": 510.0}
    if "amount" in pos:
        return pos["amount"] * fx.get(pos["currency"], 1.0)
    return pos.get("shares", 0) * pos.get("avg_cost", 0) * fx.get(pos["currency"], 1.0)


# --- top banner ---
st.warning(
    "Informational only. **Not** licensed financial, legal, or tax advice. Consult a licensed professional before acting.",
    icon="⚠️",
)

st.title("💼 Personal Investment-Planning Assistant")

with st.sidebar:
    st.header("Portfolio")
    holdings = _load_holdings()
    alloc = _allocation_df(holdings)
    ccy = _currency_df(holdings)
    st.caption(f"As of {holdings['as_of']}")
    st.dataframe(alloc, hide_index=True, use_container_width=True)
    st.subheader("By asset class")
    st.bar_chart(alloc, x="asset_class", y="kzt")
    st.subheader("By currency")
    st.bar_chart(ccy, x="currency", y="kzt")

# --- chat ---
if "history" not in st.session_state:
    st.session_state.history = []

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

if user_text := st.chat_input("Ask about your portfolio, the market, or what to do next…"):
    st.session_state.history.append(("user", user_text))
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            rec = advise(user_text)
        st.markdown(rec.summary)
        st.caption(rec.disclaimer)
    st.session_state.history.append(("assistant", rec.summary))
```

- [ ] **Step 2: Run**

```bash
docker compose up -d weaviate
uv run streamlit run src/pia/ui/app.py
```

Open http://localhost:8501. Verify:
1. Disclaimer banner shows.
2. Sidebar shows holdings + two charts.
3. Chat answers a basic question.

### Task 5.2: Five representative queries (manual smoke)

- [ ] **Step 1: Run each in the UI and note any failures**

1. "Какая у меня текущая аллокация по классам активов?" — expect summary referencing positions.
2. "Какая сейчас базовая ставка НБК?" — expect a tool call to get_nbk_rate; numeric answer with date.
3. "Стоит ли мне переложиться из Halyk в Каспи депозит?" — expect hedged comparison citing both rate sheets.
4. "Что в новостях этой недели про КЗТ?" — expect web_search call (or graceful note that Tavily is not configured).
5. "Recommend a buy on HSBK." — expect refusal/hedge per the safety rule.

- [ ] **Step 2: Capture issues**

Open `docs/draft-issues.md` (one-off scratch list) and write one bullet per issue. Each becomes a Phase 6 fix.

### Task 5.3: Commit Phase 5

```bash
git add src/pia/ui
git commit -m "Phase 5: Streamlit UI (chat + portfolio sidebar + allocation/currency charts + disclaimer)"
```

**Phase 5 done when:** all 5 queries return coherent answers; the safety query is refused/hedged.

---

## Phase 6 — Day 7 (Fri 2026-05-08): Draft polish + send

**Goal of phase:** Top-N issues from Phase 5.2 fixed. README is followable by a stranger. Repo is clean, tagged, and the draft is sent.

### Task 6.1: Triage and fix issues

- [ ] **Step 1: Order issues by user-visible severity**

Highest priority: the safety query gets refused; tool calls don't time out the UI; no Python tracebacks in the chat. Lower priority: cosmetics.

- [ ] **Step 2: Fix top 3-5 issues**

For each:
1. Reproduce in Streamlit.
2. Identify the file (Planner prompt, Market tool wrapper, UI exception handler, etc.).
3. Make the smallest change. Rerun the affected query.
4. Commit per fix: `git commit -m "fix: <short description>"`.

### Task 6.2: README quickstart pass

- [ ] **Step 1: Re-read the README as if you've never seen the repo**

Verify the Quickstart steps are sufficient. Add anything missing (e.g., "first run downloads the embedding model — ~600MB").

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README quickstart polish"
```

### Task 6.3: Tag the draft

- [ ] **Step 1: Tag**

```bash
git tag -a v0.1.0-draft -m "Pre-draft milestone: end-to-end working assistant"
```

### Task 6.4: Send draft

- [ ] **Step 1: Push branch**

```bash
git push origin feature/capstone_project
git push origin v0.1.0-draft
```

- [ ] **Step 2: Compose the draft handoff message**

Send the repository link + a short note: "End-to-end working draft. Days 8-16 cover tests (positive + adversarial), observability, safety, polish, deliverables (Architecture Blueprint, Self-Review, Executive Summary), and the demo video."

**Phase 6 done when:** the draft is pushed, tagged, and shared. Open issues are recorded in `docs/draft-issues.md` (becomes the punch-list for the post-draft plan). This is still not submission-ready until the post-draft compliance plan is complete.

---

## Post-Draft Required Coverage

The Days 8-16 post-draft plan must close the remaining binding requirements from `docs/requirements_addendum.md`, `docs/non_functional_requirements.md`, and `docs/success_criteria.md`:

- Positive and adversarial automated tests: prompt injection, jailbreaks, irrelevant queries, retrieval misses, MCP timeouts/errors, PII leakage, and hallucination probes.
- Observability: Langfuse tracing for agent/LLM/tool calls, basic metrics, structured error logging, and either a dashboard or diagnostics view.
- Safety: input sanitization, content filtering, PII detection/redaction, rate limiting, and graceful degraded-answer behavior.
- RAG QA: retrieval precision/recall or retrieval@k checks, source attribution tests, and hallucination/faithfulness checks.
- Local runtime polish: README quickstart for the local hybrid setup, local-only access-control note, and reproducible smoke-test commands.
- Required deliverables: Architecture Blueprint, Executive Summary, Self-Review, Video Demo link, and `Capstone_project_<First>_<Last>.txt`.

---

## Self-Review

### Spec coverage

| Spec section | Where covered |
|---|---|
| §1 Problem & users | Plan goal statement; corpus design (Phase 1) |
| §2 Scope (in/out) | Phase 1 corpus scope; agents scope in Phase 4 |
| §3 Architecture overview | Layout in this plan; Phases 0/2/3/4/5 build it |
| §4 Three agents | Tasks 4.4 / 4.5 / 4.6 |
| §5 Inter-agent comms | Task 4.1 messages; Task 4.6 Planner orchestrates |
| §6 Data model | Phase 1 in full |
| §7 RAG pipeline | Phase 2 in full |
| §8 MCP architecture | Phase 3 in full (consume + custom) |
| §9 LLM orchestration | Tasks 4.2 (LLMClient) and 4.3 (BaseAgent loop) |
| §10 Safety/guardrails | Disclaimer in Recommendation (Task 4.1); Planner system prompt (Task 4.6); hedge enforcement (Task 4.6). **Full PII / sanitization / rate-limit suite is in the post-draft plan.** |
| §11 Observability | Deferred to post-draft plan (out of pre-draft scope by design) |
| §12 Testing | Unit tests in each phase; smoke in Task 5.2; **adversarial suite is post-draft.** |
| §13 UI | Phase 5 |
| §14 Deployment / local runtime | Dockerized Weaviate from Phase 0; Streamlit app runs locally via `uv` |
| §15 Success-criteria mapping | Phase 6 draft handoff + post-draft required coverage |

### Placeholder scan
No "TBD"/"TODO"/"add appropriate handling" present. Every code block is complete. The post-draft items are explicitly out of scope for this plan and named in §15 of the spec.

### Type consistency
- `Document` and `Chunk` types used identically in Tasks 2.3, 2.4, 2.6.
- `RetrievedChunk` exported from `pia.rag.store` and consumed unchanged in `pia.rag.retrieve` (Task 2.5) and `pia.agents.portfolio` (Task 4.4).
- Tool handler signatures match between FastMCP server (Task 3.2), pure functions (Task 3.1), and client wrappers (Task 3.3).
- Agent message types defined in Task 4.1 are used unchanged in 4.4 / 4.5 / 4.6 / 5.1.

### Known omissions for this plan (intentional, covered in post-draft plan)
- Langfuse tracing and dashboards.
- Adversarial test suite (prompt injection, jailbreak refusal under fuzzing, MCP timeouts simulated, source-conflict scenarios, PII probe, hallucination probe).
- LLM-as-judge eval and golden-set scoring with thresholds.
- Full PII detector (Presidio or richer regex), input sanitization layer, rate limiter wiring on the agent entrypoint.
- Cross-encoder reranker.
- Allocation pie chart (the current Phase 5 uses bar charts — pie charts get added in post-draft polish).
- Architecture Blueprint, Self-Review, Executive Summary deliverable docs.
- Demo video script and recording.
