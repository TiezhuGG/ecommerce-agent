# 电商导购 Agent

这是一个以教学驱动方式推进的电商导购 Agent 项目，目标是帮助你在真实编码过程中学习以下能力：

- Vue 3 前端界面与业务模块拆分
- FastAPI 后端接口设计
- 基于 LangGraph 的 Agent 工作流
- 电商导购、售前 FAQ、商品对比等真实业务场景建模

## 当前阶段

当前完成的是第一轮迭代的基础版本：

- 后端提供基础健康检查接口
- 前端已切换为中文界面
- 前端已接入 Tailwind CSS
- 首页已重构为响应式的电商导购 Agent 展示骨架
- 页面包含搜索区、智能导购区、商品列表区、对比区、FAQ 区
- 搜索、对比、FAQ 目前使用前端静态示例数据，用于先跑通页面和业务结构

## 项目结构

- `backend/`
  - FastAPI 服务
  - 当前提供 `/health` 健康检查接口
- `frontend/`
  - Vue 3 + Vite + Tailwind CSS 前端
  - 当前主要用于展示第一版页面骨架和交互结构
- `docs/`
  - 项目架构、业务设计、接口规划和迭代说明

## 当前页面包含什么

首页现在不是最终功能页，而是第一版业务壳子。它的作用是把后续要做的核心模块先搭出来：

- 搜索筛选区
  - 对应未来的结构化商品搜索
- 智能导购区
  - 对应未来的 LangGraph 推荐工作流入口
- 商品结果区
  - 对应未来的商品检索和推荐结果展示
- 对比分析区
  - 对应未来的商品对比接口
- FAQ 区
  - 对应未来的售前知识库问答

## 如何启动后端

```powershell
cd C:\Users\FFF\Desktop\ecommerce-agent\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

如果你习惯使用虚拟环境，也可以先创建并激活虚拟环境，再安装依赖。

## 如何启动前端

```powershell
cd C:\Users\FFF\Desktop\ecommerce-agent\frontend
npm install
npm run dev
```

前端默认访问后端地址：`http://127.0.0.1:8000`

## 下一步会做什么

接下来的迭代不会一次性把所有功能全做完，而是继续按小步推进：

1. 把静态商品数据迁移到后端接口
2. 增加真实的商品搜索接口
3. 接入 PostgreSQL 存储商品与 FAQ 数据
4. 接入 OpenAI SDK 做意图解析
5. 用 LangGraph 串起导购推荐工作流

## 架构文档

详细架构说明见：

- `docs/电商导购Agent-V1架构与迭代计划.md`
