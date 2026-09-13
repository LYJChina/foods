# 食品行业 AI 公共服务平台 Demo 运行手册

## 1. 交付范围

本项目在 FastapiAdmin 上游项目基础上增加匿名公开门户，包含：首页、出口合规预检、预检结果、六类场景展示和企业数智化轻量诊断。

所有页面均显示“DEMO 原型”。当前结果来自确定性 Mock 规则，只用于演示信息架构、交互流程和前后端调用，不代表正式政府系统，不构成认证、检验、合规或法律意见。

当前版本没有以下能力：

- 不上传或解析真实文件；
- 不调用 OCR、实时法规库、政府后台接口或真实大模型；
- 不保存配方、工艺、成本、客户、订单和生产经营数据；
- 不提供正式账号体系、业务审批、电子签章或监管认证；
- 不保证 Mock 结果适用于任何真实产品或目标市场。

## 2. 环境要求

- Python 3.12；
- Node.js 20 或更高版本；
- 前端固定使用 pnpm 9.15.3；
- 本地 Mock 联调无需 MySQL、Redis 和外部模型服务。

以下命令均从仓库根目录 `platform` 开始执行。不要提交任何 `.env` 文件。

## 3. 安装与启动

### 3.1 后端

首次准备虚拟环境：

    cd backend
    python3.12 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt

如果仓库依赖由 `uv` 管理，也可按上游说明使用 `uv sync`。本 Demo 已验证的轻量启动方式如下：

    cd backend
    .venv/bin/uvicorn app:create_app --factory --lifespan off --host 127.0.0.1 --port 8001

`--lifespan off` 用于跳过上游管理端的 MySQL、Redis 等生命周期依赖，仅适合本地 Mock 演示。需要验证完整管理端时，应恢复上游启动方式并配置数据库与 Redis。

可用以下地址检查后端：

- `GET http://127.0.0.1:8001/api/v1/food-ai/portal/summary`
- `GET http://127.0.0.1:8001/food-ai/portal/summary`

两种路径在当前应用配置下均可访问；前端统一使用 `/api/v1` 前缀。

### 3.2 前端

首次安装依赖：

    cd frontend/web
    npx --yes pnpm@9.15.3 install --frozen-lockfile

启动开发服务器并把 API 代理到本地后端：

    cd frontend/web
    VITE_API_BASE_URL=http://127.0.0.1:8001 npx --yes pnpm@9.15.3 dev --host 127.0.0.1

浏览器打开：

- 首页：`http://127.0.0.1:5180/web/#/portal/home`
- 出口预检：`http://127.0.0.1:5180/web/#/portal/precheck`
- 场景展示：`http://127.0.0.1:5180/web/#/portal/scenarios`
- 数智化诊断：`http://127.0.0.1:5180/web/#/portal/diagnosis`

公开门户无需登录。如果直接访问 `/web/portal/...` 被哈希路由带到登录页，应改用 `/web/#/portal/...`。

## 4. 推荐演示流程

### 4.1 首页

1. 指出页面顶部持续显示“DEMO 原型”；
2. 介绍“1+4+2+N”业务框架中的四类公共服务入口；
3. 展示统计数字均标注为演示数据；
4. 展开 AI 助手，说明回复为预置演示文本。

### 4.2 出口合规预检

1. 填写示例产品名称，选择产品类别和目标市场；
2. 仅选择标签图片、包装图片、产品规格说明或公开资料等低敏材料类型；
3. 确认不含企业核心数据并接受结果边界；
4. 提交后展示任务编号、风险条目、缺失材料、演示来源和下一步建议；
5. 强调结果来自固定 Demo 规则，不是法规结论。

### 4.3 场景与诊断

1. 展示通用办公、研发、制造、质量、营销出海和经营六类场景；
2. 完成五题轻量诊断；
3. 解释结果按“公共平台直接解决、轻量 POC、企业专项建设”三类分流；
4. 后端不可用时，诊断页会明确提示已降级为浏览器本地确定性规则。

## 5. 测试与构建

后端：

    cd backend
    .venv/bin/python -m pytest -q
    .venv/bin/python -m ruff check app/plugin/food_ai tests/plugin/food_ai app/api/v1/routers.py

前端：

    cd frontend/web
    npx --yes pnpm@9.15.3 test
    npx --yes pnpm@9.15.3 type-check
    npx --yes pnpm@9.15.3 build:dev

## 6. 数据与运行限制

- 预检任务使用进程内存仓库，后端重启后任务和结果会丢失；
- 多进程或多实例部署会形成互不共享的任务集合；
- 当前无数据库迁移、持久化、文件存储和任务队列；
- 当前无需流式输出；请求为短响应，前端只需展示提交中、成功和失败状态；
- 诊断页保留透明的本地降级用于演示连续性，预检页不伪造成功结果；
- 上生产前必须补充正式数据源授权、法规更新责任、隐私评估、安全评估和验收口径。

## 7. 简单服务器部署建议

Demo 服务器可采用同机部署：Nginx 提供前端静态文件，并将 `/api/v1/` 反向代理至单实例 Uvicorn。生产化前不应直接复用进程内任务仓库；建议改为 PostgreSQL 持久化，并按实际并发引入 Redis、任务队列和集中日志。

部署时至少做到：HTTPS、来源限制、请求体大小限制、服务端限流、访问日志脱敏、错误信息收敛、健康检查和最小权限运行。真实密钥管理要求见 [API_KEY_SECURITY.md](API_KEY_SECURITY.md)。

## 8. 常见问题

- 页面跳到登录页：检查 URL 是否为 `/web/#/portal/...`。
- 前端提交失败：确认 8001 端口后端仍在运行，并检查 `VITE_API_BASE_URL`。
- 诊断出现本地降级提示：后端请求失败；该提示是显式降级，不代表真实服务结果。
- 预检结果页刷新后提示找不到任务：后端进程可能已重启，重新提交一次即可。
