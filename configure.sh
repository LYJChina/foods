#!/bin/bash
set -eu

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env.local"
umask 077

existing_value() {
  local name="$1"
  if [ ! -f "$ENV_FILE" ]; then
    return 0
  fi
  awk -F= -v key="$name" '$1 == key {sub(/^[^=]*=/, ""); gsub(/^"|"$/, ""); print; exit}' "$ENV_FILE"
}

ask_value() {
  local label="$1" current="$2" fallback="$3" answer
  local display="$current"
  [ -n "$display" ] || display="$fallback"
  read -r -p "$label [$display]: " answer
  printf '%s' "${answer:-$display}"
}

ask_secret() {
  local label="$1" current="$2" answer
  read -r -s -p "$label（回车保留当前）: " answer
  printf '\n' >&2
  printf '%s' "${answer:-$current}"
}

printf '\n公共服务平台本地模型配置\n'
printf 'API key 输入时不会显示，配置只写入本机 .env.local。\n\n'

llm_url="$(ask_value '问答 API 地址' "$(existing_value DOCUMENT_LLM_BASE_URL)" 'https://api.deepseek.com')"
llm_model="$(ask_value '问答模型名称' "$(existing_value DOCUMENT_LLM_MODEL)" '请填写官方模型名称')"
llm_key="$(ask_secret '问答 API key' "$(existing_value DOCUMENT_LLM_API_KEY)")"
llm_timeout="$(ask_value '问答超时时间（秒）' "$(existing_value DOCUMENT_LLM_TIMEOUT_SECONDS)" '30')"

multimodal_url="$(ask_value '文档解析 API 地址' "$(existing_value MULTIMODAL_API_URL)" '请填写多模态模型地址')"
multimodal_model="$(ask_value '文档解析模型名称' "$(existing_value MULTIMODAL_MODEL)" '请填写官方模型名称')"
multimodal_key="$(ask_secret '文档解析 API key' "$(existing_value MULTIMODAL_API_KEY)")"
multimodal_timeout="$(ask_value '文档解析超时时间（秒）' "$(existing_value MULTIMODAL_TIMEOUT)" '120')"
multimodal_concurrency="$(ask_value '文档解析并发数' "$(existing_value MULTIMODAL_MAX_CONCURRENCY)" '2')"
layout_tokens="$(ask_value '版面解析最大 token 数' "$(existing_value MULTIMODAL_LAYOUT_MAX_TOKENS)" '8192')"
parser_url="$(existing_value DOCUMENT_PARSER_URL)"
parser_token="$(existing_value DOCUMENT_PARSER_TOKEN)"
[ -n "$parser_url" ] || parser_url='http://127.0.0.1:8002'

tmp_file="$(mktemp "$PROJECT_ROOT/.env.local.tmp.XXXXXX")"
cleanup() { rm -f "$tmp_file"; }
trap cleanup EXIT INT TERM

{
  printf '%s\n' '# Generated locally by configure.sh. Never commit this file.'
  printf 'DOCUMENT_LLM_BASE_URL=%s\n' "$llm_url"
  printf 'DOCUMENT_LLM_MODEL=%s\n' "$llm_model"
  printf 'DOCUMENT_LLM_API_KEY=%s\n' "$llm_key"
  printf 'DOCUMENT_LLM_TIMEOUT_SECONDS=%s\n' "$llm_timeout"
  printf 'MULTIMODAL_API_URL=%s\n' "$multimodal_url"
  printf 'MULTIMODAL_MODEL=%s\n' "$multimodal_model"
  printf 'MULTIMODAL_API_KEY=%s\n' "$multimodal_key"
  printf 'MULTIMODAL_TIMEOUT=%s\n' "$multimodal_timeout"
  printf 'MULTIMODAL_MAX_CONCURRENCY=%s\n' "$multimodal_concurrency"
  printf 'MULTIMODAL_LAYOUT_MAX_TOKENS=%s\n' "$layout_tokens"
  printf 'DOCUMENT_PARSER_URL=%s\n' "$parser_url"
  printf 'DOCUMENT_PARSER_TOKEN=%s\n' "$parser_token"
} > "$tmp_file"
chmod 600 "$tmp_file"
mv -f "$tmp_file" "$ENV_FILE"
trap - EXIT INT TERM

printf '\n配置已保存到 %s\n' "$ENV_FILE"
printf '下一步执行：./stop.sh && ./start.sh\n'
