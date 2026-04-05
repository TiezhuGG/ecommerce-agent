# 电商导购 Agent

这是一个以“教学优先、逐轮迭代”为目标推进的电商导购 Agent 项目，目标是让你在真实编码过程中逐步掌握下面几类能力：

- Vue 3 + TailwindCSS 前端页面拆分与状态管理
- FastAPI 后端接口设计与服务分层
- 基于兼容 OpenAI 协议模型的 LLM 调用封装
- 基于 LangGraph 的单 Agent 编排
- 电商导购、FAQ、商品对比这类真实业务工具的组合方式

## 当前阶段

当前已经完成到第八轮迭代，核心能力包括：

- `/products` 商品搜索工具
- `/faq/ask` 售前 FAQ 工具
- `/compare` 商品对比工具
- `/intent/parse` 意图解析工具
- `/agent/precheck` Agent 运行预检
- `/agent/chat` LangGraph 单 Agent 对话入口

前端当前已经升级成统一的 Agent 工作台，能直接展示：

- Agent 路由结果
- 最终回答
- 解析出的意图条件
- 工具调用轨迹
- 预检结果与风险提示

## 项目结构

- `backend/`
  FastAPI 服务，包含商品、FAQ、对比、意图解析和 Agent 编排能力
- `frontend/`
  Vue 3 + Vite + TailwindCSS 前端，负责展示商品搜索、FAQ、对比区和 Agent 工作台
- `docs/`
  每一轮迭代文档、架构说明和复盘记录

## 如何启动后端

```powershell
cd C:\Users\FFF\Desktop\ecommerce-agent\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

如果你使用虚拟环境，请先激活已有的 `.venv`，不要重复创建多个环境，避免依赖混乱。

建议优先使用 Python 3.12 或 3.13。
当前如果使用 Python 3.14，LangGraph 相关依赖虽然可以安装，但会打印兼容性警告。

## 如何启动前端

```powershell
cd C:\Users\FFF\Desktop\ecommerce-agent\frontend
npm install
npm run dev
```

前端默认访问后端地址：`http://127.0.0.1:8000`

## 建议的学习顺序

1. 先看 `backend/app/catalog`、`backend/app/faq`、`backend/app/compare`
   先理解什么叫“可复用业务工具”
2. 再看 `backend/app/intent`
   理解 LLM 在系统里如何只负责“理解需求”，而不是直接编造商品结果
3. 最后看 `backend/app/agent`
   理解 LangGraph 是如何把路由、工具调用和最终回答串起来的
4. 对照 `frontend/src/App.vue` 和 `frontend/src/components/AgentPromptPanel.vue`
   理解前端如何把 Agent 运行过程可视化

## 文档入口

- `docs/电商导购Agent-V1架构与迭代计划.md`
- `docs/迭代-08-LangGraph单Agent编排与预检.md`
