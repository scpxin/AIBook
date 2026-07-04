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

### Docker 部署规范
- Date: 2026-07-02
- Context: 用户要求将项目迁移到 Docker 环境，今后新项目都用 Docker 管理
- Category: 运维部署
- Instructions:
  - 所有项目使用 Docker Compose 管理
  - 项目存放路径：`/home/ubuntu/<项目名>-docker/`
  - 所有项目共用主机 port 80，通过不同 URL 路径区分（如 `/fanqie/`、`/other/`）
  - 数据持久化使用 Docker Volume
  - 容器设置 `restart: unless-stopped`

### Docker 镜像拉取
- Date: 2026-07-02
- Context: 服务器无法访问 Docker Hub，需要使用镜像加速
- Category: 环境配置
- Instructions:
  - 使用 DaoCloud 镜像：`docker.m.daocloud.io/library/<image>`
  - 拉取后 tag 为官方名称：`docker tag docker.m.daocloud.io/library/<image> <image>`
  - 已缓存镜像：`nginx:alpine`、`python:3.11-slim`

### 服务器环境
- Date: 2026-07-02
- Context: 腾讯云 VPS 部署环境
- Category: 运维部署
- Instructions:
  - 服务器 IP：`140.143.210.177`，用户名 `ubuntu`，系统 Ubuntu 22.0.4
  - Docker 已安装（v29.6.1），Docker Compose v5.2.0
  - 旧服务已停止：systemd `fanqie-content`、系统 Nginx（避免端口冲突）

### 文件部署路径（关键！）
- Date: 2026-07-02
- Context: Agent 修改了前端文件但没放到正确位置，导致页面不更新
- Category: 运维部署
- Instructions:
  - **前端文件**（index-v2.html、nginx.conf）**必须**复制到 `/home/ubuntu/fanqie-docker/`（Docker Compose bind mount 源目录）
  - **后端 Python 模块**通过 `scp` → `/tmp/novel_creator/` → `docker cp` → 容器
  - **server-v2.py** 同样通过 `docker cp` → 容器
  - **部署脚本**：`/workspace/deploy/sync.sh`（用法：`./sync.sh frontend|backend|server|all`）
  - **详细文档**：`/workspace/.monkeycode/docs/PROJECT_DEPLOY.md`
- 前端部署后执行 `docker compose restart web`
- 后端部署后执行 `docker compose restart backend`

### 前端开发常见 Bug 修复记录
- Date: 2026-07-04
- Context: 多次修复前端 bug，记录以避免重复犯错
- Category: 排错调试
- Instructions:
  - **Vue 模态框/弹出层必须放在 `<div id="app">` 内部**：放在外部 Vue 无法控制（v-if/@click 不生效），导致弹窗无法关闭
  - **所有 v-if/v-show/@click 元素必须在 #app 内**：Vue 只挂载 #app 内部元素
  - **模板变量显示原始 {{ }} = 元素在 #app 外**：当 {{ m.name }} 等变量未插值时，首先检查 div 平衡，很可能某个多余 </div> 把 #app 关闭了
  - **新增模态框后必须验证位置**：每次添加新的 v-if 模态框/弹出层后，必须用脚本验证该元素在 #app 关闭之前
  - **JS 语法检查**：修改后必须 `node --check` 验证，避免语法错误导致整个页面白屏
  - **body stream already read**：fetch 响应只能读一次，先 `r.text()` 再 `JSON.parse()`
  - **重复变量声明**：同一作用域内不能重复 `const`/`let` 声明同名变量
  - **nextTick 导入**：使用 `nextTick` 必须从 `vue` 导入
  - **Vue API 导入完整性检查**：每次新增 Vue 组合式 API 调用（如 `watch`）时，必须同步添加到顶部的 `const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue` 解构中。忘记导入会导致页面一闪而过（JS 运行时错误导致 Vue 挂载失败）
  - **"一闪而过"排查清单**：页面闪白/空白时，按顺序检查：① JS 语法（node --check）② Vue API 是否全部导入 ③ 模态框是否在 #app 内 ④ 模板中引用的变量/函数是否在 return 中暴露
  - **DIV 嵌套校验（关键！）**：修改 HTML 后必须用脚本验证 `<div>` 开闭标签平衡。多余 `</div>` 会导致 #app 提前关闭，后续所有模态框/按钮都在 #app 外面，Vue 不渲染它们。检查方法：遍历模板行跟踪深度，depth 不能为负，最终必须回零
  - **模态框显示原始 {{ }} 语法 = #app 提前关闭**：看到模板变量未插值时，首先检查 div 平衡，很可能某个多余 `</div>` 把 #app 关闭了
  - **FOUC 防护**：在 `#app` 元素上添加 `v-cloak` 属性，并在 CSS 中添加 `[v-cloak] { display: none !important; }`，防止 Vue 挂载前原始 HTML 闪烁
  - **watch 初始化触发**：Vue watch 在 setup 阶段会将初始值与 undefined 对比，可能误触发回调。使用 `setupDone` 标志位延迟启用 watch 逻辑
  - **ref/reactive 访问**：模板中自动解包，JS 中必须 `.value`
  - **API 路径前缀**：前端调用 `/api/xxx`，Nginx 代理 `/fanqie/api/` → 后端 `/api/`

### 后端开发常见 Bug 修复记录
- Date: 2026-07-03
- Context: 后端 Python 代码修复记录
- Category: 排错调试
- Instructions:
  - **format_prompt 安全化**：使用 SafeFormatter 子类，缺失 key 返回空字符串，永不 KeyError
  - **统一生成路径**：所有 AI 生成调用必须走 `format_prompt`，不能绕过
  - **SSE 流式响应**：流式端点必须设置 `text/event-stream` 响应头 + `Cache-Control: no-cache`
  - **流式超时**：AI 客户端流式超时必须 ≥600s，避免长文本生成中断
  - **项目存储目录**：`os.makedirs(PROJECTS_DIR, exist_ok=True)` 必须在启动时执行
  - **urllib.parse.quote**：URL 编码必须用 `urllib.parse.quote`，不是 `urllib.request.quote`
  - **路径遍历防护**：所有用户输入的 ID（project_id/book_id）必须用正则白名单校验
  - **SSRF 防护**：代理类端点必须限制允许域名白名单
  - **JSON 解析失败**：不能静默忽略，必须返回 400 错误
  - **重复 import**：模块顶部已导入的不要在函数内重复导入

### 参考项目管理
- Date: 2026-07-03
- Context: 用户要求建立参考项目追踪机制，记录借鉴内容在本项目的应用位置
- Category: 工作流协作
- Instructions:
  - 详细记录文档：`/workspace/.monkeycode/docs/REFERENCE_PROJECTS.md`
  - 每次用户分享参考项目时，必须记录：项目 URL、借鉴内容、在本项目的应用位置（文件路径+行号）
  - 记录格式：项目名称、项目简介、借鉴内容列表（含应用位置）、相关文件变更

### 全面代码审计（2026-07-03）
- Date: 2026-07-03
- Context: 对整个项目进行全面逻辑审查，修复 28 个前端问题 + 20 个后端问题 + 14 个 novel_creator 问题
- Category: 排错调试
- Instructions:
  - **前端关键修复**：模态框必须在 #app 内、自动保存需 watch 触发、storyContext 需持久化、hasStepContent(3) 不应要求 bookOverview
  - **后端关键修复**：搜索 API 路径遍历、SSRF 防护、count 参数上限、JSON 解析错误处理
  - **novel_creator 关键修复**：ai_client 提取公共方法、SSL 上下文统一、移除死代码和调试 print
  - **parseOutline 中文数字**：新增 cnNumToArabic 函数处理中文章节号

### 超时配置规范
- Date: 2026-07-03
- Context: 多次因超时导致生成失败
- Category: 环境配置
- Instructions:
  - Nginx `proxy_read_timeout`: 600s
  - AI 客户端 `timeout`: 600s
  - 前端 `API_TIMEOUT`: 600000ms
  - 三者必须同步调整，缺一不可

### GitHub 版本管理
- Date: 2026-07-04
- Context: 建立 GitHub 版本控制，方便回滚
- Category: 工作流协作
- Instructions:
  - 远程仓库：`https://github.com/scpxin/AIBook.git`
  - 每次提交后必须 `git push origin master` 推送到 GitHub
  - 提交前先验证 HTML 结构（html.parser 检查 div 标签配对）
  - 功能修改 → feat: / 修复 → fix: / 重构 → refactor:
  - 推送命令：`git push origin master`
  - 回滚时：`git log --oneline` 查找 commit hash → `git reset --hard <hash>` → `git push -f origin master`
  - **每次修改后必须同步更新 README.md**：包括功能列表、API接口、项目结构、版本历史等
  - README.md 与实际代码保持同步，不能过时
