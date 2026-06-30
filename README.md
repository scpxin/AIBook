# 番茄小说下载工具

两个番茄小说下载工具，均无需安装任何软件。

---

## 方式一：油猴脚本（推荐）

**文件**: `userscript/fanqie.user.js`

进入任意番茄小说章节页面自动获取完整内容，一键下载整本 TXT。

### 功能

- 打开章节页面自动显示完整内容
- 一键下载整本小说为 TXT 文件
- 下载过程支持暂停 / 继续
- 实时显示下载进度（章节数、速度、预计剩余时间）
- 右下角工具栏：获取全文、复制、下载整本

### 安装

1. 安装 [Tampermonkey](https://www.tampermonkey.net/) 浏览器扩展
2. 打开脚本安装链接：`https://raw.githubusercontent.com/scpxin/fanqie/master/userscript/fanqie.user.js`
3. 点击 Tampermonkey 弹出窗口中的「安装」
4. 访问任意番茄小说章节页面即可使用

---

## 方式二：网页下载器（无需安装任何扩展）

**文件**: `docs/index.html`

一个纯前端网页，打开即用。通过 CORS 代理访问 API，**无需后端服务器**，已部署到 GitHub Pages。

### 使用方法

直接打开：`https://scpxin.github.io/fanqie/`（需先在仓库设置中启用 Pages，见下方部署步骤）

在页面中：
- **按书名搜索**：输入书名搜索，选择搜索结果中的书籍
- **粘贴链接**：直接粘贴 `fanqienovel.com` 的章节或书籍链接，自动识别并定位
- **下载整本**：点击「下载整本 TXT」，等待完成后点击「保存 TXT 文件」

### 部署到 GitHub Pages

1. 打开仓库 Settings 页面：`https://github.com/scpxin/fanqie/settings/pages`
2. **Source** 选择 **Deploy from a branch**
3. **Branch** 选择 `master`，目录选择 `/docs`
4. 点击 **Save**
5. 约 1 分钟后访问 `https://scpxin.github.io/fanqie/`

### 原理

所有 API 请求通过 `https://corsproxy.io/` 代理转发，绕过浏览器跨域限制：

| API | 说明 |
|-----|------|
| 搜索 API | `novel.snssdk.com` / 搜索书名 |
| 目录 API | `fanqienovel.com/api/reader/directory/detail` / 获取章节目录 |
| 内容 API | `101.35.133.34:5000/api/content` / 获取完整文本 |

### 本地运行（备选）

如果 CORS 代理不可用，也可以用 Python 本地启动：

```bash
cd web-tool
python3 server.py
```

然后打开 `http://localhost:8000`

---

## 项目结构

```
fanqie/
├── README.md
├── userscript/
│   └── fanqie.user.js        # 油猴脚本
├── web-tool/
│   ├── server.py             # 本地 Python 后端（备选）
│   └── index.html            # 网页前端源文件
└── docs/
    └── index.html            # GitHub Pages 部署文件
```

---

## 技术说明

### API 来源

- **章节内容**: 自建 API `101.35.133.34:5000`（来自 [addallno/fqdt](https://github.com/addallno/fqdt) 项目）
- **章节目录**: 番茄小说官方 API
- **搜索**: 番茄小说官方搜索 API

### 章节链接解析流程

```
章节链接 /reader/{item_id}
    → 官方 API 获取 book_id
    → 官方目录 API 获取所有章节 ID 列表
    → 自建内容 API 逐章获取完整文本
```

---

## 注意事项

- 仅供学习交流使用
- 内容 API 服务器 `101.35.133.34` 为第三方维护，稳定性无法保证
- 下载全本需数分钟，取决于网络和章节数量
- CORS 代理 `corsproxy.io` 为公共服务，如不可用可改用油猴脚本或本地 Python 版本
