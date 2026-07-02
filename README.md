# 番茄小说下载 + AI 创作平台

基于 Docker 部署的番茄小说下载与 AI 小说创作平台，集成 MuMuAINovel 核心 AI 创作能力。

## 功能概览

### 小说下载
- 搜索番茄小说（支持书名、作者、链接）
- 查看章节目录
- 下载整本小说到服务器（支持暂停/继续）
- 下载内容持久化存储

### AI 创作（集成 MuMuAINovel）
- **灵感生成**：AI 生成书名、简介、主题、类型选项
- **世界观构建**：自动生成时间背景、空间环境、世界规则
- **角色生成**：批量生成角色和组织（含性格、背景、关系）
- **大纲生成**：自动生成章节大纲
- **章节生成**：根据大纲逐章生成正文
- **风格分析**：分析任意文本的写作风格
- **风格仿写**：根据分析结果仿写新内容

## 在线访问

```
http://140.143.210.177/fanqie/
```

## 快速开始

### 前置要求

- Docker 29+
- Docker Compose v5+

### 启动服务

```bash
git clone https://github.com/scpxin/fanqie.git
cd fanqie/deploy
docker compose up -d --build
```

服务启动后访问 `http://<服务器IP>/fanqie/`

### 配置 AI 模型

1. 点击右上角设置图标
2. 添加大模型配置（支持所有 OpenAI 兼容 API）
3. 常用预设：
   - 智谱 GLM-4-Flash（免费）
   - DeepSeek V3
   - 通义千问 Turbo

## 项目结构

```
fanqie/
├── deploy/
│   ├── docker-compose.yml      # Docker Compose 配置
│   ├── Dockerfile              # 后端镜像构建
│   ├── nginx.conf              # Nginx 反向代理配置
│   ├── server-v2.py            # Python 后端服务
│   ├── index-v2.html           # 前端页面
│   ├── novel_creator/          # AI 小说创作模块
│   │   ├── __init__.py
│   │   ├── prompts.py          # AI prompt 模板
│   │   ├── ai_client.py        # OpenAI 兼容 API 客户端
│   │   └── generator.py        # 小说创作生成器
│   └── DOCKER.md               # Docker 操作文档
├── userscript/
│   └── fanqie.user.js          # 油猴脚本（独立使用）
└── docs/
    └── index.html              # GitHub Pages 演示页
```

## API 接口

### 小说下载

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/search` | GET | 搜索小说 |
| `/api/directory` | GET | 获取章节目录 |
| `/api/content` | GET | 获取章节内容 |
| `/api/resolve` | GET | 解析番茄小说链接 |
| `/api/download/start` | GET | 开始下载 |
| `/api/download/status` | GET | 查询下载进度 |
| `/api/download/pause` | GET | 暂停下载 |
| `/api/download/resume` | GET | 继续下载 |
| `/api/download/file` | GET | 下载文件（同时保存到服务器） |
| `/api/downloads/list` | GET | 获取已下载书籍列表 |
| `/api/downloads/content` | GET | 获取已下载书籍内容 |

### AI 创作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/novel/inspiration/title` | POST | 生成书名建议 |
| `/api/novel/inspiration/description` | POST | 生成简介选项 |
| `/api/novel/inspiration/theme` | POST | 生成主题选项 |
| `/api/novel/inspiration/genre` | POST | 生成类型标签 |
| `/api/novel/worldbuilding` | POST | 构建世界观 |
| `/api/novel/characters` | POST | 生成角色 |
| `/api/novel/outline` | POST | 生成大纲 |
| `/api/novel/chapter` | POST | 生成章节正文 |
| `/api/novel/analyze-style` | POST | 分析写作风格 |
| `/api/novel/analyze-chapter` | POST | 分析章节 |
| `/api/novel/generate-style` | POST | 风格仿写生成 |

### AI 通用

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ai/analyze` | POST | 风格分析（简化版） |
| `/api/ai/generate` | POST | 仿写生成（简化版） |

## Docker 部署

详见 [DOCKER.md](deploy/DOCKER.md)

### 常用命令

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f

# 重启
docker compose restart

# 停止
docker compose down

# 更新代码后重建
docker compose down && docker compose up -d --build
```

### 服务架构

```
用户 → Nginx (80) → Python Backend (8000)
                              ↓
                     Volume: fanqie-downloads
```

## 技术栈

- **后端**: Python 3.11 + http.server
- **前端**: 原生 HTML/JS（单文件应用）
- **AI 客户端**: OpenAI 兼容 API
- **部署**: Docker + Nginx
- **数据持久化**: Docker Volume

## 数据来源

- 搜索 API：番茄小说官方搜索接口
- 目录 API：番茄小说官方目录接口
- 内容 API：自建内容服务（仅限中国 IP 直连）

## 许可证

GPL-3.0
