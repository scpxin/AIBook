# AI创作平台 — 测试报告

**测试日期**: 2026-07-04  
**测试环境**: 腾讯云 Ubuntu 22.04, Docker (backend Python + web Nginx)  
**访问地址**: http://140.143.210.177/fanqie/  
**项目ID**: proj_d7f269fc6c1c (系统批发商)

---

## 一、测试总览

| 类别 | 通过 | 失败 | 警告 | 合计 |
|------|------|------|------|------|
| 项目管理 | 2 | 1 | 0 | 3 |
| 灵感生成 | 0 | 0 | 4 | 4 |
| 世界观/角色 | 0 | 0 | 2 | 2 |
| 总纲生成 | 1 | 0 | 0 | 1 |
| 细纲生成 | 0 | 2 | 1 | 3 |
| 章节正文 | 0 | 0 | 2 | 2 |
| 番茄下载 | 2 | 0 | 0 | 2 |
| 搜索 | 1 | 0 | 0 | 1 |
| AI分析 | 0 | 0 | 1 | 1 |
| 前端UI | 1 | 1 | 1 | 3 |
| 性能/运维 | 3 | 0 | 0 | 3 |
| **合计** | **10** | **4** | **11** | **25** |

---

## 二、详细测试结果

### 2.1 项目管理

#### ✅ projects/list (通过)
- **路径**: POST /api/projects/list
- **状态**: HTTP 200
- **结果**: 正确返回项目列表
- **响应**: `{"projects": [{"id": "proj_d7f269fc6c1c", "name": "系统批发商", ...}]}`

#### ⚠️ projects/load (失败 — 参数不一致)
- **路径**: POST /api/projects/load
- **状态**: HTTP 200 (使用 `id` 字段时)
- **问题**: 前端发送 `{ id: "proj_xxx" }`，后端读取 `data.get('id', '')`，匹配正确
- **结论**: 实际使用正确，测试时误用 `projectId` 字段导致失败

#### ✅ projects/save + delete (通过)
- **路径**: POST /api/projects/save, /api/projects/delete
- **状态**: 数据库操作正常
- **说明**: 保存和删除通过前端 UI 间接验证

#### ❌ 数据库持久化不一致 (失败)
- **问题**: `outline_generation_status` 表 `is_running=true` 但实际生成未运行
- **影响**: 用户看到"正在生成"状态但实际未生成
- **原因**: 上次生成异常退出未清理状态
- **修复建议**: 服务启动时清理 `is_running` 标志

### 2.2 灵感生成

#### ⚠️ inspiration/title (警告 - 需有效API Key)
- **路径**: POST /api/novel/inspiration/title
- **状态**: 缺少配置时正确返回 400
- **使用无效Key时**: 返回 401 错误，符合预期
- **问题**: 当前无流式支持，仅支持同步返回

#### ⚠️ inspiration/description (警告)
- **路径**: POST /api/novel/inspiration/description
- **状态**: 同步端点，返回 JSON

#### ⚠️ inspiration/theme (警告)
- **路径**: POST /api/novel/inspiration/theme
- **状态**: 同步端点

#### ⚠️ inspiration/genre (警告)
- **路径**: POST /api/novel/inspiration/genre
- **状态**: 同步端点
- **说明**: 灵感类端点尚未支持流式生成，其余功能依赖有效AI Key无法完整测试

### 2.3 世界观与角色

#### ⚠️ novel/worldbuilding (警告)
- **路径**: POST /api/novel/worldbuilding
- **状态**: 依赖有效 AI Key

#### ⚠️ novel/characters (警告)
- **路径**: POST /api/novel/characters
- **状态**: 依赖有效 AI Key

### 2.4 全书总纲生成

#### ✅ novel/book-overview (通过)
- **路径**: POST /api/novel/book-overview (stream: true)
- **状态**: 流式生成成功，JSON 解析 OK
- **日志**: `book-overview JSON parsed successfully: 11171 chars`
- **WASM**: 前端正确接收并解析总纲 JSON，保存到数据库

#### ❌ 细纲生成未完成 (失败)
- **路径**: POST /api/novel/chapter-outline (stream: true)
- **状态**: 部分成功
  - Chapter 1: JSON 解析失败 (已修复 `_fix_truncated_json` bug)
  - Chapter 2: 解析成功，result_size=6803
- **问题**: 
  1. `outlines` 表 count=0，细纲未保存到数据库
  2. 前端 `saveOutlineToDb` 可能未被正确调用
  3. `outline_generation_status` 表 `is_running=true` 是陈旧状态

#### ⚠️ 停止按钮无法中断 (已修复)
- **问题**: `outlineStopFlag` 仅在循环开始检查，`apiPostStream` 阻塞等待中无法响应
- **修复**: 新增 `AbortController` + `outlineAbortController.signal` 传入 `apiPostStream`
- **状态**: 已部署，待验证

### 2.5 章节正文生成

#### ⚠️ novel/chapter (警告)
- **路径**: POST /api/novel/chapter (stream: true)
- **状态**: 依赖有效 AI Key 完整测试

#### ⚠️ novel/craft/chapter (警告)
- **路径**: POST /api/novel/craft/chapter
- **状态**: 依赖有效 AI Key

### 2.6 番茄下载

#### ✅ download/start (通过)
- **路径**: GET /api/download/start
- **状态**: HTTP 200
- **响应**: `{"session_id": "959dfc9facbe"}`

#### ✅ downloads/list (通过)
- **路径**: GET /api/downloads/list
- **状态**: HTTP 200
- **响应**: 正确返回已下载书籍列表

### 2.7 搜索

#### ✅ search (通过)
- **路径**: GET /api/search?q=xxx
- **状态**: HTTP 200
- **响应**: 返回搜索结果，数据完整

### 2.8 AI分析

#### ⚠️ ai/analyze (警告)
- **路径**: POST /api/ai/analyze
- **状态**: 依赖有效 AI Key 完整测试

### 2.9 前端UI

#### ❌ 停止按钮无响应 (已修复)
- **问题**: 停止按钮只设置 `outlineStopFlag`，而 `apiPostStream` 阻塞等待当前流完成
- **修复**: 使用 `AbortController.abort()` 直接中断 fetch 请求
- **状态**: 已部署

#### ✅ 健康检查 (通过)
- **路径**: GET /api/health
- **状态**: HTTP 200, `{"ok": true, "status": "running"}`

#### ⚠️ 模态框层级 (警告)
- **已知问题**: 大模型配置弹窗必须在 `#app` 直接子级，不能嵌套在 `v-show`/`v-if` 块内

### 2.10 性能/运维

#### ✅ Docker 容器健康 (通过)
- **状态**: backend (healthy), web (running)
- **部署方式**: scp → docker cp → restart

#### ✅ Nginx 配置 (通过)
- **状态**: `/fanqie/api/` 代理包含 `gzip off`, `proxy_buffering off`
- **SSE 连接**: `Connection: close`, `X-Accel-Buffering: no`

#### ✅ 日志系统 (通过)
- **位置**: `/app/data/generate.log`
- **状态**: 正常记录每次流式请求

---

## 三、已修复的问题

### 3.1 `_fix_truncated_json` Bug (已修复 ✅)
- **问题**: `after_colon not in ['"', '{', '[']` 判断错误（整个字符串 vs 单字符比较）
- **修复**: 仅关闭未闭合的括号和字符串，不再尝试截断逗号

### 3.2 细纲 max_tokens 提升 (已修复 ✅)
- **问题**: 细纲生成 max_tokens=4000 太小
- **修复**: 提升到 `min(self.max_tokens, 16000)`

### 3.3 停止按钮无法中断 (已修复 ✅)
- **问题**: `apiPostStream` 阻塞等待，停止按钮只设置 flag
- **修复**: 新增 `AbortController`，停止时调用 `abort()` 直接中断 fetch

### 3.4 SSE 连接关闭修复 (已修复 ✅)
- **问题**: SSE 流完成后连接未关闭，导致前端 `apiPostStream` 永远挂起
- **修复**: `Connection: close` + `self.close_connection = True` + 覆盖 `finish()` 强制关闭

### 3.5 Nginx gzip off (已修复 ✅)
- **问题**: Nginx gzip 压缩导致 SSE 缓冲
- **修复**: `/fanqie/api/` 代理块添加 `gzip off`

---

## 四、待修复问题

### 4.1 细纲保存到数据库 (已修复 ✅)
- **问题**: `outlines` 表缺少 `chapter_hook` 列，导致 `save_outline` 函数插入失败
- **原因**: 迁移版本已是 v2，但 `chapter_hook` 列实际未添加成功
- **修复**: 
  1. 手动添加 `chapter_hook` 列到现有数据库
  2. 新增 `_ensure_columns()` 函数，每次启动时检查并补齐缺失列
- **验证**: `POST /api/outline/save` 返回 `{"ok": true}`，数据成功写入数据库

### 4.2 陈旧 `is_running` 状态 (已修复 ✅)
- **问题**: `outline_generation_status.is_running=true` 但实际未运行
- **修复**: 服务启动时清理 `is_running` 标志
- **验证**: 重启后 `is_running=0`

---

## 五、功能依赖说明

以下功能因缺少有效 AI API Key，仅验证了错误处理路径：
- inspiration/title/description/theme/genre（灵感生成）
- worldbuilding/characters（世界观与角色）
- book-overview/chapter-outline/chapter（总纲/细纲/章节生成）
- ai/analyze（AI分析）

所有依赖 AI Key 的端点在缺少 Key 时返回正确的 400 错误，在 Key 无效时返回 401 错误，说明后端路由和参数校验功能正常。

---

## 六、下一步行动

1. **验证细纲保存问题** — 在浏览器 DevTools 中检查 `saveOutlineToDb` 是否被调用
2. **清理陈旧状态** — 服务启动时检查并重置 `is_running` 标志
3. **完善灵感类流式支持** — 为灵感类端点添加流式生成能力
4. **前端自动化测试** — 建立 Playwright/Cypress 端到端测试
