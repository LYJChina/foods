# Integrated Document Parser Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the existing document parser source into this repository and provide polished macOS start/stop commands that manage the parser, platform backend, and Vue frontend as one local development runtime.

**Architecture:** The repository keeps three isolated processes and two Python environments. A standard-library Python supervisor owns PID files, health checks, logs, startup rollback, and browser opening; thin `.command` launchers provide the double-click experience. Parser credentials move from Python literals to an ignored root `.env.local`, while the platform backend remains the only browser-facing API boundary.

**Tech Stack:** Python 3.12, `venv`, FastAPI/Uvicorn, Vue 3/Vite, macOS `.command` launchers, Python `unittest`/pytest, shell smoke checks

**Spec:** `docs/superpowers/specs/2026-09-14-integrated-document-parser-runtime-design.md`

## Global Constraints

- Public UI copy must continue to use “公共服务平台智能体” and must not expose the upstream parser implementation name.
- Preserve the parser license as a source-compliance file without linking it from the portal UI.
- Do not copy or commit `.venv`, caches, output directories, sample documents, generated responses, or any API key/private endpoint literal.
- `backend/data/documents/` is local runtime data; do not stage, delete, or rewrite it.
- Browsers call only the platform FastAPI service on port 8001; the parser remains a loopback-only internal service on port 8002.
- The supervisor may terminate only processes whose PID files it created and whose command identity still matches.
- An unknown process occupying 8001, 8002, or 5180 must never be killed automatically.
- Repository paths containing spaces and Chinese characters must work.
- First-run parser installation may be long, but subsequent starts must skip installation when the dependency fingerprint is unchanged.
- Secrets must never be written to logs, command output, tests, Git history, or frontend files.

---

### Task 1: Define the local runtime configuration contract

**Files:**
- Modify: `.gitignore`
- Create: `.env.local.example`
- Create: `scripts/scan_secrets.py`
- Create: `scripts/tests/test_runtime_config.py`
- Create: `scripts/dev_runtime.py`

**Interfaces:**
- Consumes: repository root, optional root `.env.local`, current process environment.
- Produces: `RuntimeConfig.load(repo_root: Path) -> RuntimeConfig`, a sanitized environment mapping for each child service, and a filename-only secret scanner for pre-commit verification.

- [ ] **Step 1: Write failing configuration tests**

  Add tests proving that `RuntimeConfig.load()` uses safe loopback defaults, lets real environment variables override `.env.local`, rejects malformed lines with the line number, and never includes secret values in `repr(config)`. Add a scanner test proving that findings report only file paths and never print the matching line or secret value.

  The required variables are `DOCUMENT_PARSER_URL`, `DOCUMENT_LLM_BASE_URL`, `DOCUMENT_LLM_MODEL`, `DOCUMENT_LLM_API_KEY`, `DOCUMENT_MULTIMODAL_BASE_URL`, `DOCUMENT_MULTIMODAL_MODEL`, `DOCUMENT_MULTIMODAL_API_KEY`, `DOCUMENT_LLM_TIMEOUT_SECONDS`, `DOCUMENT_MULTIMODAL_TIMEOUT_SECONDS`, and `DOCUMENT_MULTIMODAL_MAX_CONCURRENCY`.

- [ ] **Step 2: Run the tests and verify RED**

  Run: `python3 -m pytest scripts/tests/test_runtime_config.py -q`

  Expected: FAIL because `scripts.dev_runtime` does not exist.

- [ ] **Step 3: Implement the minimal configuration loader**

  Create `scripts/dev_runtime.py` with immutable dataclasses for configuration. Parse `.env.local` without executing it as shell code. Accept comments, blank lines, and quoted scalar values. Use `os.environ` as the highest-priority source. Redact every field whose name contains `KEY`, `TOKEN`, `SECRET`, or `PASSWORD` from representations and diagnostic output.

  Create `scripts/scan_secrets.py` to scan caller-supplied files for credential-shaped values and prohibited copied private endpoints. Its only finding output is the affected relative path; it returns nonzero when findings exist.

  The example file contains only empty placeholders and loopback URLs. It explains that `.env.local` is local-only and that keys must not be committed.

  Add `.env.local`, `.runtime/`, and `services/document_parser/.venv/` to `.gitignore`.

- [ ] **Step 4: Verify GREEN and static secret safety**

  Run: `python3 -m pytest scripts/tests/test_runtime_config.py -q`

  Run: `python3 scripts/scan_secrets.py .env.local.example scripts/dev_runtime.py scripts/scan_secrets.py scripts/tests/test_runtime_config.py`

  Expected: PASS with no output. The scanner must never print matching lines.

- [ ] **Step 5: Commit the configuration contract**

  Run: `git add .gitignore .env.local.example scripts/dev_runtime.py scripts/scan_secrets.py scripts/tests/test_runtime_config.py && git commit -m "feat: define unified local runtime configuration"`

---

### Task 2: Vendor the parser source without runtime debris or credentials

**Files:**
- Create: `services/document_parser/pyproject.toml`
- Create: `services/document_parser/LICENSE.md`
- Create: `services/document_parser/src/mineru/**`
- Create: `services/document_parser/tests/test_distribution_boundary.py`
- Modify: `services/document_parser/src/mineru/utils/multimodal_config.py`

**Interfaces:**
- Consumes: `/Users/liuyijie/Desktop/my_project/MinerU/mineru`, its root `pyproject.toml`, and `LICENSE.md`.
- Produces: an installable parser distribution whose existing `mineru-api` console entry point remains operational inside `services/document_parser/.venv`.

- [ ] **Step 1: Write a failing distribution-boundary test**

  Assert that the vendored service contains packaging metadata, the API entry point, and the license. Recursively assert that it contains no `.venv`, `__pycache__`, `.pyc`, `output`, `output-local`, response dump, sample document, nested duplicate source tree, or credential literal. Assert that multimodal configuration obtains URL, model, key, timeout, and concurrency from environment variables.

- [ ] **Step 2: Run the test and verify RED**

  Run: `python3 -m pytest services/document_parser/tests/test_distribution_boundary.py -q`

  Expected: FAIL because the vendored service is not present.

- [ ] **Step 3: Copy only the required source and metadata**

  Use an explicit allowlist: root `pyproject.toml`, root `LICENSE.md`, and the root `mineru/` package. Exclude cache files mechanically. Do not copy the existing `.venv`, `data`, `demo`, `docs`, `output`, `output-local`, `MinerU-master`, egg-info, local test scripts, or generated files.

  Keep the internal package name unchanged so the upstream imports and entry point remain valid. Repository-facing directory and process labels use `document_parser`.

- [ ] **Step 4: Replace hard-coded multimodal settings**

  Change the copied configuration module so all sensitive values come from `os.environ`. Loopback-safe or empty values are the only defaults. Preserve the existing prompt and parser behavior unless a test proves an environment-related change is required.

- [ ] **Step 5: Verify the source boundary**

  Run: `python3 -m pytest services/document_parser/tests/test_distribution_boundary.py -q`

  Run a filename-only secret scan across tracked and untracked candidate source files before staging. Expected: PASS with zero secret-bearing files.

- [ ] **Step 6: Commit the vendored service**

  Run: `git add services/document_parser && git commit -m "feat: add internal document parser service"`

---

### Task 3: Implement dependency bootstrap and service definitions

**Files:**
- Modify: `scripts/dev_runtime.py`
- Create: `scripts/tests/test_runtime_bootstrap.py`
- Create: `scripts/tests/test_runtime_services.py`

**Interfaces:**
- Consumes: `RuntimeConfig`, repository layout, installed Python and pnpm executables.
- Produces: `ensure_parser_environment()`, `ServiceSpec`, and `build_service_specs()` for parser, backend, and frontend.

- [ ] **Step 1: Write failing bootstrap tests**

  Test with temporary directories and fake command runners. Cover: creating a missing parser venv, installing editable `.[pipeline]`, writing a SHA-256 fingerprint only after successful installation, skipping installation when the fingerprint matches, and retrying after a failed installation.

- [ ] **Step 2: Write failing service-definition tests**

  Assert exact working directories, commands, ports, health URLs, log names, and environment subsets. Ensure the parser binds `127.0.0.1:8002`, backend binds `127.0.0.1:8001`, and frontend binds `127.0.0.1:5180`. Assert that the frontend receives no model key.

- [ ] **Step 3: Run both tests and verify RED**

  Run: `python3 -m pytest scripts/tests/test_runtime_bootstrap.py scripts/tests/test_runtime_services.py -q`

  Expected: FAIL because bootstrap and service definitions are absent.

- [ ] **Step 4: Implement bootstrap and service specifications**

  Use injectable command execution so tests never install ML packages. Select a supported Python interpreter, create the venv with `python -m venv`, update pip, and install `-e services/document_parser[pipeline]`. Hash the parser `pyproject.toml` plus interpreter version for the fingerprint.

  Backend and frontend preflight checks must not silently reinstall their full dependency sets. Instead, detect missing `backend/.venv/bin/uvicorn` or `frontend/web/node_modules/.bin/vite` and print the exact preparation command.

- [ ] **Step 5: Verify GREEN**

  Run: `python3 -m pytest scripts/tests/test_runtime_bootstrap.py scripts/tests/test_runtime_services.py -q`

- [ ] **Step 6: Commit bootstrap and service definitions**

  Run: `git add scripts/dev_runtime.py scripts/tests && git commit -m "feat: bootstrap local document parser runtime"`

---

### Task 4: Implement safe multi-process lifecycle supervision

**Files:**
- Modify: `scripts/dev_runtime.py`
- Create: `scripts/tests/test_runtime_lifecycle.py`

**Interfaces:**
- Consumes: `ServiceSpec` values and `.runtime/{logs,pids}`.
- Produces: `RuntimeSupervisor.start()`, `.stop()`, `.restart()`, `.status()`, and `.logs()` plus CLI exit codes.

- [ ] **Step 1: Write failing lifecycle tests**

  Using temporary directories and controllable fake processes, test:

  - dependency-order startup and reverse-order rollback;
  - reuse of an already healthy managed service;
  - refusal to kill an unknown listener;
  - stale PID cleanup;
  - PID identity verification before termination;
  - readiness timeout with service name and log path;
  - backend health verification that requires the assistant route;
  - stop affecting only supervisor-owned processes;
  - no secret values in errors or log headers.

- [ ] **Step 2: Run lifecycle tests and verify RED**

  Run: `python3 -m pytest scripts/tests/test_runtime_lifecycle.py -q`

  Expected: FAIL because lifecycle supervision is absent.

- [ ] **Step 3: Implement process ownership and health checks**

  Start children with explicit working directories, append-only per-service logs, and PID metadata containing PID, command fingerprint, start time, and repository root. Before stopping, confirm both PID liveness and command identity. Use HTTP probes with bounded retries and no external dependency.

  If a port is occupied by an unmanaged unhealthy service, stop with an actionable message. If it is occupied by a compatible healthy service, report it as externally managed and reuse it without creating a PID file or later stopping it.

- [ ] **Step 4: Implement CLI commands and terminal presentation**

  Add `start`, `stop`, `restart`, `status`, and `logs`. Default to `start`. Render a compact table with ANSI colors only when stdout is a TTY and `NO_COLOR` is unset. Never include the environment mapping in output.

  On complete startup, invoke macOS `open` for the portal URL unless `--no-open` is provided. The command exits zero only when all health checks pass.

- [ ] **Step 5: Verify GREEN**

  Run: `python3 -m pytest scripts/tests/test_runtime_lifecycle.py -q`

  Run: `NO_COLOR=1 python3 scripts/dev_runtime.py status`

  Expected: tests pass and status output remains aligned without escape sequences.

- [ ] **Step 6: Commit lifecycle supervision**

  Run: `git add scripts/dev_runtime.py scripts/tests/test_runtime_lifecycle.py && git commit -m "feat: supervise local platform services"`

---

### Task 5: Add double-click launchers and operator documentation

**Files:**
- Create: `start.command`
- Create: `stop.command`
- Modify: `README.md`
- Modify: `frontend/web/README.md`
- Create: `scripts/tests/test_runtime_launchers.py`

**Interfaces:**
- Consumes: `scripts/dev_runtime.py` CLI.
- Produces: macOS double-click entry points and a single authoritative local-running guide.

- [ ] **Step 1: Write failing launcher tests**

  Assert that both files use a portable shebang, resolve their own directory safely, quote paths, delegate to the Python supervisor, preserve the exit code, and are executable. Assert that no launcher sources `.env.local` as shell code.

- [ ] **Step 2: Run launcher tests and verify RED**

  Run: `python3 -m pytest scripts/tests/test_runtime_launchers.py -q`

  Expected: FAIL because the launchers do not exist.

- [ ] **Step 3: Implement the launchers**

  `start.command` changes to its own repository directory and executes `python3 scripts/dev_runtime.py start "$@"`. `stop.command` does the same with `stop "$@"`. Both print a short failure hint and keep the Terminal window readable on errors without pausing successful launches unnecessarily.

  Apply executable permissions with `chmod +x start.command stop.command`.

- [ ] **Step 4: Update documentation**

  Make `./start.command` the primary local start path and `./stop.command` the primary stop path. Document first-run duration, `.env.local` setup, status/log commands, port ownership safety, and manual fallback commands. Do not expose key examples that resemble real credentials.

- [ ] **Step 5: Verify GREEN**

  Run: `python3 -m pytest scripts/tests/test_runtime_launchers.py -q`

  Run: `git diff --check`

- [ ] **Step 6: Commit launchers and docs**

  Run: `git add start.command stop.command README.md frontend/web/README.md scripts/tests/test_runtime_launchers.py && git commit -m "feat: add one-command local platform launcher"`

---

### Task 6: Migrate local configuration and perform end-to-end verification

**Files:**
- Local-only create: `.env.local` (never stage)
- Modify if required by verified incompatibility: `backend/app/config/setting.py`
- Modify if required by verified incompatibility: `backend/app/plugin/food_ai/document_parser_client.py`
- Test: existing frontend and backend suites plus runtime supervisor suites

**Interfaces:**
- Consumes: the user's existing local parser settings without displaying them.
- Produces: a working one-command local runtime and verified document parsing/assistant routes.

- [ ] **Step 1: Migrate secrets locally without printing them**

  Read the existing parser settings in-process, write only the required values to root `.env.local`, and set restrictive local permissions. Do not include the file contents in terminal output. Report only the variable names and whether each is set.

- [ ] **Step 2: Stop the legacy three-process runtime safely**

  Resolve current listeners and stop only the known existing processes after confirming their command lines. Do not delete their source directories or output. The new supervisor must then own newly started PIDs.

- [ ] **Step 3: Run the unified launcher**

  Run: `./start.command --no-open` if the launcher forwards arguments; otherwise run `python3 scripts/dev_runtime.py start --no-open` for automated verification.

  Expected: parser 8002 healthy, backend 8001 healthy with assistant route present, frontend 5180 HTTP 200.

- [ ] **Step 4: Exercise real boundaries**

  Submit a harmless small public test document through the platform backend rather than directly from the browser to the parser. Poll until ready or obtain a precise failure. Call the public assistant endpoint with a non-sensitive question. Verify that no frontend request contains a model key and no service log contains a key.

- [ ] **Step 5: Run all automated verification**

  Run: `python3 -m pytest scripts/tests services/document_parser/tests -q`

  Run: `cd backend && .venv/bin/pytest tests/plugin/food_ai -q && .venv/bin/ruff check app/plugin/food_ai tests/plugin/food_ai`

  Run: `cd frontend/web && pnpm vitest run && pnpm type-check && pnpm build`

  Run: `git diff --check`

  Run a filename-only secret scan over the exact staged tree. Confirm `.env.local`, `.runtime/`, parser `.venv`, and `backend/data/documents/` are absent from the index.

- [ ] **Step 6: Verify stop and restart behavior**

  Run the supervisor `stop`, confirm owned ports are released, then run `start --no-open` again and confirm all health probes pass. Confirm unrelated listeners, if any, were not changed.

- [ ] **Step 7: Commit any compatibility fixes**

  Only if Step 4 exposed a real interface mismatch, commit the minimal tested fix with `fix: align integrated document parser runtime`. Do not create a compatibility commit when no code change is required.

- [ ] **Step 8: Push the feature branch after final review**

  Push `feat/integrated-document-parser-runtime` only after all verification succeeds and no secrets or runtime data are staged. Merge into `main` only with explicit user approval.
