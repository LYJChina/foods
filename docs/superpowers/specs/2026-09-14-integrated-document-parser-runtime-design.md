# Integrated Document Parser Runtime Design

## 1. Goal

Move the document parsing runtime currently located at `/Users/liuyijie/Desktop/my_project/MinerU` into the public-service platform repository and provide a single polished macOS entry point that starts the parser, FastAPI platform backend, and Vue frontend together.

The public interface continues to use the product name “公共服务平台智能体”. Upstream implementation names must not appear in page titles, labels, API responses, screenshots, or public-service navigation.

## 2. Confirmed Current State

- The Vue frontend runs on `127.0.0.1:5180`.
- The platform FastAPI service runs on `127.0.0.1:8001`.
- The document parser runs as an independent FastAPI process on `127.0.0.1:8002`.
- The platform backend communicates with the parser through `DOCUMENT_PARSER_URL`; browsers never call the parser directly.
- The parser source tree is approximately 4.1 MB, while its existing virtual environment is approximately 1.3 GB.
- The parser currently stores its multimodal API URL, model name, and API key in a Python source file. Those values must not be copied into the repository.
- `backend/data/documents/` contains local runtime data and must remain untracked and untouched.

## 3. Selected Architecture

### 3.1 Repository layout

Add a self-contained internal service at:

- `services/document_parser/src/`: copied parser package source required by the running API.
- `services/document_parser/pyproject.toml`: parser dependencies and console entry points.
- `services/document_parser/LICENSE.md`: upstream license retained as a source-compliance artifact; it is not linked from the portal UI.
- `services/document_parser/.env.local.example`: variable names and safe placeholders only.
- `scripts/dev_runtime.py`: cross-process development supervisor.
- `start.command`: double-clickable macOS launcher.
- `stop.command`: double-clickable macOS shutdown command.
- `.runtime/`: ignored PID files and logs.

Do not copy `.venv`, output directories, caches, sample documents, generated Markdown, test response dumps, duplicated nested source trees, or hard-coded secrets.

### 3.2 Process isolation

Keep three independent processes:

1. Document parser: its own `.venv`, port 8002.
2. Platform backend: existing `backend/.venv`, port 8001.
3. Vue frontend: existing `frontend/web/node_modules`, port 5180.

The parser remains out-of-process because its native and ML dependencies are substantially heavier than the platform backend. A parser crash or memory spike must not terminate the public API.

### 3.3 One-command lifecycle

`start.command` invokes `python3 scripts/dev_runtime.py start`. The supervisor:

1. Resolves all paths relative to the repository root, including paths containing spaces or Chinese characters.
2. Creates `.runtime/logs` and `.runtime/pids`.
3. Loads local configuration without printing secret values.
4. Detects an already healthy service and reuses it instead of creating a duplicate.
5. Refuses to kill an unknown process merely because it occupies a required port.
6. Creates the parser virtual environment on the first run and installs the checked-in parser project when required.
7. Checks that the existing backend environment and frontend dependencies are installed; if either is missing, it prints the exact setup command and stops instead of performing an unbounded platform installation.
8. Starts services in dependency order: parser, platform backend, frontend.
9. Waits for health probes before continuing to the next dependency.
10. Prints a compact aligned status table with service name, port, status, and log path.
11. Opens `http://127.0.0.1:5180/web/#/portal/home` after all probes pass.

`stop.command` invokes the same supervisor with `stop`. It terminates only PIDs previously written by the supervisor, waits for graceful exit, and removes stale PID files. It does not kill unrelated listeners.

Additional supported commands are `status`, `restart`, and `logs`, but the primary user flow remains double-clicking `start.command` and `stop.command`.

## 4. Configuration and Secret Migration

Create a root-local `.env.local` contract and add it to `.gitignore`. It contains:

- `DOCUMENT_PARSER_URL=http://127.0.0.1:8002`
- `DOCUMENT_LLM_BASE_URL`
- `DOCUMENT_LLM_MODEL`
- `DOCUMENT_LLM_API_KEY`
- `DOCUMENT_MULTIMODAL_BASE_URL`
- `DOCUMENT_MULTIMODAL_MODEL`
- `DOCUMENT_MULTIMODAL_API_KEY`
- timeout and concurrency settings required by the parser.

The supervisor exports the relevant subset into each child process. The parser configuration module reads environment variables at runtime and must contain no credential literal or private network endpoint. The existing secret values may be migrated locally into `.env.local`, but tools and tests may only report whether a key is configured; they must never display it.

`.env.local.example` contains placeholders and explanatory comments. Neither `.env.local` nor `.runtime/` may be staged or committed.

## 5. Parser Source Boundary

Copy only the source used by the current `mineru-api` process and the corresponding packaging metadata. Preserve its internal Python package imports to avoid an unsafe mass rename, but expose it to the rest of this repository only as the generic `document_parser` service.

No parser-specific route is exposed through the browser. The platform backend remains the sole public boundary and continues to translate parser status and results into the existing `/food-ai/documents` contract.

Because this is a local personal-learning setup, the portal UI does not display upstream attribution. If the platform is later offered as an online service to third parties or the copied source is redistributed, the license and attribution obligations must be reviewed before release.

## 6. Health, Logs, and Error Handling

Health probes:

- Parser: `GET http://127.0.0.1:8002/health` must return HTTP 200 and a healthy status.
- Backend: `GET http://127.0.0.1:8001/openapi.json` must return HTTP 200 and include `/food-ai/assistant/questions`.
- Frontend: `GET http://127.0.0.1:5180/web/` must return HTTP 200.

Logs are written separately:

- `.runtime/logs/document-parser.log`
- `.runtime/logs/backend.log`
- `.runtime/logs/frontend.log`

If one stage fails, the supervisor prints the failing service, a concise reason, and the log path. Services started during that unsuccessful run are stopped in reverse order. Existing healthy services that were reused are left running.

The terminal presentation uses restrained blue, green, amber, and red ANSI colors, clear Unicode status marks, and no marketing animation. Output must remain readable when ANSI color is unavailable.

## 7. Dependency Installation

Do not copy the existing 1.3 GB virtual environment. It contains absolute interpreter paths and is unsuitable for Git.

On first run, the supervisor creates `services/document_parser/.venv` with a supported local Python version and installs the parser in editable mode with the currently required pipeline extra. Subsequent runs use a dependency fingerprint to skip installation when `pyproject.toml` has not changed.

Large model caches stay in the user's normal cache directories and are not copied into the repository. The launcher reports first-run installation and model-loading time explicitly so a long initialization is not mistaken for a hang.

## 8. Compatibility and Non-goals

- Initial launcher support targets macOS because the current workspace and `.command` workflow are macOS-based.
- Shell quoting must support the repository path `/Users/liuyijie/Desktop/项目/shipin/platform`.
- The integration does not merge the parser into the platform FastAPI process.
- The integration does not add RAG storage, MCP endpoints, authentication, or production deployment.
- It does not copy existing parsed documents, output folders, caches, `.venv`, or API response dumps.
- It does not change the existing public document upload and question-answering interface.

## 9. Verification

Automated checks must cover:

- Configuration loading without secret disclosure.
- PID ownership and stale-PID handling.
- Unknown-port-owner refusal.
- Startup ordering and rollback after a failed health probe.
- Status output for healthy, stopped, and unhealthy services.
- Parser configuration rejects missing required model settings without exposing values.
- Repository scan confirms no credential-shaped value is tracked.
- `.env.local`, `.runtime/`, parser `.venv`, outputs, and caches are ignored.
- Existing platform frontend and backend tests still pass.

Manual acceptance:

1. From a stopped state, double-click `start.command`.
2. Observe a compact status display for all three services.
3. Confirm the portal opens automatically.
4. Upload a supported document and reach parsed content preview.
5. Submit one document question and one general assistant question.
6. Double-click `stop.command` and confirm all supervisor-owned processes stop.
7. Run `start.command` again and confirm it does not reinstall unchanged dependencies or create duplicate processes.

## 10. Delivery Boundary

Implementation will be developed on `feat/integrated-document-parser-runtime`. The runtime data directory remains local. Before any Git push, tracked files and diffs must be scanned for API keys, private endpoints, generated outputs, and virtual environments.
