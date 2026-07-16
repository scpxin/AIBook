# 用户指令记忆

本文件记录了用户的指令、偏好和教导，用于在未来的交互中提供参考。

## 格式

### 用户指令条目
用户指令条目应遵循以下格式：

[用户指令摘要]
- Date: [YYYY-MM-DD]
- Context: [提及的场景或时间]
- Instructions:
  - [用户教导或指示的内容，逐行描述]

### 项目知识条目
Agent 在任务执行过程中发现的条目应遵循以下格式：

[项目知识摘要]
- Date: [YYYY-MM-DD]
- Context: Agent 在执行 [具体任务描述] 时发现
- Category: [运维部署|构建方法|测试方法|排错调试|工作流协作|环境配置]
- Instructions:
  - [具体的知识点，逐行描述]

## 去重策略
- 添加新条目前，检查是否存在相似或相同的指令
- 若发现重复，跳过新条目或与已有条目合并
- 合并时，更新上下文或日期信息
- 这有助于避免冗余条目，保持记忆文件整洁

## 条目

### 服务器与Docker环境配置
- Date: 2026-07-09
- Context: 服务器环境配置汇总
- Category: 运维部署
- Instructions:
  - 服务器: 140.143.210.177, ubuntu用户, SSH: `sshpass -p '<SSH_PASSWORD>' ssh -o StrictHostKeyChecking=no ubuntu@140.143.210.177`
  - 部署方式: Docker容器（fanqie-v2-frontend:80, fanqie-v2-backend:8000）
  - 服务器路径: `/home/ubuntu/fanqie-v2/` (仓库直接部署)
  - 后端文件注入: `docker cp到容器 → docker restart → sleep 5`
  - 前端部署: `frontend/dist/` 由docker构建时生成
  - 数据目录: `/home/ubuntu/fanqie_data/` volume mount到 `/app/data/`
  - git: remote=`scpxin:<GITHUB_TOKEN>@github.com/scpxin/AIBook.git`, 默认分支=master
  - AI模型: LongCat-2.0, endpoint: `https://api.longcat.chat/openai//v1/chat/completions`
  - DB: SQLite, `/app/data/fanqie.db`

### LongCat-2.0模型使用要点
- Date: 2026-07-11
- Context: E2E测试发现LongCat-2.0对复杂prompt不稳定
- Category: 环境配置
- Instructions:
  - LongCat-2.0不适合长prompt(>100字符)+高max_tokens(>6000)的复杂JSON生成
  - prompt超过~120字符时API间歇性返回空choices,导致"AI返回空内容"错误
  - 解决方案: 简化prompt至100字符以内,max_tokens控制在3000-5000,加fallback模板
  - 修复文件: structure_service.py, design_service.py, execution_service.py, novel_creator/generator.py
  - generator.py智能重试: token_options=[base,3000,5000],空响应自动重试
  - validation.py改为宽松模式(不强制required_keys)

### LongCat API配置
- Date: 2026-07-11
- Context: 本地测试环境可用的LongCat API配置
- Category: 环境配置
- Instructions:
  - Endpoint: `https://api.longcat.chat/openai`
  - API Key: `<LONGCAT_API_KEY>`

### 代码修改流程规范
- Date: 2026-07-11
- Context: 用户要求规范开发流程
- Category: 工作流协作
- Instructions:
  - **所有代码修改必须推送 GitHub** (`https://github.com/scpxin/AIBook.git`, 分支 `master`)
  - **严禁删除或覆盖 GitHub 上的任何内容** (禁止 force push, 禁止删除分支/标签/文件)
  - 开发流程: 本地 `/workspace/deploy/` 编辑 → git commit → git push GitHub → 服务器 `git pull` 或 rsync 同步 → Docker cp + restart → 测试
  - 服务器路径: `/home/ubuntu/fanqie-v2/` (直接 git clone 的仓库)
  - 本地路径: `/workspace/deploy/` (backend_v2/app/, novel_creator/, frontend/)
  - 模型: `LongCat-2.0`
  - 启动方式: `cd /workspace/deploy/backend_v2 && PYTHONPATH=/workspace/deploy:$PYTHONPATH AI_ENDPOINT=https://api.longcat.chat/openai AI_API_KEY=<LONGCAT_API_KEY> AI_MODEL=LongCat-2.0 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`
  - 注意: proxy.monkeycode-ai.com的key在当前环境返回403,不可用

### V2流水线测试项目
- Date: 2026-07-11
- Context: E2E全流水线测试创建的项目
- Category: 运维部署
- Instructions:
  - 测试项目ID: `e2e-test-20260711`
  - 输入灵感: "反套路系统 系统批发 主角是系统 给不同世界的人批发系统 剧情搞笑"
  - 测试结果: 19/19模块全部通过,生成5章正文共16628字
  - 发现问题: M9卷纲接口代码Bug(已修复)、部分API字段名不匹配
  - 测试报告: `方案文档/E2E全流程测试报告_20260711.md`
  - 正文文件: `方案文档/E2E测试正文_反套路系统_20260711.md`

### 前后端开发常见Bug修复
- Date: 2026-07-05
- Context: 前后端代码修复经验汇总
- Category: 排错调试
- Instructions:
  - 前端: 模态框必须在#app内,Vue API需完整导入,JS语法node --check,DIV嵌套校验
  - 后端: format_prompt安全化,text/event-stream响应头,JSON解析错误返回400
  - 数据库: sqlite busy_timeout=30000ms
  - SSRF防护: 代理端点必须域名白名单
  - 路径遍历: 用户输入ID正则白名单校验

### 项目API与数据结构
- Date: 2026-07-11
- Context: v2 API数据格式要点
- Category: 排错调试
- Instructions:
  - 模块保存: `/api/v2/pipeline/{projectId}/data/{moduleName}` (POST)
  - 项目ID由前端generateId()生成(格式pj-xxx),无create端点
  - 世界观: save_world()期望{"origin":{...}}嵌套格式
  - 灵感API: 字段名user_input不是prompt
  - story/master schema中characters字段是List[Any](不能是List[str])

### 超时与性能配置
- Date: 2026-07-11
- Context: 超时配置规范
- Category: 环境配置
- Instructions:
  - Nginx proxy_read_timeout: 600s
  - AI客户端timeout: 600s (构造函数默认)
  - 前端API_TIMEOUT: 600000ms
  - generator.py中effective_timeout = max(90, max_tokens*20//1000)
  - uvicorn --workers 2

### 方案文档统一管理
- Date: 2026-07-11
- Context: 要求所有报告/方案/改进建议统一存放
- Category: 工作流协作
- Instructions:
  - 所有报告、方案、改进建议、测试报告等文档统一放在 `/workspace/方案文档/` 目录
  - 命名规则: `{方案名}_{日期}.md`,例如 `E2E测试报告_20260711.md`
  - 不再散落在 reports/、scripts/、.monkeycode/docs/ 等位置
  - 保留 .monkeycode/docs/ 中的 PROJECT.md、PROJECT_DEPLOY.md 等长期参考文档
  - 保留 .monkeycode/specs/ 中的技术方案设计文档
  - 临时性报告/测试结果/修复方案一律归入 方案文档/

### Git分支规范
- Date: 2026-07-11
- Context: 用户要求默认推送到master分支
- Category: 工作流协作
- Instructions:
  - 所有git推送默认推送到 `master` 分支,不使用 `main`
  - 服务器: `git branch -M main master` 确保分支名为master
  - GitHub仓库默认分支为master
  - **严禁使用 `git push --force`**,会覆盖远程历史导致数据丢失

### 参考项目与模板系统
- Date: 2026-07-09
- Context: 模板系统API
- Category: 运维部署
- Instructions:
  - 模板API: /api/v2/generation-templates/ (CRUD + match + apply)
  - 匹配分数: 同组+40,题材+25,世界类型+20,子类型+20,风格+15
  - 前端路由: /templates(模板库), /create-v2(集成弹窗)
  - 参考项目文档: /workspace/.monkeycode/docs/REFERENCE_PROJECTS.md
