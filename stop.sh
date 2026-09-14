#!/bin/bash
set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_ROOT/.runtime/pids"

stop_service() {
  local name="$1" pidfile="$2"
  if [ ! -f "$pidfile" ]; then
    printf "%-12s %s\n" "$name" "未由当前脚本启动"
    return
  fi

  local pid
  pid="$(cat "$pidfile")"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    local attempt
    for attempt in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.2
    done
    printf "%-12s %s\n" "$name" "已停止"
  else
    printf "%-12s %s\n" "$name" "进程已不存在"
  fi
  rm -f "$pidfile"
}

printf "\n正在停止公共服务平台…\n\n"
stop_service "门户前端" "$PID_DIR/frontend.pid"
stop_service "平台后端" "$PID_DIR/backend.pid"
stop_service "文档解析" "$PID_DIR/document-parser.pid"
printf "\n已完成。\n\n"
