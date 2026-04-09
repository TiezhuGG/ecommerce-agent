# 电商导购 Agent

这是一个以“教学优先、逐轮迭代”为目标推进的电商导购 Agent 项目，目标是在真实编码过程中逐步掌握下面几类能力：

- Vue 3 + TailwindCSS 前端页面拆分与状态管理
- FastAPI 后端接口设计与服务分层
- 基于兼容 OpenAI 协议模型的 LLM 调用封装
- 基于 LangGraph 的单 Agent 编排
- 电商导购、知识库问答、商品对比这类真实业务工具的组合方式

## 当前阶段

当前代码已经完成到第九轮迭代，核心能力包括：

- `/products` 商品搜索工具
- `/faq/ask` 知识库问答 / RAG 第一版
- `/compare` 商品对比工具
- `/intent/parse` 意图解析工具
- `/agent/precheck` Agent 运行预检
- `/agent/chat` LangGraph 单 Agent 对话入口
- `/agent/runs` 最近持久化的 Agent 运行历史

后端已经补上了可替换的数据访问层骨架：

- 当前默认仍使用内存种子数据
- 已新增仓储层和 `DATABASE_URL` 配置入口
- 后续接 PostgreSQL 时，不需要再重拆业务服务层
- 当 `DATABASE_URL` 可用时，后端会自动初始化表并写入 seed 数据

前端当前已经升级成统一的 Agent 工作台，能直接展示：

- Agent 路由结果
- 最终回答
- 解析出的意图条件
- 工具调用轨迹
- 预检结果与风险提示
- 知识库引用片段与检索模式

## 项目结构

- `backend/`
  FastAPI 服务，包含商品、知识库问答、对比、意图解析和 Agent 编排能力
- `frontend/`
  Vue 3 + Vite + TailwindCSS 前端，负责展示商品搜索、FAQ/RAG、对比区和 Agent 工作台
- `docs/`
  每一轮迭代文档、架构说明和复盘记录

## 如何启动后端

```powershell
cd C:\Users\FFF\Desktop\ecommerce-agent
python -m pip install -r backend\requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

如果你使用虚拟环境，建议先激活虚拟环境，再执行 `python -m pip install ...`，不要直接依赖某个历史遗留的 `pip.exe` 启动器。

当前项目会尽量兼容 Python 3.14，但部分三方依赖在 3.14 下仍可能打印兼容性警告；如果你更希望环境更安静，Python 3.12 / 3.13 仍然是更稳的选择。

后端环境变量可参考：

- `backend/.env.example`

其中：

- `DATABASE_URL` 目前作为后续数据库接入预留配置
- 当前未配置时，后端会自动回退到仓库内置的 seed 数据
- 当前已内置 SQLAlchemy + PostgreSQL 驱动接入代码，但是否真正切到数据库，以 `health` / `agent/precheck` 返回的 `data_backend` 为准
- `agent/precheck` 返回的 `agent_log_backend` 可用于确认 Agent 运行日志是否已启用数据库持久化
- 当数据库日志持久化启用后，可通过 `/agent/runs` 查看最近的 Agent 运行摘要

## 如何启动前端

```powershell
cd C:\Users\FFF\Desktop\ecommerce-agent\frontend
npm install
copy .env.example .env
npm run dev
```

前端默认访问后端地址：`http://127.0.0.1:8000`

如需改成其他后端地址，可修改：

- `frontend/.env`
- `VITE_API_BASE_URL`

## 建议的学习顺序

1. 先看 `backend/app/catalog`、`backend/app/faq`、`backend/app/compare`
   先理解什么叫“可复用业务工具”
2. 再看 `backend/app/intent`
   理解 LLM 和本地规则如何一起把自然语言整理成结构化搜索条件
3. 最后看 `backend/app/agent`
   理解 LangGraph 是如何把路由、工具调用和最终回答串起来的
4. 对照 `frontend/src/App.vue` 和 `frontend/src/components/AgentPromptPanel.vue`
   理解前端如何把 Agent 运行过程可视化

## 文档入口

- `docs/电商导购Agent-V1架构与迭代计划.md`
- `docs/迭代-08-LangGraph单Agent编排与预检.md`
- `docs/迭代-09-知识库RAG第一版.md`
