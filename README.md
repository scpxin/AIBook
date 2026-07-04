# AI创作平台

基于 Docker 前后端分离架构的小说下载与 AI 小说创作平台，支持风格分析驱动的全流程创作。

## 架构

```
┌─────────────────────────────────────────────────────┐
│ Docker Compose                                       │
│  ┌──────────────────┐     ┌──────────────────────┐  │
│  │ frontend (Nginx) │────▶│ backend (FastAPI)    │  │
│  │ Vue 3 + Vite     │     │ Python 3.11          │  │
│  │ Port 80          │     │ Port 8000            │  │
│  └──────────────────┘     └──────────────────────┘  │
│         │                          │                │
│         ▼                          ▼                │
│  /fanqie/api/* proxy          SQLite + WAL          │
└─────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router |
| 后端 | Python 3.11 + FastAPI + Uvicorn + Pydantic |
| 数据库 | SQLite + WAL 模式 |
| 部署 | Docker Compose (frontend Nginx + backend Python) |

## 在线访问

```
http://140.143.210.177/fanqie/
```

## 快速开始

```bash
git clone https://github.com/scpxin/AIBook.git
cd AIBook/deploy
docker compose up -d
```

访问 `http://<服务器IP>/fanqie/`

## 项目结构

```
AIBook/
├── deploy/
│   ├── docker-compose.yml          # Docker Compose 编排
│   ├── backend_v2/                 # FastAPI 后端
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py             # FastAPI 入口
│   │       ├── config.py           # 环境变量配置
│   │       ├── database.py         # 数据库初始化
│   │       ├── models/
│   │       │   └── schemas.py      # Pydantic 请求/响应模型
│   │       ├── api/                # API 路由模块（8个文件）
│   │       └── services/           # 业务逻辑服务
│   ├── frontend/                   # Vue 3 前端工程
│   │   ├── Dockerfile              # 多阶段构建(Vite + Nginx)
│   │   ├── nginx.conf              # SPA 路由 + API 代理
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.ts             # 应用入口
│   │       ├── App.vue             # 根组件 + 全局样式
│   │       ├── router/             # Vue Router
│   │       ├── stores/             # Pinia 状态管理
│   │       ├── api/                # API 客户端封装
│   │       ├── components/         # 通用组件
│   │       └── views/              # 页面组件
│   ├── novel_creator/              # AI 小说创作核心模块
│   │   ├── database.py             # SQLite + schema 迁移
│   │   ├── generator.py            # NovelGenerator 生成器
│   │   ├── prompts.py              # Novel 流程 prompt
│   │   ├── craft_prompts.py        # 网文技法 prompt
│   │   └── ai_client.py            # OpenAI 兼容客户端
│   └── legacy/                     # 旧版归档（参考用）
│       ├── server-v2.py            # 旧版后端
│       ├── index-v2.html           # 旧版前端
│       └── docker-compose.yml      # 旧版编排
├── README.md
└── .gitignore
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 8000 | 后端 HTTP 端口 |
| DB_PATH | /app/data/fanqie.db | 数据库路径 |
| AI_TIMEOUT | 600 | AI 调用超时（秒） |
| SESSION_TTL | 86400 | 下载 session 过期时间 |

## 开发指南

### 前端

```bash
cd deploy/frontend
npm install
npm run dev    # 开发模式，热更新
npm run build  # 生产构建
```

### 后端

```bash
cd deploy/backend_v2
pip install -r requirements.txt
uvicorn app.main:app --reload
# API 文档: http://localhost:8000/docs
```

## 许可证

GPL-3.0
