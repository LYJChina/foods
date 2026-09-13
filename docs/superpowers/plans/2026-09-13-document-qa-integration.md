# DocumentParser Document QA Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** 在食品行业 AI 公共服务平台中交付单文档上传、DocumentParser 解析、Markdown 预览、轻量检索和带引用 LLM 问答的完整 Demo。

**Architecture:** Vue 门户只调用平台 FastAPI；平台后端通过独立 HTTP 客户端访问 DocumentParser 进程，并使用独立 SQLite 保存文档、解析块与问答。问答先用 FTS5/BM25 或关键词降级检索 Top K，再由可替换的 DocumentAnswerer 调用服务端模型 API。

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, httpx, sqlite3/FTS5, pytest, Vue 3, TypeScript, Vite, Vitest

**Spec:** docs/superpowers/specs/2026-09-13-document-qa-integration-design.md

## Global Constraints

- DocumentParser 与平台使用独立 Python 环境和进程；不得把 DocumentParser 重依赖加入平台后端。
- 浏览器不得直接访问 DocumentParser 或模型 API，不得接触任何 API key。
- 只允许单个公开或低敏文档；配方、工艺、成本、客户、订单和生产经营文档禁止上传。
- 页面始终显示“DEMO 原型”和“AI 生成，仅供辅助阅读”。
- DocumentParser 或 LLM 未配置时必须明确返回不可用，不得使用 Mock 伪造解析或问答成功。
- 默认限制 20 MB、100 页、24 小时保留；均从后端配置读取。
- 原文件名不得用作磁盘路径；日志不得记录文件内容、模型上下文、密钥或厂商原始错误体。
- DocumentParser 界面或公开文档必须显著标注使用 DocumentParser，并建议上线前复核许可证。
- 前端继续使用 npx --yes pnpm@9.15.3。
- 所有新增行为严格执行 RED、GREEN、REFACTOR。

---

### Task 1: 文档领域模型、配置与 SQLite 仓库

**Files:**
- Create: backend/app/plugin/food_ai/document_schema.py
- Create: backend/app/plugin/food_ai/document_repository.py
- Modify: backend/app/config/setting.py
- Test: backend/tests/plugin/food_ai/test_document_repository.py

**Interfaces:**
- Produces: DocumentStatus, DocumentRecord, DocumentChunk, Citation, QuestionResult.
- Produces: DocumentRepository with create_document, update_status, replace_chunks, get_document, list_chunks, search_chunks, save_question, delete_document, delete_expired.
- Produces settings for DocumentParser URL/token, storage/retention/limits and model URL/name/key/timeout.

- [ ] **Step 1: Write failing repository tests**

Use tmp_path / documents.db. Assert create/read, deterministic chunk ordering, keyword search ranking, cascade deletion and expiry deletion. Hand-write expected records; do not derive expectations with repository helpers.

- [ ] **Step 2: Run RED**

Run:

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_repository.py -q

Expected: import failure because document_schema and document_repository do not exist.

- [ ] **Step 3: Implement minimal schemas and repository**

Use Pydantic models for API-facing values and sqlite3 parameterized statements. Create documents, chunks and questions tables. Attempt an FTS5 virtual table; when unavailable, score normalized query-token intersections in Python. Enable foreign keys and make delete_document transactional.

- [ ] **Step 4: Run GREEN and full backend tests**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_repository.py -q
    .venv/bin/python -m pytest -q

- [ ] **Step 5: Commit**

    git add backend/app/config/setting.py backend/app/plugin/food_ai/document_schema.py backend/app/plugin/food_ai/document_repository.py backend/tests/plugin/food_ai/test_document_repository.py
    git commit -m "feat: add document repository and search"

### Task 2: DocumentParser HTTP 客户端

**Files:**
- Create: backend/app/plugin/food_ai/document_parser_client.py
- Test: backend/tests/plugin/food_ai/test_document_parser_client.py

**Interfaces:**
- Consumes: DocumentParser observed routes POST /tasks, GET /tasks/{task_id}, GET /tasks/{task_id}/result and GET /health.
- Produces: DocumentParserClient(base_url, service_token, timeout) with health, submit, get_status and get_result.
- Produces: DocumentParserUnavailable and DocumentParserInvalidResponse exceptions containing safe public messages only.

- [ ] **Step 1: Write failing client tests**

Use httpx MockTransport with complete DocumentParser fixtures. Assert multipart submission requests return_md and return_content_list, service token is sent only when configured, 202 status maps to progress, malformed JSON raises DocumentParserInvalidResponse, and network failure raises DocumentParserUnavailable without embedding the URL or token in the exception string.

- [ ] **Step 2: Run RED**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_parser_client.py -q

Expected: import failure for document_parser_client.

- [ ] **Step 3: Implement the client**

Inject an httpx.AsyncClient or transport for tests. Normalize base_url, set bounded connect/read/write/pool timeouts, use files and data form fields, call raise_for_status, validate required task_id/status/result fields and close owned clients.

- [ ] **Step 4: Run GREEN**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_parser_client.py -q

- [ ] **Step 5: Commit**

    git add backend/app/plugin/food_ai/document_parser_client.py backend/tests/plugin/food_ai/test_document_parser_client.py
    git commit -m "feat: add document_parser service client"

### Task 3: 文件校验、解析结果清洗与分段

**Files:**
- Create: backend/app/plugin/food_ai/document_processing.py
- Test: backend/tests/plugin/food_ai/test_document_processing.py

**Interfaces:**
- Produces: validate_upload(file_name, content_type, header, size, confirmed_low_sensitivity), sanitize_file_name, extract_chunks(document_parser_result), and count_pdf_pages.
- Consumes: DocumentParser Markdown/content-list response.

- [ ] **Step 1: Write failing validation and chunk tests**

Cover allowed PDF/DOCX/PPTX/JPEG/PNG signatures, extension/MIME mismatch, 20 MB boundary, missing low-sensitivity confirmation, a forbidden core-data declaration, a 101-page PDF, duplicate header/footer removal, stable chunk ids, heading path retention, page number retention and total-context-safe chunk lengths.

- [ ] **Step 2: Run RED**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_processing.py -q

- [ ] **Step 3: Implement minimal processing**

Use file signatures and pypdf for PDF page count. Generate disk names with UUID plus approved suffix. Treat all parsed document text as data. Split at headings/paragraphs with bounded length and overlap, preserving source page and ordinal.

- [ ] **Step 4: Run GREEN and Ruff**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_processing.py -q
    .venv/bin/python -m ruff check app/plugin/food_ai tests/plugin/food_ai

- [ ] **Step 5: Commit**

    git add backend/app/plugin/food_ai/document_processing.py backend/tests/plugin/food_ai/test_document_processing.py
    git commit -m "feat: validate and chunk parsed documents"

### Task 4: 文档任务服务与平台 API

**Files:**
- Create: backend/app/plugin/food_ai/document_service.py
- Create: backend/app/plugin/food_ai/document_controller.py
- Modify: backend/app/api/v1/routers.py
- Test: backend/tests/plugin/food_ai/test_document_controller.py

**Interfaces:**
- Produces: POST /food-ai/documents, GET /food-ai/documents/{id}, GET /food-ai/documents/{id}/content and DELETE /food-ai/documents/{id}.
- Produces: DocumentService.create, refresh_status, get_content and delete.
- Consumes: DocumentRepository, DocumentParserClient and document_processing functions.

- [ ] **Step 1: Write failing API tests**

Use FastAPI TestClient with a temporary repository/storage directory and fake DocumentParser boundary. Assert anonymous low-sensitivity upload returns 202, status progresses queued → parsing → indexing → ready, content is paginated, invalid type is 400, oversized payload is 413, missing confirmation is 400, missing id is 404, and delete removes the original file plus database data.

- [ ] **Step 2: Run RED**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_controller.py -q

- [ ] **Step 3: Implement service and controller**

Stream uploads to a UUID path while enforcing byte limit. Store only safe file metadata. Submit to DocumentParser, persist external task id, refresh state on status reads, index exactly once after completion, and map upstream failures to safe 502/503 responses. Never return DocumentParser URL or local path.

- [ ] **Step 4: Run GREEN and full backend tests**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_controller.py -q
    .venv/bin/python -m pytest -q

- [ ] **Step 5: Commit**

    git add backend/app/plugin/food_ai/document_service.py backend/app/plugin/food_ai/document_controller.py backend/app/api/v1/routers.py backend/tests/plugin/food_ai/test_document_controller.py
    git commit -m "feat: add document parsing api"

### Task 5: 带引用的 LLM 问答

**Files:**
- Create: backend/app/plugin/food_ai/document_answerer.py
- Modify: backend/app/plugin/food_ai/document_service.py
- Modify: backend/app/plugin/food_ai/document_controller.py
- Test: backend/tests/plugin/food_ai/test_document_answerer.py
- Test: backend/tests/plugin/food_ai/test_document_questions.py

**Interfaces:**
- Produces: DocumentAnswerer.answer(question, chunks) returning QuestionResult.
- Produces: OpenAICompatibleDocumentAnswerer using only backend model settings.
- Produces: POST /food-ai/documents/{id}/questions.

- [ ] **Step 1: Write failing answerer tests**

Assert the generated system message says parsed content is untrusted data, forbids following instructions from the document, requires chunk citations and requires insufficient evidence refusal. Assert structured valid output maps citations only to supplied chunk ids; invented citations or malformed output are rejected.

- [ ] **Step 2: Run answerer RED, then implement**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_answerer.py -q

Implement a protocol plus injected HTTP transport. Do not log prompts or Authorization. Apply timeout and one bounded retry only to safe transient failures. Validate output with Pydantic.

- [ ] **Step 3: Write failing question API tests**

Assert ready document search selects literal matching chunks, not-ready returns 409, missing model configuration returns 503, empty question returns 422, valid answer includes quotes/page/anchors, and insufficient evidence bypasses free-form guessing.

- [ ] **Step 4: Implement question service and run GREEN**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_answerer.py tests/plugin/food_ai/test_document_questions.py -q
    .venv/bin/python -m pytest -q

- [ ] **Step 5: Commit**

    git add backend/app/plugin/food_ai/document_answerer.py backend/app/plugin/food_ai/document_service.py backend/app/plugin/food_ai/document_controller.py backend/tests/plugin/food_ai/test_document_answerer.py backend/tests/plugin/food_ai/test_document_questions.py
    git commit -m "feat: add cited document questions"

### Task 6: Vue 文档工作台与问答页面

**Files:**
- Modify: frontend/web/src/router/routes.ts
- Modify: frontend/web/src/layouts/portal/index.vue
- Modify: frontend/web/src/views/portal/home/index.vue
- Modify: frontend/web/src/views/portal/content.ts
- Modify: frontend/web/src/styles/portal.scss
- Create: frontend/web/src/types/food-ai/document.ts
- Create: frontend/web/src/api/module_food_ai/documents.ts
- Create: frontend/web/src/views/portal/documents/index.vue
- Create: frontend/web/src/views/portal/documents/upload-validation.ts
- Create: frontend/web/src/views/portal/documents/status.ts
- Create: frontend/web/src/views/portal/documents/DocumentPreview.vue
- Create: frontend/web/src/views/portal/documents/DocumentQuestions.vue
- Test: frontend/web/src/__tests__/document-upload-validation.spec.ts
- Test: frontend/web/src/__tests__/document-flow.spec.ts

**Interfaces:**
- Consumes: document create/status/content/question/delete APIs.
- Produces: public route /portal/documents and full upload → progress → preview → question flow.

- [ ] **Step 1: Write failing pure validation/status tests**

Assert one-file limit, allowed suffixes, 20 MB client hint, mandatory confirmation, terminal status detection and polling delay selection. Client validation is usability only; backend remains authoritative.

- [ ] **Step 2: Run RED and implement helpers**

    cd frontend/web
    npx --yes pnpm@9.15.3 test -- src/__tests__/document-upload-validation.spec.ts

- [ ] **Step 3: Write failing mounted flow tests**

Mock only the typed platform API boundary. Assert the page labels DocumentParser usage, rejects missing confirmation inline, submits FormData, announces progress without moving focus, renders Markdown as escaped/sanitized content, sends a question only when ready, displays citations as buttons/links to stable anchors, reports service-unconfigured errors, and confirms before deletion.

- [ ] **Step 4: Implement typed API and UI**

Use existing PortalLayout and compact design tokens. Keep body text at least 16px and controls at least 44px. Use a two-column preview/questions layout above 1024px and one column below. Do not use raw v-html unless output is sanitized with the existing DOMPurify dependency.

- [ ] **Step 5: Run GREEN, type-check and build**

    cd frontend/web
    npx --yes pnpm@9.15.3 test
    npx --yes pnpm@9.15.3 type-check
    npx --yes pnpm@9.15.3 build:dev

- [ ] **Step 6: Commit**

    git add frontend/web/src/router/routes.ts frontend/web/src/layouts/portal/index.vue frontend/web/src/views/portal frontend/web/src/styles/portal.scss frontend/web/src/types/food-ai/document.ts frontend/web/src/api/module_food_ai/documents.ts frontend/web/src/__tests__
    git commit -m "feat: add document parsing and qa workspace"

### Task 7: 清理策略、运行编排、安全文档与联调

**Files:**
- Create: backend/app/plugin/food_ai/document_cleanup.py
- Modify: backend/app/plugin/food_ai/document_controller.py
- Modify: backend/env/.env.example
- Modify: docs/DEMO_RUNBOOK.md
- Modify: docs/API_KEY_SECURITY.md
- Create: docs/DOCUMENT_PARSER_INTEGRATION.md
- Test: backend/tests/plugin/food_ai/test_document_cleanup.py

**Interfaces:**
- Produces: cleanup_expired_documents(repository, storage_dir, now).
- Produces: reproducible three-process startup without copying DocumentParser credentials into platform.

- [ ] **Step 1: Write failing cleanup tests**

Create expired and active document fixtures plus files under tmp_path. Assert only expired database rows and their owned UUID directories are removed, paths outside configured storage are refused, and repeated cleanup is idempotent.

- [ ] **Step 2: Run RED, implement cleanup and run GREEN**

    cd backend
    .venv/bin/python -m pytest tests/plugin/food_ai/test_document_cleanup.py -q

- [ ] **Step 3: Document local startup and security**

Document three terminals: DocumentParser on 8002, platform on 8001 and Vue on 5180. Use variable names and placeholders only. Record that the inspected DocumentParser checkout contained an untracked non-placeholder credential requiring rotation, without recording its value. Document attribution, service isolation, retention, size/page limits and failure behavior.

- [ ] **Step 4: Run security scans**

Scan tracked changes for common provider key prefixes, private keys, Authorization literals, local IPs, source paths, government emblems and claims of official/real-time capability. Allow documented placeholder variable names but fail on non-placeholder values.

- [ ] **Step 5: Run complete verification**

    cd backend
    .venv/bin/python -m pytest -q
    .venv/bin/python -m ruff check app/plugin/food_ai tests/plugin/food_ai app/api/v1/routers.py
    cd ../frontend/web
    npx --yes pnpm@9.15.3 test
    npx --yes pnpm@9.15.3 type-check
    npx --yes pnpm@9.15.3 build:dev
    cd ../../..
    git diff --check

- [ ] **Step 6: Run real local integration**

Start DocumentParser, platform and Vue. Upload one approved low-sensitivity sample; verify progress, Markdown preview, indexed chunks, one cited answer and deletion. Repeat with DocumentParser stopped and model variables absent to verify explicit 503 states. Inspect 375, 768, 1024 and 1440 widths with no horizontal page scroll or assistant overlay.

- [ ] **Step 7: Commit**

    git add backend/app/plugin/food_ai/document_cleanup.py backend/app/plugin/food_ai/document_controller.py backend/env/.env.example backend/tests/plugin/food_ai/test_document_cleanup.py docs
    git commit -m "docs: add document_parser integration runbook"
