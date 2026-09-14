# Docker Demo Runtime Design

## Goal

Provide a single Docker Compose command that runs the current public-portal
demo on Windows, without relying on the Unix-only `start.sh` virtualenv paths.

## Scope

The new development-only Compose stack will contain three services:

- `document-parser`: builds from `document-parser/`, exposes only `127.0.0.1:8002`, and stores parser output in a named volume.
- `backend`: builds from `backend/`, runs `uvicorn app:create_app --factory --lifespan off` on `8001`, reads `DOCUMENT_PARSER_URL=http://document-parser:8002`, and receives optional model configuration from the ignored root `.env.local` file.
- `web`: runs the Vite development server on `5180`; its API proxy targets `http://backend:8001` on the Compose network.

The existing `docker/docker-compose.yaml` remains untouched because it is the
upstream production stack and requires MySQL and Redis. The new stack will be
an explicitly named root-level development configuration.

## Configuration and Security

`.env.local` remains the sole local location for model keys. It is loaded into
the backend service only and is excluded by `.gitignore` and `.dockerignore`.
No key is copied into an image layer, frontend bundle, source file, or Compose
file. The service-to-service parser address is overridden inside Compose so it
does not depend on a host port.

## Runtime Behavior

`docker compose -f compose.demo.yaml up --build` builds and starts all three
services. Compose health checks make the backend wait for parser readiness and
the frontend wait for the backend. The public entry point is
`http://127.0.0.1:5180/web/#/portal/home`. The stack can be stopped with
`docker compose -f compose.demo.yaml down`.

The demo parser image intentionally omits the optional local `pipeline` extra,
which would pull a large PyTorch/CUDA runtime. First build still needs working
access to package registries; Docker does not bypass the existing local
proxy/TLS issue.

## Validation

Validation will run Compose configuration parsing, build the images, wait for
the three health endpoints, and request the portal summary through the backend.
Failure output is collected with `docker compose ... logs` without exposing
environment values.
