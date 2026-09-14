# Docker Demo Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Windows-friendly Docker Compose development stack for the parser, backend, and Vite portal.

**Architecture:** Three source-built containers share a private network. Only ports 8002, 8001, and 5180 are published to localhost. The backend receives the parser service DNS name and optional ignored `.env.local` model settings.

**Tech Stack:** Docker Compose v2, Python 3.12, FastAPI/Uvicorn, MinerU, Node 20, pnpm.

## Global Constraints

- Do not modify the existing production `docker/docker-compose.yaml`.
- Do not copy API keys into images or frontend assets.
- Keep the existing user change in `backend/app/config/setting.py`.

### Task 1: Add source-built service images

**Files:**
- Create: `docker/demo/backend.Dockerfile`
- Create: `docker/demo/parser.Dockerfile`
- Create: `docker/demo/web.Dockerfile`

- [ ] Add minimal Dockerfiles that install the existing backend, parser pipeline, and frontend lockfile dependencies and expose the service commands used by Compose.
- [ ] Run Dockerfile syntax inspection through Compose config validation.

### Task 2: Add development Compose entrypoint

**Files:**
- Create: `compose.demo.yaml`

- [ ] Define parser, backend, and web services with localhost-only published ports.
- [ ] Add health checks and dependency ordering.
- [ ] Load optional root `.env.local` into backend without baking it into an image.

### Task 3: Document and verify startup

**Files:**
- Modify: `README.md`

- [ ] Document `docker compose -f compose.demo.yaml up --build` and shutdown/log commands.
- [ ] Run `docker compose -f compose.demo.yaml config`.
- [ ] If Docker registry access is available, build and smoke-test `/health`, `/openapi.json`, and the portal root.
