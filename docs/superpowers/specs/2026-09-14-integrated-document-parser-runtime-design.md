# 单仓库一键启动设计

## 目标

将平台源码和文档解析服务的干净源码放在同一个 Git 仓库中。新环境只需克隆一个仓库、分别配置三套依赖，之后通过根目录 `start.sh` 同时启动全部服务。

## 目录

- `document-parser/`：文档解析服务源码和它自己的 `.venv`。
- `backend/`：平台 FastAPI 源码和它自己的 `.venv`。
- `frontend/web/`：Vue 源码和 `node_modules`。
- `start.sh`：启动 8002、8001、5180 三个服务。
- `stop.sh`：只停止由 `start.sh` 记录的进程。
- `.env.local`：本地模型配置，不提交。
- `.runtime/`：本地日志、PID 和解析输出，不提交。

## 边界

- 不复制原项目 1.3 GB 的 `.venv`、缓存、模型、输出、样例文档或测试响应。
- 解析服务和平台后端使用不同虚拟环境，不合并 Python 依赖。
- 原解析配置中的地址、模型名和 API key 改为从 `.env.local` 读取。
- 用户页面只显示“公共服务平台智能体”，不暴露内部解析实现名称。
- `backend/data/documents/`保持本地未跟踪状态。

## 新环境使用流程

1. 克隆这一个仓库。
2. 用 Python 3.12 分别配置 `document-parser/.venv` 和 `backend/.venv`。
3. 在 `frontend/web` 执行 `pnpm install`。
4. 复制 `.env.local.example` 为 `.env.local` 并填写本地模型配置。
5. 在仓库根目录执行 `./start.sh`。
6. 需要停止时执行 `./stop.sh`。

## 验收

- 解析服务 `/health` 返回 200。
- 平台后端 OpenAPI 可见文档和公共问答路由。
- 门户首页返回 200。
- 通过平台接口完成一次上传、解析和内容查询。
- 公共问答接口可实际调用后端模型。
- Git 中不包含 API key、`.env.local`、`.venv`、`.runtime/` 和解析运行数据。
