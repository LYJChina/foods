#!/bin/bash
set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$PROJECT_ROOT/.runtime"
LOG_DIR="$PROJECT_ROOT/.runtime/logs"
PID_DIR="$PROJECT_ROOT/.runtime/pids"
mkdir -p "$LOG_DIR" "$PID_DIR" "$RUNTIME_DIR/parser-output"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

info() { printf "${BLUE}%-12s${RESET} %s\n" "$1" "$2"; }
ok() { printf "${GREEN}%-12s${RESET} %s\n" "$1" "$2"; }
warn() { printf "${YELLOW}%-12s${RESET} %s\n" "$1" "$2"; }
fail() { printf "${RED}%-12s${RESET} %s\n" "$1" "$2" >&2; }

if [ -f "$PROJECT_ROOT/.env.local" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$PROJECT_ROOT/.env.local"
  set +a
else
  warn "环境配置" "未找到 .env.local；可启动页面，模型功能需要先配置"
fi

export MINERU_API_OUTPUT_ROOT="${MINERU_API_OUTPUT_ROOT:-$RUNTIME_DIR/parser-output}"
export MINERU_API_MAX_CONCURRENT_REQUESTS="${MINERU_API_MAX_CONCURRENT_REQUESTS:-1}"
export MINERU_PROCESSING_WINDOW_SIZE="${MINERU_PROCESSING_WINDOW_SIZE:-1}"
export MINERU_PDF_RENDER_THREADS="${MINERU_PDF_RENDER_THREADS:-1}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8001}"

require_executable() {
  if [ ! -x "$1" ]; then
    fail "缺少环境" "$1"
    fail "处理方式" "$2"
    exit 1
  fi
}

require_executable "$PROJECT_ROOT/document-parser/.venv/bin/mineru-api" \
  "先按 README 配置 document-parser/.venv"
require_executable "$PROJECT_ROOT/backend/.venv/bin/uvicorn" \
  "先按 README 配置 backend/.venv"
require_executable "$PROJECT_ROOT/frontend/web/node_modules/.bin/vite" \
  "先安装 Node.js 和 pnpm，再在 frontend/web 执行 pnpm install"

port_is_busy() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

start_service() {
  local name="$1" port="$2" workdir="$3" logfile="$4" pidfile="$5"
  shift 5
  if port_is_busy "$port"; then
    fail "$name" "端口 $port 已被占用，请先停止旧服务"
    exit 1
  fi
  local previous_dir="$PWD"
  cd "$workdir" || exit 1
  "$@" >>"$logfile" 2>&1 &
  echo "$!" >"$pidfile"
  cd "$previous_dir" || exit 1
  info "$name" "正在启动（端口 ${port}）"
}

wait_http() {
  local name="$1" url="$2" logfile="$3"
  local attempt
  for attempt in $(seq 1 90); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      ok "$name" "已就绪"
      return 0
    fi
    sleep 1
  done
  fail "$name" "启动超时，查看日志：$logfile"
  "$PROJECT_ROOT/stop.sh" >/dev/null 2>&1 || true
  exit 1
}

printf "\n${BLUE}食品行业 AI 公共服务平台${RESET}\n"
printf "正在启动公共服务平台智能体…\n\n"

cleanup() {
  trap - EXIT INT TERM
  "$PROJECT_ROOT/stop.sh" >/dev/null 2>&1 || true
}
trap 'cleanup' EXIT INT TERM

start_service "文档解析" 8002 "$PROJECT_ROOT/document-parser" \
  "$LOG_DIR/document-parser.log" "$PID_DIR/document-parser.pid" \
  "$PROJECT_ROOT/document-parser/.venv/bin/mineru-api" --host 127.0.0.1 --port 8002
wait_http "文档解析" "http://127.0.0.1:8002/health" "$LOG_DIR/document-parser.log"

start_service "平台后端" 8001 "$PROJECT_ROOT/backend" \
  "$LOG_DIR/backend.log" "$PID_DIR/backend.pid" \
  "$PROJECT_ROOT/backend/.venv/bin/uvicorn" app:create_app --factory --lifespan off --host 127.0.0.1 --port 8001
wait_http "平台后端" "http://127.0.0.1:8001/openapi.json" "$LOG_DIR/backend.log"

start_service "门户前端" 5180 "$PROJECT_ROOT/frontend/web" \
  "$LOG_DIR/frontend.log" "$PID_DIR/frontend.pid" \
  "$PROJECT_ROOT/frontend/web/node_modules/.bin/vite" --mode development --host 127.0.0.1 --port 5180
wait_http "门户前端" "http://127.0.0.1:5180/web/" "$LOG_DIR/frontend.log"

printf "\n${GREEN}全部服务已启动${RESET}\n"
printf "首页：http://127.0.0.1:5180/web/#/portal/home\n"
printf "日志：%s\n\n" "$LOG_DIR"

if [ "${NO_OPEN:-0}" != "1" ] && command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:5180/web/#/portal/home"
fi

printf "当前终端会继续管理三个服务；按 Ctrl+C 可全部停止。\n"
wait
